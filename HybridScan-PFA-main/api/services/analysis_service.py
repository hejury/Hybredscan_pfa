"""api/services/analysis_service.py — Pont vers analyze.analyser() pour
un fichier televerse. AUCUNE logique de detection ici : ce module ecrit
une copie temporaire du televersement (jamais le chemin fourni par le
navigateur, qui n'est qu'un nom de fichier non fiable), appelle
analyser() exactement comme app.py le fait deja pour la page "Analyser un
fichier", puis convertit le dict resultat en schema API stable."""
import os
import re
import shutil
import tempfile
import uuid

import quarantine_manager
from analyze import analyser

from api.schemas.analysis import AnalysisResult, QuarantineAction, VirusTotalResult

_CARACTERES_SURS = re.compile(r"[^A-Za-z0-9._-]+")


def _nom_fichier_temp_sur(original_filename: str) -> str:
    """Derive un nom de fichier temporaire lisible (pour que history.csv
    reste utile) SANS jamais faire confiance au chemin fourni par le
    navigateur : seul le dernier segment (os.path.basename, qui neutralise
    deja tout ".." ou chemin absolu) est conserve, puis assaini caractere
    par caractere, puis prefixe d'un jeton aleatoire pour eviter toute
    collision/predictibilite. Le fichier reste ecrit dans un repertoire
    temporaire dedie a cette requete (voir analyze_uploaded_file)."""
    base = os.path.basename(original_filename) or "fichier"
    base = _CARACTERES_SURS.sub("_", base) or "fichier"
    return "%s_%s" % (uuid.uuid4().hex[:8], base)


def parse_action(action: str) -> QuarantineAction:
    """Normalise analyze.py::r["action"] (chaine humaine) en forme
    structuree. Les quatre formes reellement produites aujourd'hui (voir
    analyze.py::analyser(), fin de fonction) sont couvertes explicitement ;
    toute forme non reconnue retombe sur "none" plutot que d'inventer un
    etat de quarantaine."""
    action = action or "aucune"
    if action == "aucune":
        return QuarantineAction(kind="none")
    if action.startswith("aucune ("):
        raison = action[len("aucune ("):]
        if raison.endswith(")"):
            raison = raison[:-1]
        return QuarantineAction(kind="auto_quarantine_disabled", reason=raison)
    if action.startswith("quarantaine : "):
        return QuarantineAction(kind="quarantined", storage_name=action[len("quarantaine : "):])
    if action.startswith("echec quarantaine : "):
        return QuarantineAction(kind="quarantine_failed", detail=action[len("echec quarantaine : "):])
    return QuarantineAction(kind="none")


def map_result(r: dict, original_filename: str, file_size_bytes: int | None) -> AnalysisResult:
    """Projette le dict `r` retourne par analyser() dans AnalysisResult --
    jamais de reinterpretation du verdict/de la confiance, uniquement un
    changement de forme (BF : cahier des charges §7/§28).

    `r["fichier"]` est le nom du fichier TEMPORAIRE cote serveur (ex.
    "hybridscan_upload_xxxx.pdf"), jamais affiche a l'utilisateur meme
    dans l'application Streamlit existante (voir app.py::bandeau(), qui
    n'affiche jamais res["fichier"] -- seul fichier.name, le nom fourni
    par le navigateur, est montre via carte("Fichier sélectionné", ...)).
    Le champ `filename` ci-dessous suit donc la meme convention :
    `original_filename`, jamais le nom temporaire interne."""
    confiance = r.get("confiance")
    confidence = float(confiance) if isinstance(confiance, (int, float)) else None

    vt_brut = r.get("etape1")
    virus_total = None
    if isinstance(vt_brut, dict) and vt_brut.get("statut"):
        virus_total = VirusTotalResult(
            statut=vt_brut["statut"],
            detections=vt_brut.get("detections"),
            total_moteurs=vt_brut.get("total_moteurs"),
        )

    return AnalysisResult(
        filename=original_filename,
        sha256=r["sha256"],
        family=r["famille"],
        detection_source=r["etape"],
        verdict=r["verdict"],
        confidence=confidence,
        detections=(r.get("detections") or None),
        message=r.get("message", ""),
        document_ml_supported=r.get("document_ml_supported"),
        action=parse_action(r.get("action", "aucune")),
        analyzed_at=r["date"],
        virus_total=virus_total,
        file_size_bytes=file_size_bytes,
    )


def analyze_uploaded_file(original_filename: str, contents: bytes, auto_quarantine: bool) -> AnalysisResult:
    """Ecrit `contents` dans un fichier temporaire nomme cote serveur --
    jamais `original_filename` utilise directement comme chemin (BF :
    nom fourni par le navigateur non fiable) -- puis appelle analyser()
    avec source_context=SOURCE_UPLOAD (copie temporaire, jamais le
    fichier reel de l'utilisateur -- voir validation/QUARANTINE-MVP.md).
    Le repertoire temporaire dedie (pas seulement le fichier) est
    nettoye que l'analyse ait reussi ou echoue."""
    dossier_temp = tempfile.mkdtemp(prefix="hybridscan_upload_")
    chemin_temp = os.path.join(dossier_temp, _nom_fichier_temp_sur(original_filename))
    try:
        with open(chemin_temp, "wb") as fh:
            fh.write(contents)
        r = analyser(chemin_temp, isoler=auto_quarantine, source_context=quarantine_manager.SOURCE_UPLOAD)
        return map_result(r, original_filename, len(contents))
    finally:
        shutil.rmtree(dossier_temp, ignore_errors=True)
