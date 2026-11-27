from core.records import get, need, scan, update
from domain import dispatch_service
from domain.matches_model import matches
from domain.plies_model import plies


def review_window(conn, user, data):
    get(conn,matches,data.game,lock=True)
    outstanding=[r for r in scan(conn,plies) if r['game']==data.game and r['capture_claim']!=r['replayed'] and
                 not r['adjudicated']]
    need(data.open or not outstanding,'尚有提子疑点待勘误')
    if not data.open:
        dispatch_service.release_for_seal(conn, data.game)
    return update(conn,matches,data.game,open=data.open)
