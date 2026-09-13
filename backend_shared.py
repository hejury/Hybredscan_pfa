#!/usr/bin/env python3
"""backend_shared.py — Fonctions partagees entre app.py (Streamlit) et
api/ (FastAPI), extraites SANS modification de comportement.

Ces fonctions vivaient auparavant uniquement dans app.py, entremelees de
code de rendu Streamlit execute au niveau module (st.set_page_config,
verrou d'authentification avec st.stop(), barre laterale, etc.) -- les
importer directement depuis app.py aurait donc execute tout ce rendu.
Elles sont deplacees ici telles quelles (memes noms, meme logique, memes
docstrings) pour que app.py ET l'API FastAPI appellent exactement le
meme code -- jamais deux implementations paralleles de la securite de
chemin ou de la lecture de l'historique (voir validation/
NEXTJS-FASTAPI-INTEGRATION.md, section "extraction des aides
partagees").

Seul changement reel de comportement : `_config_racines_scan()`
importait `streamlit` au niveau module dans app.py (deja importe pour
tout le reste de l'application) ; ici l'import est local a la fonction,
protege par le meme bloc try/except qu'auparavant -- exactement le motif
deja etabli par analyze.py::_charger_cle_vt() et auth.py::
_compte_configure() pour la meme raison (rester importable sans
dependre d'une execution Streamlit active)."""
import os
from pathlib import Path

import pandas as pd

from analyze import HISTORY, QUARANTINE

# Valeurs de verdict reellement produites par analyze.analyser() -- copie
# fidele des cles de app.py::VERDICTS (qui associe en plus libelle/couleur/
# classe CSS, non pertinents ici). Toute valeur absente de cet ensemble est
# traitee comme une erreur technique neutre, jamais assimilee a "sain".
_VERDICTS_CONNUS = {"malveillant", "sain", "indetermine"}

_COLONNES_HISTORIQUE = ["date", "fichier", "sha256", "etape", "verdict",
                        "confiance", "detections", "action"]

# Extensions candidates pour le scan de dossier (valider_dossier_scan
# ci-dessous) -- decide SEULEMENT quels fichiers sont soumis a
# analyser(), jamais comment ils sont classes ou routes. analyser()
# (analyze.py) reste l'unique source de verite pour l'identification
# reelle du fichier (en-tete binaire, validation structurelle) : un
# executable renome ".pdf"/".docx" suit toujours le routage PE existant,
# une archive quelconque renommee ".docx" echoue toujours la validation
# DOCX -- rien ici ne change ce comportement. Seule constante partagee
# par app.py (Streamlit) ET l'API FastAPI (api/config.py en importe la
# valeur) : jamais deux listes qui pourraient diverger.
EXTENSIONS_SCAN_DOSSIER = (".exe", ".dll", ".pdf", ".docx")


def _cible_interdite(chemin_resolu):
    """Garde-fous frontend minimaux (BF non couverte par le backend) : refuse
    les cibles manifestement dangereuses sans exposer le chemin resolu, sans
    inventer de politique de liste blanche plus large. Voir le rapport de
    cette slice pour la limitation de securite residuelle."""
    if chemin_resolu.parent == chemin_resolu:
        return True  # racine du systeme de fichiers (ex. "C:\\" ou "/")
    try:
        if chemin_resolu == QUARANTINE.resolve():
            return True
    except Exception:
        pass
    if chemin_resolu == (HISTORY.resolve().parent / ".streamlit"):
        return True
    return False


def _config_racines_scan():
    """Source de configuration des racines de scan autorisees -- meme
    mecanisme de repli deja etabli par analyze.py::_charger_cle_vt() pour
    VT_API_KEY : variable d'environnement en priorite (utile pour un
    deploiement/conteneur), sinon .streamlit/secrets.toml (persiste entre
    redemarrages de Streamlit sans dependre d'une variable de processus
    ephemere -- voir validation/FOLDER-SCAN-CONFIG.md). Jamais de valeur
    par defaut codee en dur : en l'absence des deux sources, retourne une
    chaine vide (aucune racine autorisee, fail-safe)."""
    brut = os.environ.get("HYBRIDSCAN_ALLOWED_SCAN_DIRS")
    if brut:
        return brut
    try:
        import streamlit as st
        return st.secrets.get("HYBRIDSCAN_ALLOWED_SCAN_DIRS", "") or ""
    except Exception:
        return ""


