from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer, String, Table

from core.db import metadata


# 复盘只有三张桌。queued 与 claimed 视为占桌，done（已报实盘提子数）与 withdrawn（顶单/撤回）腾桌。
# 两个部分唯一索引在数据库层兜底：一桌最多一张在用派单、一局最多占一桌。
dispatch_orders = Table('dispatch_orders', metadata,
    Column('code', String(64), primary_key=True),
    Column('ply', String(160), ForeignKey('plies.code'), nullable=False),
    Column('game', String(160), ForeignKey('matches.code'), nullable=False),
    Column('score', Float, nullable=False),
    Column('table_no', Integer, nullable=True),
    Column('status', String(16), nullable=False),
    Column('claimed_by', String(160), nullable=True),
    Column('actual', Integer, nullable=True),
    Column('bumped_from', String(64), nullable=True),
    Column('created_at', DateTime, nullable=False),
    Column('claimed_at', DateTime, nullable=True),
    Column('closed_at', DateTime, nullable=True),
    CheckConstraint("status in ('queued', 'claimed', 'done', 'withdrawn')"),
    CheckConstraint('table_no is null or table_no between 1 and 3'),
    CheckConstraint('actual is null or actual between 0 and 50'),
    CheckConstraint("status in ('done', 'withdrawn') or table_no is not null"),
)

Index('uq_dispatch_active_table', dispatch_orders.c.table_no, unique=True,
      postgresql_where=dispatch_orders.c.status.in_(('queued', 'claimed')),
      sqlite_where=dispatch_orders.c.status.in_(('queued', 'claimed')))
Index('uq_dispatch_active_game', dispatch_orders.c.game, unique=True,
      postgresql_where=dispatch_orders.c.status.in_(('queued', 'claimed')),
      sqlite_where=dispatch_orders.c.status.in_(('queued', 'claimed')))
