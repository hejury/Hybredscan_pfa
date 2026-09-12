"""api/services/dashboard_service.py — Agrege history.csv, quarantine/ et
l'etat du watcher en metriques honnetes. Aucune base de donnees
distincte, aucun nombre invente : chaque valeur est un comptage direct
issu des services existants (cahier des charges §31/§32)."""
from datetime import datetime

from api.services import history_service, protection_service, quarantine_service
from api.schemas.dashboard import DashboardKpis, DashboardResponse, FileTypeBreakdown, VerdictBreakdown
from api.services.history_service import _famille_depuis_nom


def get_dashboard() -> DashboardResponse:
    historique = history_service.fetch_history()
    items = historique.items
    aujourdhui = datetime.now().date()

    analyses_today = 0
    verdict_counts = {"sain": 0, "malveillant": 0, "indetermine": 0}
    family_counts = {"pe": 0, "pdf": 0, "docx": 0}

    for i in items:
        try:
            if datetime.fromisoformat(i.date).date() == aujourdhui:
                analyses_today += 1
        except (ValueError, TypeError):
            pass
        if i.verdict in verdict_counts:
            verdict_counts[i.verdict] += 1
        famille = _famille_depuis_nom(i.file_name)
        if famille in family_counts:
            family_counts[famille] += 1

    try:
        quarantine_count = quarantine_service.list_quarantine().total
    except quarantine_service.QuarantineUnavailableError:
        quarantine_count = None

    protection_status = protection_service.get_status()

    return DashboardResponse(
        kpis=DashboardKpis(
            analyses_today=analyses_today,
            threats_detected=verdict_counts["malveillant"],
            quarantine_count=quarantine_count,
            total_analyzed=len(items),
            protection_active=protection_status.active,
        ),
        verdict_breakdown=VerdictBreakdown(**verdict_counts),
        file_type_breakdown=FileTypeBreakdown(**family_counts),
        recent_activity=items[:6],
    )
