"""api/services/quarantine_service.py — Pont vers quarantine_manager.py,
point d'entree UNIQUE pour la lecture de la quarantaine (voir
validation/QUARANTINE-MVP.md). Ne lit et ne sert jamais le contenu isole
(.quarantine) -- uniquement les metadonnees deja normalisees par
quarantine_manager.list_quarantine_items()/get_quarantine_details()."""
from typing import Optional

import quarantine_manager
from analyze import BASE

from api.schemas.quarantine import QuarantineEntry, QuarantineListResponse


class QuarantineUnavailableError(Exception):
    """Le repertoire quarantine/ n'a pas pu etre liste (voir
    quarantine_manager.list_quarantine_items, statut "erreur")."""


def _map(e: dict) -> QuarantineEntry:
    return QuarantineEntry(
        id=e["id"],
        status=e["statut"],
        display_name=e["nom_affiche"],
        quarantined_at=e.get("date_isolation"),
        detection_source=e.get("detecte_par"),
        reason=e.get("details"),
        sha256=e.get("sha256"),
        confidence=e.get("confidence"),
        family=e.get("family"),
        verdict=e.get("verdict"),
        source_context=e.get("source_context"),
        original_removed=e.get("original_removed"),
        file_size_bytes=e.get("file_size_bytes"),
        schema_format=e["format"],
    )


def list_quarantine() -> QuarantineListResponse:
    statut, enregistrements, avertissements = quarantine_manager.list_quarantine_items(str(BASE))
    if statut == "absent":
        return QuarantineListResponse(total=0, isolated=0, incomplete=0, warnings=[], items=[])
    if statut == "erreur":
        raise QuarantineUnavailableError()

    items = [_map(e) for e in enregistrements]
    isoles = sum(1 for i in items if i.status == "isole")
    return QuarantineListResponse(
        total=len(items), isolated=isoles, incomplete=len(items) - isoles,
        warnings=avertissements, items=items,
    )


def get_details(item_id: str) -> Optional[QuarantineEntry]:
    e = quarantine_manager.get_quarantine_details(item_id, str(BASE))
    if e is None:
        return None
    return _map(e)
