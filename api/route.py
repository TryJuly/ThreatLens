from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import IPvAnyAddress

from api import repository

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/events")
def events(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    src_ip: IPvAnyAddress | None = None,
    sensor: str | None = None,
    event: str | None = None,
):
    return repository.list_events(
        request.app.state.conn,
        limit,
        offset,
        src_ip=str(src_ip) if src_ip else None,
        sensor=sensor,
        event=event,
    )


@router.get("/ips/{ip}")
def ip_info(ip: IPvAnyAddress, request: Request):
    info = repository.get_ip_info(request.app.state.conn, str(ip))
    if info is None:
        raise HTTPException(status_code=404, detail="IP inconnue")
    return info


@router.get("/stats")
def stats(request: Request):
    return repository.get_stats(request.app.state.conn)
