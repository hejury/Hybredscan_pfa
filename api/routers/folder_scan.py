from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_current_user
from api.schemas.folder_scan import FolderScanConfigResponse, FolderScanRequest, FolderScanSummary
from api.services import folder_scan_service

router = APIRouter(prefix="/api/v1/scan", tags=["folder-scan"])


@router.get("/folder/config", response_model=FolderScanConfigResponse)
async def folder_scan_config(_user: dict = Depends(get_current_user)) -> FolderScanConfigResponse:
    return folder_scan_service.get_config()


@router.post("/folder", response_model=FolderScanSummary)
async def scan_folder(
    payload: FolderScanRequest,
    _user: dict = Depends(get_current_user),
) -> FolderScanSummary:
    """Scanne un dossier server-side deja verifie contre les racines
    autorisees (backend_shared.valider_dossier_scan) -- jamais un chemin
    arbitraire fourni par le navigateur (cahier des charges §40)."""
    try:
        return folder_scan_service.scan_folder(
            payload.path, payload.recursive, payload.automatic_quarantine)
    except folder_scan_service.FolderScanValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Le scan n'a pas pu être effectué pour le moment.",
        )
