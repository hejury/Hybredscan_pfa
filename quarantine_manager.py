#!/usr/bin/env python3
"""quarantine_manager.py — Point d'entree UNIQUE pour la quarantaine HybridScan.

Remplace analyze.py::quarantaine() (ecriture) et
app.py::charger_quarantaine() (lecture) par un module centralise. Ni
analyze.py ni app.py ne doivent manipuler directement les fichiers du
repertoire quarantine/ en dehors de ce module (BF3/BF10).

Ce module ne prend AUCUNE decision de malveillance : il consomme un
verdict deja etabli par le pipeline existant (etape1_virustotal/
etape2_ia/document_ml.*.predict) et se contente de l'isoler et d'en
consigner les metadonnees. Jamais d'ouverture, d'execution, d'extraction
d'archive, de resolution de lien, ni d'appel a Office/shell/subprocess/
PowerShell/wscript/cscript sur le contenu mis en quarantaine.

Stockage :
  quarantine/<id>.quarantine   -- charge utile opaque (permissions retirees)
  quarantine/<id>.json         -- metadonnees UTF-8 (voir CONTRAT_METADATA)

`<id>` est un UUID4 genere a chaque appel de quarantine_file() -- jamais
derive du nom de fichier original (protection structurelle contre la
traversee de chemin : le nom original n'est JAMAIS utilise pour construire
un chemin sur disque, uniquement stocke comme valeur de metadonnee).

Compatibilite ascendante : les anciens enregistrements
"<horodatage>_<nom_original>" (+ ".json" au format {nom_origine,
chemin_origine, date_isolation, detecte_par, details}) restent lisibles
par list_quarantine_items()/get_quarantine_details() -- jamais reecrits,
jamais supprimes, champs absents affiches comme "inconnu"/None, jamais
fabriques."""
import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

STATUT_BLOQUE = "bloque"

SOURCE_UPLOAD = "upload"
SOURCE_FOLDER_SCAN = "folder_scan"
SOURCE_WATCHER = "watcher"
SOURCE_AUTRE = "other"

SUFFIXE_PAYLOAD = ".quarantine"
SUFFIXE_META = ".json"

# Libelle humainement lisible de l'etape de detection (utilise par la liste
# et par la raison de blocage) -- CIC de la meme table que
# app.py::_SOURCE_LIBELLES pour rester coherent avec le reste de l'UI.
_LIBELLES_SOURCE_DETECTION = {
    "1 (signature)": "VirusTotal",
    "2 (IA)": "IA PE",
    "2 (ia_pdf)": "IA PDF",
    "2 (ia_docx)": "IA DOCX (prototype de recherche)",
}

# Raison de blocage humainement lisible -- jamais une explication de
# caracteristiques que le modele n'a pas reellement produite (BF8).
_RAISONS_DETECTION = {
    "1 (signature)": "VirusTotal a signalé le fichier comme malveillant.",
    "2 (IA)": "Le moteur IA PE a classé le fichier comme malveillant.",
    "2 (ia_pdf)": "Le moteur IA PDF a classé le document comme malveillant.",
    "2 (ia_docx)": "Le moteur IA DOCX a classé le document comme malveillant.",
}


def libelle_source_detection(etape):
    return _LIBELLES_SOURCE_DETECTION.get(etape, etape or "Source inconnue")


def raison_detection(etape):
    return _RAISONS_DETECTION.get(
        etape, "Le fichier a été classé malveillant par le pipeline d'analyse.")


class ErreurQuarantaine(Exception):
    """Mise en quarantaine impossible -- jamais masquee en silence ; voir
    BF13 (analyser() doit conserver le verdict MALVEILLANT et rapporter
    explicitement l'echec, jamais pretendre que le fichier a ete isole)."""


def _repertoire_quarantaine(base_dir):
    return Path(base_dir) / "quarantine"


