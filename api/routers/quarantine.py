from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user
from api.schemas.quarantine import QuarantineEntry, QuarantineListResponse
from api.services import quarantine_service

router = APIRouter(prefix="/api/v1/quarantine", tags=["quarantine"])


@router.get("", response_model=QuarantineListResponse)
async def get_quarantine_list(_user: dict = Depends(get_current_user)) -> QuarantineListResponse:
    try:
        return quarantine_service.list_quarantine()
    except quarantine_service.QuarantineUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Le contenu de la quarantaine n'a pas pu être chargé pour le moment.",
        )


@router.get("/{item_id}", response_model=QuarantineEntry)
async def get_quarantine_item(item_id: str, _user: dict = Depends(get_current_user)) -> QuarantineEntry:
    entry = quarantine_service.get_details(item_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Élément de quarantaine introuvable.")
    return entry
