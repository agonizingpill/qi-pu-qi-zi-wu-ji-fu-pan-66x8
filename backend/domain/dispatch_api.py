from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from domain import dispatch_service as service
from domain.dispatch_schemas import ClaimOrder, ReportCaptures, SwapOrder

router = APIRouter()


@router.get('/dispatch_orders')
def list_dispatch_orders(user=Depends(actor)):
    with transaction() as conn:
        return service.board(conn)


@router.post('/dispatch_orders/plan')
def plan_dispatch(user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.plan(conn)
        record(conn, user, 'dispatch.plan')
        return output


@router.post('/dispatch_orders/claim')
def claim_order(data: ClaimOrder, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.claim(conn, user, data)
        record(conn, user, 'dispatch.claim')
        return output


@router.post('/dispatch_orders/swap')
def swap_order(data: SwapOrder, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.swap(conn, user, data)
        record(conn, user, 'dispatch.swap')
        return output


@router.post('/dispatch_orders/report')
def report_captures(data: ReportCaptures, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.report(conn, user, data)
        record(conn, user, 'dispatch.report')
        return output
