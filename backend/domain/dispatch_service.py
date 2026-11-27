from datetime import datetime, timezone

from sqlalchemy import select, text

from core.records import get, need, scan, update
from domain.dispatch_model import dispatch_orders
from domain.learning import PRIORITY, classify
from domain.matches_model import matches
from domain.plies_model import plies

# 复盘只有三张桌。
TABLES = 3
ACTIVE = ('queued', 'claimed')
# 固定顾问锁键，令派单、换单、领单、报数、封账在库内串行，避免跨行竞态。
BOARD_LOCK = 1145523792


def _now():
    return datetime.now(timezone.utc)


def _lock(conn):
    if conn.dialect.name == 'postgresql':
        conn.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': BOARD_LOCK})


def _active(conn):
    return [order for order in scan(conn, dispatch_orders) if order['status'] in ACTIVE]


def _dispatchable(ply, game):
    return game is not None and game['open'] and not ply['witness'] and not ply['adjudicated']


def _one_per_game(conn, exclude_plies, exclude_games):
    """按模型「核对提子」分数从高到低排出候选，每局只取最高分的一个。"""
    games = {row['code']: row for row in scan(conn, matches)}
    pool = [ply for ply in scan(conn, plies)
            if ply['code'] not in exclude_plies and ply['game'] not in exclude_games
            and _dispatchable(ply, games.get(ply['game']))]
    if not pool:
        return []
    scored = classify(pool)
    hits = [(ply, score['score']) for ply, score in zip(pool, scored) if score['label'] == PRIORITY]
    hits.sort(key=lambda pair: (-pair[1], pair[0]['code']))
    chosen, seen = [], set()
    for ply, score in hits:
        if ply['game'] in seen:
            continue
        seen.add(ply['game'])
        chosen.append((ply, score))
    return chosen


def _place(conn, ply, score, table_no, bumped_from=None):
    values = dict(ply=ply['code'], game=ply['game'], score=score, table_no=table_no,
                  status='queued', claimed_by=None, actual=None, bumped_from=bumped_from,
                  created_at=_now(), claimed_at=None, closed_at=None)
    present = conn.execute(select(dispatch_orders.c.code)
                           .where(dispatch_orders.c.code == ply['code'])).first()
    if present is None:
        conn.execute(dispatch_orders.insert().values(code=ply['code'], **values))
    else:
        conn.execute(dispatch_orders.update()
                     .where(dispatch_orders.c.code == ply['code']).values(**values))
    return get(conn, dispatch_orders, ply['code'])


def _retire(conn, order, **extra):
    return update(conn, dispatch_orders, order['code'], status='withdrawn', closed_at=_now(), **extra)


def board(conn):
    orders = scan(conn, dispatch_orders)
    active = sorted((o for o in orders if o['status'] in ACTIVE),
                    key=lambda o: (o['table_no'] or 99, -o['score'], o['code']))
    closed = sorted((o for o in orders if o['status'] not in ACTIVE),
                    key=lambda o: (o['closed_at'] or datetime.min.replace(tzinfo=timezone.utc), o['code']),
                    reverse=True)
    occupied = {o['table_no'] for o in active}
    return {'tables': TABLES, 'free': len([t for t in range(1, TABLES + 1) if t not in occupied]),
            'orders': active + closed}


def plan(conn):
    """排单：撤下不再合规的单，再用「核对提子」高分补齐空桌。可重复执行，用于中断后恢复。"""
    _lock(conn)
    games = {row['code']: row for row in scan(conn, matches)}
    plies_by_code = {row['code']: row for row in scan(conn, plies)}
    survivors = []
    for order in _active(conn):
        ply = plies_by_code.get(order['ply'])
        if ply is None or not _dispatchable(ply, games.get(order['game'])):
            _retire(conn, order)                      # 已重放/已封账：腾桌，不再派
        else:
            survivors.append(order)
    free_tables = [t for t in range(1, TABLES + 1) if t not in {o['table_no'] for o in survivors}]
    if free_tables:
        candidates = _one_per_game(conn, {o['ply'] for o in survivors}, {o['game'] for o in survivors})
        for (ply, score), table_no in zip(candidates, free_tables):
            _place(conn, ply, score, table_no)
    return board(conn)


def claim(conn, user, data):
    """领单。与换单同时提交时，先落库者生效：先领到按原单做。"""
    _lock(conn)
    order = get(conn, dispatch_orders, data.code, lock=True)
    need(order['status'] == 'queued', '该单已被领走或已结束，请刷新后重新领单')
    return {'status': 'claimed',
            'order': update(conn, dispatch_orders, data.code, status='claimed',
                            claimed_by=user['sub'], claimed_at=_now())}


def swap(conn, user, data):
    """换单：用更高分手次顶掉还没领的单。已领的单不可顶。"""
    _lock(conn)
    order = get(conn, dispatch_orders, data.code, lock=True)
    need(order['status'] == 'queued', '该单已领走或已结束：已领到即按原单做，不可换单')
    need(data.ply != order['ply'], '换单手次与原单相同')
    ply = get(conn, plies, data.ply, lock=True)
    game = get(conn, matches, ply['game'])
    need(_dispatchable(ply, game), '该手次已重放或已封账，不再派单')
    others = [o for o in _active(conn) if o['code'] != order['code']]
    need(ply['game'] not in {o['game'] for o in others}, '该局已占一桌，不能同时占两桌')
    score = classify([ply])[0]
    need(score['label'] == PRIORITY, '仅对模型判为「核对提子」的手次派单')
    need(score['score'] > order['score'], '仅更高分的手次可以顶掉未领的单')
    table_no = order['table_no']
    _retire(conn, order)
    placed = _place(conn, ply, score['score'], table_no, bumped_from=order['code'])
    return {'status': 'swapped', 'order': placed, 'withdrawn': order['code']}


def report(conn, user, data):
    """领单人报完实盘提子数，才腾桌；同时把重放数写回手次。"""
    _lock(conn)
    order = get(conn, dispatch_orders, data.code, lock=True)
    need(order['status'] == 'claimed', '请先领单再报实盘提子数')
    need(order['claimed_by'] == user['sub'], '该单由他人领走，须由领单人报数')
    need(0 <= data.actual <= 50, '重放数量越界')
    ply = get(conn, plies, order['ply'], lock=True)
    need(get(conn, matches, ply['game'])['open'] and not ply['adjudicated'],
         '无法修改已勘误或冻结的手次')
    update(conn, plies, ply['code'], replayed=data.actual, witness=True)
    done = update(conn, dispatch_orders, data.code, status='done', actual=data.actual, closed_at=_now())
    return {'status': 'done', 'order': done}


def release_for_seal(conn, game):
    """封账前：已领未报数的单拦住封账；其余未领的单一律撤回。"""
    _lock(conn)
    orders = [order for order in _active(conn) if order['game'] == game]
    need(not any(order['status'] == 'claimed' for order in orders),
         '已领单尚未报实盘提子数，暂不能封账')
    for order in orders:
        _retire(conn, order)
