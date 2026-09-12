from typing import Literal, Optional

from pydantic import BaseModel, Field

from api.schemas.analysis import DetectionSource, FileFamily, QuarantineAction

# Comme app.py::page "Scan de dossier", un fichier dont l'appel a
# analyser() leve une exception (ex. erreur de lecture disque en cours de
# scan) est compte separement ("erreur") -- une valeur que analyser()
# lui-meme ne produit jamais comme r["verdict"], propre a ce wrapper de
# scan (voir app.py, n_erreur = sum(... r["verdict"] not in VERDICTS)).
FolderScanVerdict = Literal["sain", "malveillant", "indetermine", "erreur"]


class FolderScanRequest(BaseModel):
    path: str = Field(min_length=1)
    recursive: bool = True
    automatic_quarantine: bool = False


class FolderScanFileResult(BaseModel):
    file_name: str
    relative_path: str
    family: FileFamily
    verdict: FolderScanVerdict
    confidence: Optional[float] = None
    detection_source: Optional[DetectionSource] = None
    action: QuarantineAction
    sha256: Optional[str] = None


class FolderScanSummary(BaseModel):
    path: str
    recursive: bool
    automatic_quarantine: bool
    processed: int
    malicious: int
    healthy: int
    indeterminate: int
    technical_errors: int
    skipped_subfolders: int
    results: list[FolderScanFileResult]


class FolderScanConfigResponse(BaseModel):
    configured: bool
    allowed_roots: list[str]
    # Portee actuelle -- jamais elargie silencieusement (cahier des charges §19).
    supported_extensions: list[str]
