from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from api.schemas.protection import (
    ProtectionEventsResponse, ProtectionStartRequest, ProtectionStatus,
)
from api.services import protection_service

router = APIRouter(prefix="/api/v1/protection", tags=["protection"])


@router.get("/status", response_model=ProtectionStatus)
async def get_status(_user: dict = Depends(get_current_user)) -> ProtectionStatus:
    return protection_service.get_status()


@router.get("/events", response_model=ProtectionEventsResponse)
async def get_events(_user: dict = Depends(get_current_user)) -> ProtectionEventsResponse:
    return ProtectionEventsResponse(events=protection_service.get_events())


@router.post("/start", response_model=ProtectionStatus)
async def start_protection(
    payload: ProtectionStartRequest = ProtectionStartRequest(),
    _user: dict = Depends(get_current_user),
) -> ProtectionStatus:
    """Reutilise watcher.Protection.demarrer() tel quel -- aucune nouvelle
    politique de surveillance, une seule instance par processus API
    (cahier des charges §29)."""
    return protection_service.start(payload.auto_quarantine)


@router.post("/stop", response_model=ProtectionStatus)
async def stop_protection(_user: dict = Depends(get_current_user)) -> ProtectionStatus:
    return protection_service.stop()
