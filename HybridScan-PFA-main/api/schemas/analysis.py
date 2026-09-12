"""api/schemas/analysis.py — Contrats API stables, deduits des valeurs
REELLEMENT produites par analyze.analyser() (voir analyze.py). Aucune
valeur inventee ; les champs non disponibles pour un resultat donne sont
nullable plutot que fabriques."""
from typing import Literal, Optional

from pydantic import BaseModel

# analyze.py::r["verdict"] -- jamais d'autre valeur produite.
Verdict = Literal["sain", "malveillant", "indetermine"]

# analyze.py::identifier_fichier()["famille"] / r["famille"].
FileFamily = Literal["pe", "pdf", "doc", "docx", "inconnu"]

# analyze.py::r["etape"] -- exactement les valeurs produites aujourd'hui,
# jamais une etape inventee.
DetectionSource = Literal[
    "1 (signature)", "2 (IA)", "2 (ia_pdf)", "2 (ia_docx)",
    "2 (document)", "2 (format invalide)",
]


class QuarantineAction(BaseModel):
    """Forme normalisee de la chaine analyze.py::r["action"] (ex.
    "quarantaine : <nom>", "echec quarantaine : <detail>", "aucune",
    "aucune (quarantaine automatique desactivee pour IA_DOCX...)"),
    parsee cote serveur une seule fois (api/services/analysis_service.py::
    parse_action) pour eviter que chaque page frontend reimplemente ce
    parsing de chaine."""
    kind: Literal["none", "quarantined", "quarantine_failed", "auto_quarantine_disabled"]
    storage_name: Optional[str] = None
    detail: Optional[str] = None
    reason: Optional[str] = None


class VirusTotalResult(BaseModel):
    """analyze.py::etape1_virustotal() -- champs optionnels selon le statut
    (detections/total_moteurs uniquement si statut in {"malveillant","sain"})."""
    statut: str
    detections: Optional[int] = None
    total_moteurs: Optional[int] = None


class AnalysisResult(BaseModel):
    """Projection stable d'un dict `r` retourne par analyze.analyser().
    Champ par champ, voir le commentaire associe pour la cle Python source."""
    filename: str  # nom fourni par le navigateur (jamais le nom temporaire serveur -- voir analysis_service.map_result)
    sha256: str  # r["sha256"]
    family: FileFamily  # r["famille"]
    detection_source: DetectionSource  # r["etape"]
    verdict: Verdict  # r["verdict"]
    confidence: Optional[float] = None  # r["confiance"], "" -> None
    detections: Optional[str] = None  # r["detections"], ex. "12/64"
    message: str  # r["message"]
    document_ml_supported: Optional[bool] = None  # r["document_ml_supported"], absent pour PE
    action: QuarantineAction  # r["action"], parsee
    analyzed_at: str  # r["date"], ISO 8601
    virus_total: Optional[VirusTotalResult] = None  # r["etape1"]
    file_size_bytes: Optional[int] = None