def _sha256_fichier(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def quarantine_file(path, *, verdict, detection_source, base_dir,
                     confidence=None, source_context=SOURCE_AUTRE,
                     family=None, virus_total_result=None,
                     original_path_hint=None):
    """Isole `path` (deja juge malveillant par l'appelant) dans
    quarantine/, avec un nom de stockage opaque et des metadonnees
    completes. Ne prend aucune decision de malveillance.

    `source_context` doit valoir SOURCE_UPLOAD si `path` est une copie
    temporaire d'un televersement (le fichier original de l'utilisateur,
    ailleurs sur son poste, n'est ni connu ni accessible) ou
    SOURCE_FOLDER_SCAN/SOURCE_WATCHER si `path` est un chemin reel
    verifie sur le systeme de fichiers local -- cette distinction
    determine `original_removed` dans les metadonnees (BF6, jamais
    invente).

    `original_path_hint` permet de fournir un chemin d'origine distinct de
    `path` lui-meme lorsque pertinent (non utilise actuellement -- reserve
    pour un futur mode watcher qui recevrait un chemin logique different
    du fichier physiquement traite). Par defaut, `path` sert de valeur.

    Retourne le dict de metadonnees ecrit. Leve ErreurQuarantaine si la
    source a disparu, si l'ecriture echoue, ou si le deplacement echoue --
    jamais un succes fabrique."""
    quarantine_dir = _repertoire_quarantaine(base_dir)

    if not os.path.isfile(path):
        raise ErreurQuarantaine("fichier source introuvable : %s" % path)

    try:
        os.makedirs(quarantine_dir, exist_ok=True)
    except OSError as e:
        raise ErreurQuarantaine("impossible de créer le répertoire de quarantaine : %s" % e)

    try:
        sha256 = _sha256_fichier(path)
    except OSError as e:
        raise ErreurQuarantaine("lecture du fichier source impossible : %s" % e)

    try:
        taille = os.path.getsize(path)
    except OSError:
        taille = None

    item_id = uuid.uuid4().hex
    dest_payload = quarantine_dir / (item_id + SUFFIXE_PAYLOAD)
    dest_meta = quarantine_dir / (item_id + SUFFIXE_META)

    nom_origine = os.path.basename(path)
    extension_origine = os.path.splitext(nom_origine)[1].lower()
    chemin_origine = original_path_hint or os.path.abspath(path)
    original_removed = source_context in (SOURCE_FOLDER_SCAN, SOURCE_WATCHER)

    meta = {
        "id": item_id,
        "original_filename": nom_origine,
        "original_path": chemin_origine,
        "original_extension": extension_origine,
        "sha256": sha256,
        "file_size_bytes": taille,
        "quarantined_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": STATUT_BLOQUE,
        "verdict": verdict,
        "detection_source": detection_source,
        "confidence": confidence,
        "reason": raison_detection(detection_source),
        "family": family,
        "virus_total_result": virus_total_result,
        "quarantine_storage_name": dest_payload.name,
        "original_removed": original_removed,
        "source_context": source_context,
    }

    # Deplacement atomique de la charge utile en premier -- si le
    # deplacement echoue, aucune metadonnee orpheline n'est ecrite
    # (BF4 : races/echecs -- jamais un enregistrement incoherent cree).
    try:
        shutil.move(path, dest_payload)
    except OSError as e:
        raise ErreurQuarantaine("déplacement vers la quarantaine impossible : %s" % e)

    try:
        os.chmod(dest_payload, 0o000)
    except OSError:
        pass  # best-effort (portee limitee sous Windows) -- pas bloquant

    try:
        with open(dest_meta, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)
    except OSError as e:
        # La charge utile est deja isolee (comportement de securite
        # prioritaire preserve) mais les metadonnees manquent -- rapporte
        # explicitement plutot que de pretendre un succes complet.
        raise ErreurQuarantaine(
            "fichier isolé mais écriture des métadonnées impossible : %s" % e)

    return meta


# --------------------------------------------------------------------
# Lecture (liste + details) -- jamais d'ouverture du contenu isole.
# --------------------------------------------------------------------

STATUT_ENREGISTREMENT_OK = "isole"
STATUT_ENREGISTREMENT_INCOMPLET = "incomplet"
STATUT_ENREGISTREMENT_FICHIER_INTROUVABLE = "fichier_introuvable"
STATUT_ENREGISTREMENT_META_ILLISIBLE = "metadonnees_illisibles"
STATUT_ENREGISTREMENT_SANS_META = "sans_metadonnees"


def _valeur_texte(meta, cle):
    v = meta.get(cle) if isinstance(meta, dict) else None
    return v if isinstance(v, str) and v else None


def _normaliser_enregistrement(item_id, meta, a_fichier, a_meta, meta_lisible):
    """Convertit un JSON de metadonnees (nouveau OU ancien format) en un
    dict normalise pour l'affichage. Ne fabrique jamais une valeur absente
    -- les champs inconnus restent None.

    `a_meta` (est-ce qu'un fichier .json existe pour cet id) est fourni
    explicitement par l'appelant -- NE PAS le deriver de `meta is not
    None`, qui vaut aussi None quand un .json existe mais est illisible
    (meta_lisible=False), ce qui confondrait "sans metadonnees" et
    "metadonnees illisibles"."""
    nouveau_format = isinstance(meta, dict) and "original_filename" in meta

    if nouveau_format:
        nom_origine = _valeur_texte(meta, "original_filename")
        date_iso = _valeur_texte(meta, "quarantined_at")
        detecte_par = _valeur_texte(meta, "detection_source")
        details = _valeur_texte(meta, "reason")
        sha256 = _valeur_texte(meta, "sha256")
        confiance = meta.get("confidence") if isinstance(meta, dict) else None
        famille = _valeur_texte(meta, "family")
        vt = meta.get("virus_total_result") if isinstance(meta, dict) else None
        verdict = _valeur_texte(meta, "verdict")
        source_context = _valeur_texte(meta, "source_context")
        original_removed = meta.get("original_removed") if isinstance(meta, dict) else None
        taille = meta.get("file_size_bytes") if isinstance(meta, dict) else None
    else:
        # Format legacy (analyze.py::quarantaine, avant centralisation).
        nom_origine = _valeur_texte(meta, "nom_origine") if meta else None
        date_iso = _valeur_texte(meta, "date_isolation") if meta else None
        detecte_par = _valeur_texte(meta, "detecte_par") if meta else None
        details = _valeur_texte(meta, "details") if meta else None
        sha256 = None
        confiance = None
        famille = None
        vt = None
        verdict = "malveillant" if meta else None  # seul verdict que ce chemin ait jamais produit
        source_context = None
        original_removed = None
        taille = None

    if a_meta and not meta_lisible:
        statut = STATUT_ENREGISTREMENT_META_ILLISIBLE
    elif a_meta and a_fichier and (not nom_origine or not date_iso):
        statut = STATUT_ENREGISTREMENT_INCOMPLET
    elif a_meta and not a_fichier:
        statut = STATUT_ENREGISTREMENT_FICHIER_INTROUVABLE
    elif a_fichier and not a_meta:
        statut = STATUT_ENREGISTREMENT_SANS_META
    else:
        statut = STATUT_ENREGISTREMENT_OK

    return {
        "id": item_id,
        "statut": statut,
        "nom_affiche": nom_origine or "Fichier non identifié",
        "date_isolation": date_iso,
        "detecte_par": detecte_par,
        "details": details,
        "sha256": sha256,
        "confidence": confiance,
        "family": famille,
        "virus_total_result": vt,
        "verdict": verdict,
        "source_context": source_context,
        "original_removed": original_removed,
        "file_size_bytes": taille,
        "format": "actuel" if nouveau_format else "legacy",
    }


def list_quarantine_items(base_dir):
    """Retourne (statut_chargement, enregistrements, avertissements) sans
    JAMAIS ouvrir le contenu des charges utiles isolees.

    statut_chargement in {"absent", "erreur", "ok"}. Un enregistrement
    malforme/orphelin n'empeche jamais l'affichage des autres (BF9)."""
    quarantine_dir = _repertoire_quarantaine(base_dir)
    if not quarantine_dir.is_dir():
        return "absent", [], []
    try:
        noms = sorted(os.listdir(quarantine_dir))
    except OSError:
        return "erreur", [], []

    fichiers = {n[:-len(SUFFIXE_PAYLOAD)] for n in noms if n.endswith(SUFFIXE_PAYLOAD)}
    # Compatibilite ascendante : anciens payloads sans extension .quarantine
    # (horodatage_nomorigine, sans suffixe reconnu) -- l'identifiant EST le
    # nom de fichier complet, rien a retirer (contrairement au nouveau
    # format ou l'id est retrouve en retirant le suffixe .quarantine).
    fichiers |= {n for n in noms
                 if not n.endswith(SUFFIXE_META) and not n.endswith(SUFFIXE_PAYLOAD)}
    metadonnees = {n[:-len(SUFFIXE_META)] for n in noms if n.endswith(SUFFIXE_META)}

    enregistrements = []
    for item_id in sorted(fichiers | metadonnees):
        a_fichier = item_id in fichiers
        a_meta = item_id in metadonnees
        meta, meta_lisible = None, True
        if a_meta:
            try:
                with open(quarantine_dir / (item_id + SUFFIXE_META), "r", encoding="utf-8") as fh:
                    contenu = json.load(fh)
                meta = contenu if isinstance(contenu, dict) else None
                meta_lisible = meta is not None
            except (OSError, ValueError, UnicodeDecodeError):
                # ValueError couvre json.JSONDecodeError ; UnicodeDecodeError
                # couvre les anciens fichiers ecrits dans un encodage non-UTF-8
                # (observe sur des enregistrements legacy reels) -- un
                # enregistrement malforme ne doit jamais interrompre
                # l'affichage des autres (BF12).
                meta_lisible = False
        enregistrements.append(_normaliser_enregistrement(item_id, meta, a_fichier, a_meta, meta_lisible))

    avertissements = []
    n_incoherents = sum(1 for e in enregistrements if e["statut"] != STATUT_ENREGISTREMENT_OK)
    if n_incoherents:
        avertissements.append(
            "%d enregistrement(s) de quarantaine sont incomplets ou incohérents ; "
            "ils restent affichés ci-dessous avec leur statut." % n_incoherents)

    # Plus recent en premier (BF9) -- tri par date de quarantaine quand
    # disponible, sinon par id (ordre alphabetique stable), jamais un
    # classement qui masquerait un enregistrement.
    enregistrements.sort(key=lambda e: (e["date_isolation"] or "", e["id"]), reverse=True)
    return "ok", enregistrements, avertissements


def get_quarantine_details(item_id, base_dir):
    """Retourne le dict de metadonnees normalise pour UN element, par id,
    ou None si introuvable. Ne renvoie jamais le contenu de la charge
    utile -- metadonnees uniquement (BF10)."""
    statut, enregistrements, _ = list_quarantine_items(base_dir)
    if statut != "ok":
        return None
    for e in enregistrements:
        if e["id"] == item_id:
            return e
    return None
