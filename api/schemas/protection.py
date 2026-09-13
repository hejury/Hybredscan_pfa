from typing import Optional

from pydantic import BaseModel


class ProtectionStatus(BaseModel):
    """Etat reellement observable du watcher tenu par CE processus API --
    jamais une pretention de protection active si aucun observer ne
    tourne (cahier des charges §28). `configured_directories` liste les
    dossiers configures (watcher.py::DOSSIERS) qui existent reellement sur
    disque, qu'ils soient ou non activement surveilles en ce moment --
    seul `active` indique si la surveillance tourne."""
    active: bool
    configured_directories: list[str]
    auto_quarantine: Optional[bool] = None


class ProtectionEvent(BaseModel):
    time: str
    file_name: str
    verdict: str
    confidence: Optional[float] = None
    detection_source: Optional[str] = None


class ProtectionEventsResponse(BaseModel):
    events: list[ProtectionEvent]


class ProtectionStartRequest(BaseModel):
    auto_quarantine: bool = True
