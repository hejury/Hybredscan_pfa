import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.config import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB, SUPPORTED_UPLOAD_EXTENSIONS
from api.dependencies import get_current_user
from api.schemas.analysis import AnalysisResult
from api.services import analysis_service

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/file", response_model=AnalysisResult)
async def analyze_file(
    file: UploadFile = File(...),
    auto_quarantine: bool = Form(default=True),
    _user: dict = Depends(get_current_user),
) -> AnalysisResult:
    """Televerse un fichier et l'analyse via le pipeline HybridScan
    existant (analyze.analyser). Le nom fourni par le navigateur n'est
    jamais utilise comme chemin sur disque -- voir
    api/services/analysis_service.py."""
    original_filename = file.filename or "fichier"
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format non pris en charge. Formats acceptés : %s."
                   % ", ".join(SUPPORTED_UPLOAD_EXTENSIONS),
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (maximum %d Mo)." % MAX_UPLOAD_SIZE_MB,
        )
    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide.")

    try:
        return analysis_service.analyze_uploaded_file(original_filename, contents, auto_quarantine)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="L'analyse n'a pas pu être effectuée pour le moment.",
        )
