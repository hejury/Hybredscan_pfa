from typing import Optional

from pydantic import BaseModel

from api.schemas.history import HistoryEntry


class DashboardKpis(BaseModel):
    """Aucune metrique de precision ML calculee a partir de l'historique
    runtime (cahier des charges §32 -- history.csv ne contient aucune
    verite terrain, un « taux de detection » y serait fabrique). Toutes
    les valeurs ci-dessous sont des comptages directs, jamais une
    statistique inferee."""
    analyses_today: int
    threats_detected: int
    quarantine_count: Optional[int] = None  # None si la quarantaine n'a pas pu etre lue
    total_analyzed: int
    protection_active: bool


class VerdictBreakdown(BaseModel):
    sain: int
    malveillant: int
    indetermine: int


class FileTypeBreakdown(BaseModel):
    """Uniquement les familles reellement prises en charge (cahier des
    charges §12) -- jamais une categorie inventee comme JPG/JS."""
    pe: int
    pdf: int
    docx: int


class DashboardResponse(BaseModel):
    kpis: DashboardKpis
    verdict_breakdown: VerdictBreakdown
    file_type_breakdown: FileTypeBreakdown
    recent_activity: list[HistoryEntry]
