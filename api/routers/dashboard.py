from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user
from api.schemas.dashboard import DashboardResponse
from api.services import dashboard_service, history_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(_user: dict = Depends(get_current_user)) -> DashboardResponse:
    try:
        return dashboard_service.get_dashboard()
    except history_service.HistoryUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Les métriques n'ont pas pu être calculées pour le moment.",
        )