def _racines_autorisees():
    """Charge et resout les racines de scan autorisees (voir
    _config_racines_scan ci-dessus pour la source -- variable d'environnement
    HYBRIDSCAN_ALLOWED_SCAN_DIRS puis secrets.toml, separateur os.pathsep —
    ';' sous Windows, ':' sous Linux/macOS ; jamais code en dur). Une racine
    manquante, non repertoire, ou dont la resolution echoue est ignoree
    silencieusement (fail-safe) plutot que de faire echouer tout le reste.
    Aucune racine n'est creee automatiquement."""
    brut = _config_racines_scan()
    racines = []
    for morceau in brut.split(os.pathsep):
        morceau = morceau.strip()
        if not morceau:
            continue
        try:
            p = Path(morceau).expanduser().resolve(strict=True)
            if p.is_dir():
                racines.append(p)
        except Exception:
            continue
    return racines


def _cible_dans_racines_autorisees(chemin_resolu, racines):
    """Verification de confinement robuste (Path.relative_to() apres
    resolution canonique) — jamais une comparaison de prefixe de chaine, qui
    autoriserait a tort un dossier comme "C:\\SafeBackup" quand seul
    "C:\\Safe" est autorise."""
    for racine in racines:
        try:
            chemin_resolu.relative_to(racine)
            return True
        except ValueError:
            continue
    return False


def valider_dossier_scan(dossier, recursif):
    """Valide un chemin de dossier et enumere les fichiers eligibles — lecture
    seule, aucun effet de bord (BF, sections 8/9 de cette slice). Retour :
    (erreur, fichiers, libelle_dossier, n_sousdossiers_ignores)
    `erreur` est None en cas de succes, sinon un message sur pour l'utilisateur
    (jamais le chemin resolu ni une trace technique brute)."""
    dossier = (dossier or "").strip()
    if not dossier:
        return None, [], None, 0

    racines = _racines_autorisees()
    if not racines:
        return "Le scan de dossiers n'est pas configuré par l'administrateur.", [], None, 0

    p = Path(dossier)
    if p.is_file():
        return "Le chemin indiqué ne correspond pas à un dossier.", [], None, 0
    if not p.exists():
        return "Le dossier indiqué est introuvable.", [], None, 0
    if not p.is_dir():
        return "Le chemin indiqué ne correspond pas à un dossier.", [], None, 0

    try:
        resolu = p.resolve(strict=True)
    except Exception:
        return "Ce dossier ne peut pas être analysé pour le moment.", [], None, 0
    if _cible_interdite(resolu):
        return "Ce dossier ne peut pas être analysé depuis cette interface.", [], None, 0
    if not _cible_dans_racines_autorisees(resolu, racines):
        return "Ce dossier n'est pas autorisé pour l'analyse.", [], None, 0

    fichiers, n_sousdossiers_ignores = [], 0
    try:
        if recursif:
            compteur_erreurs = {"n": 0}
            def _compter_erreur(_exc):
                compteur_erreurs["n"] += 1
            for racine, _, noms in os.walk(resolu, onerror=_compter_erreur):
                for n in noms:
                    if n.lower().endswith(EXTENSIONS_SCAN_DOSSIER):
                        fichiers.append(os.path.join(racine, n))
            n_sousdossiers_ignores = compteur_erreurs["n"]
        else:
            for n in os.listdir(resolu):
                chemin_f = os.path.join(resolu, n)
                if os.path.isfile(chemin_f) and n.lower().endswith(EXTENSIONS_SCAN_DOSSIER):
                    fichiers.append(chemin_f)
        libelle_dossier = resolu.name or str(resolu)
    except PermissionError:
        return "HybridScan ne peut pas lire ce dossier.", [], None, 0
    except Exception:
        return "Ce dossier ne peut pas être analysé pour le moment.", [], None, 0

    return None, fichiers, libelle_dossier, n_sousdossiers_ignores


def charger_historique():
    """Chargement defensif de history.csv (BF9) — jamais d'exception qui
    remonte a l'appelant, jamais de ligne invalide assimilee a « sain ».

    Retour : (statut, df, avertissements)
      statut in {"absent", "erreur", "ok"}."""
    if not HISTORY.exists():
        return "absent", None, []
    try:
        df = pd.read_csv(HISTORY, dtype=str, keep_default_na=False)
    except Exception:
        return "erreur", None, []

    avertissements = []
    for col in _COLONNES_HISTORIQUE:
        if col not in df.columns:
            df[col] = ""
            avertissements.append(
                "Colonne absente de l'historique : %s (valeurs vides utilisées)." % col)

    n_invalides = int((~df["verdict"].isin(_VERDICTS_CONNUS)).sum())
    if n_invalides:
        avertissements.append(
            "%d ligne(s) de l'historique portent une valeur de verdict non reconnue ; "
            "elles sont affichées comme « Erreur technique », jamais comme « Sain »." % n_invalides)

    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.notna().any():
        df = (df.assign(_tri=dates)
                .sort_values("_tri", ascending=False, na_position="last")
                .drop(columns="_tri"))
    else:
        df = df.iloc[::-1]
    return "ok", df.reset_index(drop=True), avertissements
