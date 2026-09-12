from typing import Optional

from pydantic import BaseModel

from api.schemas.analysis import QuarantineAction


class HistoryEntry(BaseModel):
    """Une ligne de history.csv. `verdict`/`detection_source` restent de
    simples chaines (pas les Literal stricts de schemas/analysis.py) : une
    ligne historique ancienne/malformee peut porter une valeur non
    reconnue -- elle doit rester visible, jamais faire echouer
    l'endpoint (cahier des charges §23)."""
    date: str
    file_name: str
    sha256: str
    detection_source: str
    verdict: str
    confidence: Optional[float] = None
    detections: Optional[str] = None
    action: QuarantineAction


class HistoryResponse(BaseModel):
    total: int
    warnings: list[str]
    items: list[HistoryEntry]
