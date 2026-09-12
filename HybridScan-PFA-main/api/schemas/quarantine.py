from typing import Literal, Optional

from pydantic import BaseModel

# quarantine_manager.py::STATUT_ENREGISTREMENT_* -- valeurs exhaustives.
QuarantineRecordStatus = Literal[
    "isole", "incomplet", "fichier_introuvable", "metadonnees_illisibles", "sans_metadonnees",
]


class QuarantineEntry(BaseModel):
    """Metadonnees uniquement -- jamais le contenu isole (cahier des
    charges §25). Champ par champ, voir quarantine_manager.py::
    _normaliser_enregistrement()."""
    id: str
    status: QuarantineRecordStatus
    display_name: str
    quarantined_at: Optional[str] = None
    detection_source: Optional[str] = None
    reason: Optional[str] = None
    sha256: Optional[str] = None
    confidence: Optional[float] = None
    family: Optional[str] = None
    verdict: Optional[str] = None
    source_context: Optional[str] = None
    original_removed: Optional[bool] = None
    file_size_bytes: Optional[int] = None
    schema_format: Literal["actuel", "legacy"]


class QuarantineListResponse(BaseModel):
    total: int
    isolated: int
    incomplete: int
    warnings: list[str]
    items: list[QuarantineEntry]
