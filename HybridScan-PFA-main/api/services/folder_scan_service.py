"""api/services/folder_scan_service.py — Pont vers valider_dossier_scan()
(backend_shared.py, partagee avec app.py) et analyze.analyser(). Aucune
nouvelle politique de securite de chemin ici : la validation/confinement
au(x) repertoire(s) autorise(s) reste entierement celle de
backend_shared.valider_dossier_scan()."""
import os
from pathlib import Path

import quarantine_manager
from analyze import analyser

from api.config import FOLDER_SCAN_EXTENSIONS
from api.schemas.folder_scan import FolderScanConfigResponse, FolderScanFileResult, FolderScanSummary
from api.services.analysis_service import parse_action
from backend_shared import _racines_autorisees, valider_dossier_scan


class FolderScanValidationError(Exception):
    """Chemin refuse par valider_dossier_scan() -- message deja sur pour
    l'utilisateur (jamais un chemin resolu ni une trace technique)."""


def get_config() -> FolderScanConfigResponse:
    racines = _racines_autorisees()
    return FolderScanConfigResponse(
        configured=bool(racines),
        allowed_roots=[str(r) for r in racines],
        supported_extensions=list(FOLDER_SCAN_EXTENSIONS),
    )


def scan_folder(path: str, recursive: bool, automatic_quarantine: bool) -> FolderScanSummary:
    erreur, fichiers, libelle_dossier, n_sousdossiers_ignores = valider_dossier_scan(path, recursive)
    if erreur:
        raise FolderScanValidationError(erreur)

    try:
        base = Path(path).expanduser().resolve()
    except Exception:
        base = None

    resultats: list[FolderScanFileResult] = []
    n_mal = n_sain = n_ind = n_err = 0
    for f in fichiers:
        nom = os.path.basename(f)
        try:
            r = analyser(f, isoler=automatic_quarantine, source_context=quarantine_manager.SOURCE_FOLDER_SCAN)
            verdict = r.get("verdict")
            if verdict == "malveillant":
                n_mal += 1
            elif verdict == "sain":
                n_sain += 1
            elif verdict == "indetermine":
                n_ind += 1
            else:
                n_err += 1
                verdict = "erreur"

            try:
                rel = str(Path(f).resolve().relative_to(base)) if base else nom
            except Exception:
                rel = nom

            confiance = r.get("confiance")
            confidence = float(confiance) if isinstance(confiance, (int, float)) else None

            resultats.append(FolderScanFileResult(
                file_name=nom, relative_path=rel, family=r.get("famille", "inconnu"),
                verdict=verdict, confidence=confidence, detection_source=r.get("etape"),
                action=parse_action(r.get("action", "aucune")), sha256=r.get("sha256"),
            ))
        except Exception:
            n_err += 1
            resultats.append(FolderScanFileResult(
                file_name=nom, relative_path=nom, family="inconnu", verdict="erreur",
                confidence=None, detection_source=None, action=parse_action("aucune"), sha256=None,
            ))

    return FolderScanSummary(
        path=libelle_dossier or path, recursive=recursive, automatic_quarantine=automatic_quarantine,
        processed=len(fichiers), malicious=n_mal, healthy=n_sain, indeterminate=n_ind,
        technical_errors=n_err, skipped_subfolders=n_sousdossiers_ignores, results=resultats,
    )
