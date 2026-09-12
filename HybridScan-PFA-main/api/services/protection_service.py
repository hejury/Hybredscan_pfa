"""api/services/protection_service.py — Pont vers watcher.py (Protection,
journal, DOSSIERS). Une SEULE instance Protection est conservee au niveau
module de CE processus API -- jamais demarree automatiquement a l'import
(cahier des charges §29), jamais une deuxieme instance dupliquee : tout
appel passe par _instance() qui reutilise l'objet existant."""
import os
import threading
from typing import Optional

from watcher import DOSSIERS, Protection, journal

from api.schemas.protection import ProtectionEvent, ProtectionStatus

_lock = threading.RLock()
_instance: Optional[Protection] = None


def _obtenir_instance() -> Protection:
    global _instance
    with _lock:
        if _instance is None:
            _instance = Protection()
        return _instance


def _safe_float(v) -> Optional[float]:
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def get_status() -> ProtectionStatus:
    prot = _obtenir_instance()
    existants = [d for d in DOSSIERS if os.path.isdir(d)]
    return ProtectionStatus(active=prot.active, configured_directories=existants)


def get_events() -> list[ProtectionEvent]:
    entrees = journal()
    return [
        ProtectionEvent(
            time=e.get("heure") or "",
            file_name=e.get("fichier") or "",
            verdict=e.get("verdict") or "?",
            confidence=_safe_float(e.get("confiance")),
            detection_source=(e.get("etape") or None),
        )
        for e in entrees
    ]


def start(auto_quarantine: bool) -> ProtectionStatus:
    with _lock:
        prot = _obtenir_instance()
        prot.demarrer(isoler=auto_quarantine)
    status = get_status()
    status.auto_quarantine = auto_quarantine
    return status


def stop() -> ProtectionStatus:
    with _lock:
        prot = _obtenir_instance()
        prot.arreter()
    return get_status()
