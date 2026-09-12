from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_current_user
from api.schemas.history import HistoryResponse
from api.services import history_service

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
async def get_history(
    search: Optional[str] = Query(default=None),
    verdict: Optional[str] = Query(default=None),
    family: Optional[str] = Query(default=None, alias="type"),
    limit: Optional[int] = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _user: dict = Depends(get_current_user),
) -> HistoryResponse:
    try:
        return history_service.fetch_history(
            search=search, verdict=verdict, family=family, limit=limit, offset=offset)
    except history_service.HistoryUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="L'historique n'a pas pu être chargé pour le moment.",
        )
