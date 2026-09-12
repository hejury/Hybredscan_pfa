"""api/services/history_service.py — Pont vers backend_shared.
charger_historique() (le meme chargement defensif que la page Streamlit
Historique). Aucune deuxieme source d'historique : history.csv reste
l'unique source de verite."""
from typing import Optional

from api.schemas.history import HistoryEntry, HistoryResponse
from api.services.analysis_service import parse_action
from backend_shared import charger_historique


def _famille_depuis_nom(nom: str) -> str:
    n = (nom or "").lower()
    if n.endswith((".exe", ".dll")):
        return "pe"
    if n.endswith(".pdf"):
        return "pdf"
    if n.endswith(".docx"):
        return "docx"
    if n.endswith(".doc"):
        return "doc"
    return "inconnu"


def _safe_float(v) -> Optional[float]:
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class HistoryUnavailableError(Exception):
    """history.csv existe mais n'a pas pu etre lu (voir
    backend_shared.charger_historique, statut "erreur")."""


def fetch_history(
    search: Optional[str] = None,
    verdict: Optional[str] = None,
    family: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> HistoryResponse:
    statut, df, avertissements = charger_historique()
    if statut == "absent":
        return HistoryResponse(total=0, warnings=[], items=[])
    if statut == "erreur":
        raise HistoryUnavailableError("history.csv illisible")

    items: list[HistoryEntry] = []
    for _, ligne in df.iterrows():
        items.append(HistoryEntry(
            date=ligne["date"],
            file_name=ligne["fichier"],
            sha256=ligne["sha256"],
            detection_source=ligne["etape"],
            verdict=ligne["verdict"],
            confidence=_safe_float(ligne["confiance"]),
            detections=(ligne["detections"] or None),
            action=parse_action(ligne["action"] or "aucune"),
        ))

    if search:
        q = search.strip().lower()
        items = [i for i in items if q in i.file_name.lower() or q in i.sha256.lower()]
    if verdict:
        items = [i for i in items if i.verdict == verdict]
    if family:
        items = [i for i in items if _famille_depuis_nom(i.file_name) == family]

    total = len(items)
    if offset:
        items = items[offset:]
    if limit is not None:
        items = items[:limit]

    return HistoryResponse(total=total, warnings=avertissements, items=items)
