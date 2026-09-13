#!/usr/bin/env python3
"""analyze.py — Orchestrateur du systeme hybride de detection de malwares."""
import os, sys, csv, json, math, shutil, hashlib, pickle
from datetime import datetime
from pathlib import Path
import pefile, requests
import quarantine_manager

def _charger_cle_vt():
    """Charge la cle VirusTotal depuis l'environnement, puis depuis
    .streamlit/secrets.toml. Ne leve jamais d'exception et n'affiche
    jamais la valeur : en son absence, l'appelant recoit simplement None."""
    cle = os.environ.get("VT_API_KEY")
    if cle:
        return cle
    try:
        import streamlit as st
        return st.secrets.get("VT_API_KEY")
    except Exception:
        return None

VT_KEY = _charger_cle_vt()
VT_URL = "https://www.virustotal.com/api/v3/files/"

def _base_dir():
    """Repertoire de base de l'application.

    Par defaut, le repertoire contenant ce fichier (donc le depot lui-meme) :
    fonctionne a l'identique sur Linux, Windows et WSL, quel que soit
    l'emplacement du clone, contrairement a l'ancien
    os.path.expanduser("~/pfe") qui supposait un clone directement sous le
    repertoire personnel de l'utilisateur. Peut etre force explicitement via
    la variable d'environnement HYBRIDSCAN_BASE_DIR (utile pour deployer les
    donnees runtime — historique, quarantaine — ailleurs que dans le depot)."""
    override = os.environ.get("HYBRIDSCAN_BASE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent

BASE = _base_dir()
MODEL_PATH = BASE / "model.pkl"
HISTORY = BASE / "history.csv"
QUARANTINE = BASE / "quarantine"
SEUIL = 0.45   # Optimise par validation croisee (voir exp_seuil.py)

# --- Routage par famille de fichier -----------------------------------------
# Le modele Random Forest PE (etape2_ia/extraire_features) reste strictement
# reserve aux PE Windows. Les formats document ci-dessous beneficient de la
# meme etape 1 (signature VirusTotal) que les PE, mais ne sont JAMAIS transmis
# a pefile/extraire_features/etape2_ia/SHAP — voir identifier_fichier()
# ci-dessous et analyser().
#
# Portee actuelle (voir document_ml/pdf/) : seul le PDF dispose d'une
# validation structurelle reelle et d'un pipeline ML dedie independant.
# DOC/DOCX restent volontairement au comportement de la phase 1 —
# VirusTotal, puis "indetermine" si non concluant, sans validation
# structurelle ni pipeline ML — en attendant une phase Office dediee
# (non commencee : pas d'extraction de caracteristiques Office, pas de
# dataset recherche, pas de modele). Aucun futur format ne doit etre
# ajoute ici sans un routage et, si applicable, un modele dedies : ce
# n'est pas un mecanisme a etendre a la legere.
EXTENSIONS_PE = (".exe", ".dll")
EXTENSIONS_PDF = (".pdf",)
EXTENSIONS_DOC = (".doc",)
EXTENSIONS_DOCX = (".docx",)
EXTENSIONS_DOCUMENT = EXTENSIONS_PDF + EXTENSIONS_DOC + EXTENSIONS_DOCX

def _entete(path, n):
    """Lit uniquement les `n` premiers octets d'un fichier — jamais son
    contenu complet, jamais une ouverture/execution. Sert uniquement a un
    routage sur par signature d'entete, pas a une analyse de contenu."""
    try:
        with open(path, "rb") as fh:
            return fh.read(n)
    except Exception:
        return b""

def _a_entete_pe(path):
    """Vrai si le fichier commence reellement par l'entete DOS 'MZ'. Sert de
    garde-fou anti-contournement : un veritable executable renomme avec une
    extension document (ex. virus.exe -> virus.pdf) doit continuer a suivre
    le pipeline PE existant plutot que d'echapper a l'analyse par modele en
    se faisant passer pour un document non pris en charge par le ML."""
    return _entete(path, 2) == b"MZ"

def _a_entete_pdf(path):
    """Vrai si la signature '%PDF-' est presente dans les 1024 premiers
    octets. La tolerance (plutot qu'une exigence stricte en position 0) suit
    la pratique standard des lecteurs PDF, qui acceptent un court prefixe
    avant l'en-tete ; ce n'est pas un parseur PDF, seule la presence du jeton
    est testee — un texte quelconque renomme en .pdf ne contient pas ce
    jeton et est donc rejete ici."""
    return b"%PDF-" in _entete(path, 1024)

def identifier_fichier(path):
    """Determine la famille ET la validite structurelle d'un fichier, a des
    fins de ROUTAGE et de garde-fou uniquement (BF §2, extension PDF-ML
    phase 2) — jamais une classification de malveillance. Aucun contenu
    document n'est jamais execute, aucune macro lancee, aucun JavaScript
    interprete, aucun lien suivi : seules des signatures d'entete sont lues.

    L'entete binaire reelle est prioritaire sur l'extension declaree pour
    detecter un PE deguise (voir _a_entete_pe). Pour PDF, l'extension
    determine le format ATTENDU et la signature '%PDF-' reelle determine si
    le fichier y correspond effectivement — un fichier texte renomme en
    .pdf est ainsi signale comme structurellement invalide plutot que
    traite comme un PDF authentique.

    DOCX : validation structurelle reelle (voir document_ml/docx/validate.py
    -- signature ZIP, archive ouvrable, parties OOXML minimales presentes).
    Un fichier .docx qui echoue cette validation (texte renomme, ZIP
    quelconque, PE deguise, archive corrompue) est signale invalide, jamais
    transmis au modele DOCX (voir analyser()).

    DOC (legacy OLE) : validation structurelle non implementee (portee
    volontairement limitee a DOCX pour cette phase, prototype de recherche
    PFA) — l'extension seule determine la famille, `valide` vaut toujours
    True, comme en phase 1 ; voir analyser(), qui n'applique aucun
    pipeline ML a cette famille.

    Retour : {"famille": "pe"|"pdf"|"doc"|"docx"|"inconnu",
              "valide": bool,
              "motif_invalide": str | None}."""
    if _a_entete_pe(path):
        return {"famille": "pe", "valide": True, "motif_invalide": None}

    ext = os.path.splitext(path)[1].lower()

    if ext in EXTENSIONS_PE:
        # Extension .exe/.dll mais entete non-MZ : comportement de la phase 1
        # conserve a l'identique — le pipeline PE existant (pefile, dans
        # extraire_features) gere deja ce cas via son propre traitement
        # d'erreur (erreur_pe), inchange par cette extension.
        return {"famille": "pe", "valide": True, "motif_invalide": None}

    if ext in EXTENSIONS_PDF:
        if _a_entete_pdf(path):
            return {"famille": "pdf", "valide": True, "motif_invalide": None}
        return {"famille": "pdf", "valide": False,
                "motif_invalide": "signature %PDF- absente"}

    if ext in EXTENSIONS_DOCX:
        try:
            from document_ml.docx.validate import valider_docx
            resultat = valider_docx(path)
            return {"famille": "docx", "valide": resultat.valide,
                    "motif_invalide": resultat.motif_invalide}
        except Exception as e:
            # Import/validation impossible : jamais un repli silencieux sur
            # "valide" (BF §2 -- meme discipline que _a_entete_pdf pour PDF).
            return {"famille": "docx", "valide": False,
                    "motif_invalide": "validation DOCX indisponible : %s" % e}

    if ext in EXTENSIONS_DOC:
        return {"famille": "doc", "valide": True, "motif_invalide": None}

    return {"famille": "inconnu", "valide": False, "motif_invalide": None}

def famille_fichier(path):
    """Compatibilite ascendante (phase 1) : famille grossiere uniquement
    (pe/document/inconnu), sans information de validite structurelle.
    Conserve pour tout appelant existant ; le nouveau code doit utiliser
    identifier_fichier()."""
    info = identifier_fichier(path)
    if info["famille"] == "pe":
        return "pe"
    if info["famille"] in ("pdf", "doc", "docx"):
        return "document"
    return "inconnu"

SUSPECT_APIS = ["CreateRemoteThread","VirtualAllocEx","WriteProcessMemory","LoadLibraryA",
                "GetProcAddress","RegSetValueExA","InternetOpenA","URLDownloadToFileA",
                "CreateProcessA","ShellExecuteA","WinExec","IsDebuggerPresent",
                "CryptEncrypt","OpenProcess","SetWindowsHookExA","CreateMutexA"]

def sha256(path):
    """BF2 — calcul de l'empreinte SHA-256."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def etape1_virustotal(digest):
    """BF3 — interroge VirusTotal (etape 1)."""
    if not VT_KEY:
        # Cle absente (variable d'environnement VT_API_KEY ou secrets.toml
        # non configures) : on bascule sur l'etape 2 sans exposer de trace
        # technique ni tenter un appel reseau voue a l'echec.
        return {"statut": "erreur_cle_absente"}
    try:
        r = requests.get(VT_URL + digest, headers={"x-apikey": VT_KEY}, timeout=30)
    except requests.exceptions.RequestException as e:
        return {"statut": "erreur_reseau", "detail": str(e)}
    if r.status_code == 404: return {"statut": "inconnu"}
    if r.status_code == 401: return {"statut": "erreur_cle"}
    if r.status_code == 429: return {"statut": "erreur_quota"}
    if r.status_code != 200: return {"statut": "erreur_api", "code": r.status_code}
    stats = r.json()["data"]["attributes"]["last_analysis_stats"]
    mal = stats.get("malicious", 0)
    return {"statut": "malveillant" if mal > 0 else "sain",
            "detections": mal, "total_moteurs": sum(stats.values())}

def entropie(data):
    if not data: return 0.0
    freq = [0]*256
    for b in data: freq[b] += 1
    e, n = 0.0, len(data)
    for c in freq:
        if c:
            p = c/n
            e -= p*math.log2(p)
    return e

def extraire_features(path):
    """BF4 — extraction statique, SANS execution du fichier."""
    pe = None
    try:
        pe = pefile.PE(path, fast_load=True)
        pe.parse_data_directories()
        f = {}
        f["file_size"] = os.path.getsize(path)
        with open(path, "rb") as fh:
            f["entropy"] = round(entropie(fh.read()), 4)
        f["nb_sections"] = len(pe.sections)
        f["size_code"] = pe.OPTIONAL_HEADER.SizeOfCode
        f["size_image"] = pe.OPTIONAL_HEADER.SizeOfImage
        f["entry_point"] = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        f["subsystem"] = pe.OPTIONAL_HEADER.Subsystem
        f["dll_char"] = pe.OPTIONAL_HEADER.DllCharacteristics
        f["machine"] = pe.FILE_HEADER.Machine
        # timestamp retire : fuite de donnees
        ents = [s.get_entropy() for s in pe.sections]
        f["sect_entropy_max"] = round(max(ents),4) if ents else 0
        f["sect_entropy_mean"] = round(sum(ents)/len(ents),4) if ents else 0
        imports, nb_dll = set(), 0
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            nb_dll = len(pe.DIRECTORY_ENTRY_IMPORT)
            for d in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in d.imports:
                    if imp.name: imports.add(imp.name.decode(errors="ignore"))
        f["nb_dll"] = nb_dll
        f["nb_imports"] = len(imports)
        for api in SUSPECT_APIS:
            f["api_"+api] = 1 if api in imports else 0
        return f
    except Exception as e:
        return {"_erreur": str(e)}
    finally:
        if pe:
            try: pe.close()
            except: pass

def etape2_ia(path):
    """BF4 + BF5 — application du modele entraine."""
    if not os.path.exists(MODEL_PATH):
        return {"statut": "erreur_modele", "detail": "model.pkl introuvable"}
    with open(MODEL_PATH, "rb") as fh:
        bundle = pickle.load(fh)
    model, colonnes = bundle["model"], bundle["features"]
    feats = extraire_features(path)
    if "_erreur" in feats:
        return {"statut": "erreur_pe", "detail": feats["_erreur"]}
    try:
        import pandas as pd; vecteur = pd.DataFrame([[feats[c] for c in colonnes]], columns=colonnes)
    except KeyError as e:
        return {"statut": "erreur_features", "detail": "colonne manquante : %s" % e}
    proba = model.predict_proba(vecteur)[0][1]
    return {"statut": "malveillant" if proba >= SEUIL else "sain",
            "confiance": round(float(proba), 4), "features": feats}

def quarantaine(path, verdict, detection_source, *, confidence=None,
                 source_context=quarantine_manager.SOURCE_AUTRE,
                 virus_total_result=None):
    """BF6 — isolation : delegue entierement a quarantine_manager (point
    d'entree unique de la quarantaine, voir validation/QUARANTINE-MVP.md).
    Ne prend aucune decision de malveillance ; consomme le verdict deja
    etabli par analyser(). Leve quarantine_manager.ErreurQuarantaine en cas
    d'echec -- jamais un succes fabrique."""
    meta = quarantine_manager.quarantine_file(
        path, verdict=verdict, detection_source=detection_source,
        confidence=confidence, source_context=source_context,
        virus_total_result=virus_total_result, base_dir=BASE)
    return meta["quarantine_storage_name"]

def journaliser(ligne):
    """BF9 — historique des analyses."""
    champs = ["date","fichier","sha256","etape","verdict","confiance","detections","action"]
    nouveau = not os.path.exists(HISTORY)
    with open(HISTORY, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=champs)
        if nouveau: w.writeheader()
        w.writerow(ligne)

def _predire_pdf(path):
    """Delegue au pipeline ML PDF dedie (document_ml/pdf) — jamais au modele
    PE, jamais un chemin partage avec un quelconque pipeline Office (portee
    de cette phase : PDF uniquement, voir analyser()). Import local et
    protege : si le module ou une dependance est absente, ou leve une
    exception inattendue, on degrade proprement vers un statut d'erreur
    plutot que de faire planter analyser() — meme discipline defensive que
    etape1_virustotal et etape2_ia dans ce fichier."""
    try:
        from document_ml.pdf.predict import predire
        return predire(path)
    except Exception as e:
        return {"statut": "erreur_module", "detail": str(e)}

def _predire_docx(path):
    """Delegue au pipeline ML DOCX dedie (document_ml/docx) — PROTOTYPE DE
    RECHERCHE PFA (voir validation/DOCX-RESEARCH-MODEL-TRAINING.md),
    jamais presente comme pret pour la production. Jamais applique a DOC
    legacy (OLE), jamais au modele PE/PDF. Import local et protege : une
    absence de module/modele degrade proprement vers un statut d'erreur,
    meme discipline que _predire_pdf ci-dessus."""
    try:
        from document_ml.docx.predict import predire
        return predire(path)
    except Exception as e:
        return {"statut": "erreur_module", "detail": str(e)}

def analyser(path, isoler=True, source_context=quarantine_manager.SOURCE_AUTRE):
    """Chaine complete : empreinte -> etape 1 -> routage par famille validee
    -> (etape 2 PE | etape 2 PDF | indetermine DOC/DOCX) -> quarantaine ->
    journal.

    `source_context` (quarantine_manager.SOURCE_UPLOAD/SOURCE_FOLDER_SCAN/
    SOURCE_WATCHER/SOURCE_AUTRE) doit etre fourni par l'appelant : lui seul
    sait si `path` est une copie temporaire d'un televersement (le fichier
    reel de l'utilisateur, ailleurs sur son poste, n'est jamais touche) ou
    un chemin local reel verifie (scan de dossier, watcher). Determine
    `original_removed` dans les metadonnees de quarantaine -- jamais
    devine automatiquement (voir validation/QUARANTINE-MVP.md). La valeur
    par defaut (SOURCE_AUTRE) est le choix le plus sur : elle implique
    `original_removed=False`, jamais une pretention de suppression non
    prouvee.

    PE (.exe/.dll, ou entete MZ reelle) : pipeline entierement inchange
    (etape2_ia, extraire_features, seuil 0.45, SHAP, quarantaine).

    PDF : traverse la meme etape 1 (signature) que les PE. Si celle-ci ne
    conclut pas, le fichier est d'abord valide structurellement
    (identifier_fichier) puis, s'il est valide, delegue a son pipeline ML
    dedie et independant (document_ml/pdf) — jamais a etape2_ia/pefile/SHAP,
    et jamais aux 29 caracteristiques PE. Un PDF structurellement invalide
    (ex. texte renomme .pdf) n'est jamais transmis au modele ; un modele PDF
    absent (aucun model_pdf.pkl sur disque) degrade proprement vers l'etat
    "non pris en charge" de la phase 1, jamais vers une erreur ni un verdict
    fabrique.

    DOCX : traverse la meme etape 1 (signature) que PE/PDF. Si celle-ci ne
    conclut pas, le fichier est d'abord valide structurellement
    (identifier_fichier, voir document_ml/docx/validate.py) puis, s'il est
    valide, delegue a son pipeline ML dedie (document_ml/docx) — un
    PROTOTYPE DE RECHERCHE PFA (voir
    validation/DOCX-RESEARCH-MODEL-TRAINING.md), jamais presente comme
    pret pour la production. Un DOCX structurellement invalide n'est
    jamais transmis au modele. Un verdict "malveillant" issu SEULEMENT du
    modele DOCX (pas d'une signature VirusTotal) n'est PAS automatiquement
    mis en quarantaine par defaut (voir la garde de securite en fin de
    fonction) — cette limitation est documentee et volontaire.

    DOC (legacy OLE) : portee volontairement limitee a DOCX pour cette
    phase — aucune validation structurelle, aucun pipeline ML,
    comportement identique a la phase 1 (VirusTotal -> si non concluant ->
    indetermine)."""
    permettre_quarantaine_auto = True
    r = {"fichier": os.path.basename(path),
         "chemin": os.path.abspath(path),
         "date": datetime.now().isoformat(timespec="seconds")}
    digest = sha256(path)
    r["sha256"] = digest
    vt = etape1_virustotal(digest)
    r["etape1"] = vt

    info = identifier_fichier(path)
    famille = info["famille"]
    r["famille"] = famille

    if vt["statut"] == "malveillant":
        r.update({"etape": "1 (signature)", "verdict": "malveillant", "confiance": 1.0,
                  "detections": "%d/%d" % (vt["detections"], vt["total_moteurs"]),
                  "message": "Fichier reconnu par %d moteurs sur %d." % (vt["detections"], vt["total_moteurs"])})
    elif vt["statut"] == "sain":
        r.update({"etape": "1 (signature)", "verdict": "sain", "confiance": 1.0,
                  "detections": "0/%d" % vt["total_moteurs"],
                  "message": "Fichier connu de VirusTotal, aucune detection (%d moteurs)." % vt["total_moteurs"]})
    elif famille == "pdf":
        if not info["valide"]:
            # Structure non conforme a l'extension .pdf declaree : jamais
            # transmis a un modele, jamais un verdict sain/malveillant
            # fabrique a partir de la seule extension (BF §2).
            r.update({"etape": "2 (format invalide)", "verdict": "indetermine",
                      "confiance": "", "detections": "", "document_ml_supported": False,
                      "message": "Le fichier ne correspond pas à la structure attendue pour "
                                 "l’extension déclarée ; par sécurité, aucune analyse statique "
                                 "n’est effectuée sur ce fichier."})
        else:
            ia_doc = _predire_pdf(path)
            if ia_doc["statut"] in ("modele_absent", "erreur_module"):
                # Aucun modele PDF entraine disponible sur disque : etat
                # identique a la phase 1 (jamais un echec technique affiche
                # a l'utilisateur, jamais un repli sur le modele PE).
                r.update({"etape": "2 (document)", "verdict": "indetermine",
                          "confiance": "", "detections": "", "document_ml_supported": False,
                          "message": "Ce format peut être vérifié par signature, mais il n’est pas pris en "
                                     "charge par le modèle d’analyse statique actuel."})
            elif ia_doc["statut"].startswith("erreur"):
                r.update({"etape": "2 (ia_pdf)", "verdict": "indetermine",
                          "confiance": "", "detections": "", "document_ml_supported": True,
                          "message": "Analyse impossible : %s" % ia_doc.get("detail", ia_doc["statut"])})
            else:
                r.update({"etape": "2 (ia_pdf)", "verdict": ia_doc["statut"],
                          "confiance": ia_doc["confiance"], "detections": "", "document_ml_supported": True,
                          "message": "Fichier inconnu de VirusTotal. Classé par le modèle PDF : %s "
                                     "(confiance %.0f%%)." % (ia_doc["statut"], ia_doc["confiance"] * 100)})
    elif famille == "docx":
        if not info["valide"]:
            # Structure non conforme a l'extension .docx declaree (texte
            # renomme, ZIP quelconque, PE deguise, archive corrompue) :
            # jamais transmis au modele, jamais un verdict fabrique.
            r.update({"etape": "2 (format invalide)", "verdict": "indetermine",
                      "confiance": "", "detections": "", "document_ml_supported": False,
                      "message": "Le fichier ne correspond pas à la structure attendue pour "
                                 "l’extension déclarée ; par sécurité, aucune analyse statique "
                                 "n’est effectuée sur ce fichier."})
        else:
            ia_doc = _predire_docx(path)
            if ia_doc["statut"] in ("modele_absent", "erreur_module"):
                r.update({"etape": "2 (document)", "verdict": "indetermine",
                          "confiance": "", "detections": "", "document_ml_supported": False,
                          "message": "Ce format peut être vérifié par signature, mais il n’est pas pris en "
                                     "charge par le modèle d’analyse statique actuel."})
            elif ia_doc["statut"].startswith("erreur"):
                r.update({"etape": "2 (ia_docx)", "verdict": "indetermine",
                          "confiance": "", "detections": "", "document_ml_supported": True,
                          "message": "Analyse impossible : %s" % ia_doc.get("detail", ia_doc["statut"])})
            else:
                # IA_DOCX -- prototype de recherche (voir
                # validation/DOCX-RESEARCH-MODEL-TRAINING.md) : jamais
                # "production-ready"/"certifie"/un pourcentage de fiabilite
                # garanti dans le message affiche.
                r.update({"etape": "2 (ia_docx)", "verdict": ia_doc["statut"],
                          "confiance": ia_doc["confiance"], "detections": "", "document_ml_supported": True,
                          "message": "Fichier inconnu de VirusTotal. Classé par IA_DOCX — prototype de "
                                     "recherche (confiance %.0f%%). Résultat expérimental, non certifié."
                                     % (ia_doc["confiance"] * 100)})
                if ia_doc["statut"] == "malveillant":
                    # Garde de securite (BF §14) : un verdict malveillant
                    # issu SEULEMENT de ce prototype de recherche DOCX
                    # n'entraine PAS de quarantaine automatique par defaut
                    # -- contrairement a un verdict signature VirusTotal ou
                    # au modele PE/PDF etablis. Documente explicitement,
                    # pas un oubli.
                    permettre_quarantaine_auto = False
    elif famille == "doc":
        # Portee de cette phase : DOCX uniquement (prototype de recherche).
        # DOC (legacy OLE) conserve exactement le comportement de la
        # phase 1 — aucune validation structurelle, aucun pipeline ML.
        r.update({"etape": "2 (document)", "verdict": "indetermine", "confiance": "", "detections": "",
                  "document_ml_supported": False,
                  "message": "Ce format peut être vérifié par signature, mais il n’est pas pris en "
                             "charge par le modèle d’analyse statique actuel."})
    else:
        ia = etape2_ia(path)
        r["etape2"] = ia
        if ia["statut"].startswith("erreur"):
            r.update({"etape": "2 (IA)", "verdict": "indetermine", "confiance": "", "detections": "",
                      "message": "Analyse impossible : %s" % ia.get("detail", ia["statut"])})
        else:
            raison = "inconnu de VirusTotal" if vt["statut"] == "inconnu" else "VirusTotal indisponible (%s)" % vt["statut"]
            r.update({"etape": "2 (IA)", "verdict": ia["statut"], "confiance": ia["confiance"], "detections": "",
                      "message": "Fichier %s. Classe par le modele : %s (confiance %.0f%%)." % (raison, ia["statut"], ia["confiance"]*100)})

    if r["verdict"] == "malveillant" and isoler and permettre_quarantaine_auto:
        try:
            confiance_meta = r["confiance"] if isinstance(r["confiance"], float) else None
            vt_meta = vt if r["etape"] == "1 (signature)" else None
            r["action"] = "quarantaine : " + quarantaine(
                path, r["verdict"], r["etape"], confidence=confiance_meta,
                source_context=source_context, virus_total_result=vt_meta)
        except Exception as e:
            r["action"] = "echec quarantaine : %s" % e
    elif r["verdict"] == "malveillant" and not permettre_quarantaine_auto:
        # Prototype de recherche DOCX (BF §14) : verdict signale a
        # l'utilisateur mais jamais mis en quarantaine automatiquement sur
        # cette seule base -- voir docstring de analyser().
        r["action"] = "aucune (quarantaine automatique desactivee pour IA_DOCX — prototype de recherche)"
    else:
        r["action"] = "aucune"

    journaliser({k: r[k] for k in ["date","fichier","sha256","etape","verdict","confiance","detections","action"]})
    return r

def afficher(r):
    """BF7 — restitution du resultat."""
    B = "=" * 62
    print(B)
    print("  Fichier   : %s" % r["fichier"])
    print("  SHA-256   : %s" % r["sha256"])
    print(B)
    print("  Etape     : %s" % r["etape"])
    print("  Verdict   : %s" % r["verdict"].upper())
    if r["confiance"] != "":
        print("  Confiance : %s" % r["confiance"])
    print()
    print("  %s" % r["message"])
    print()
    print("  Action    : %s" % r["action"])
    print(B)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 analyze.py <fichier> [--no-quarantine]")
        sys.exit(1)
    cible = sys.argv[1]
    if not os.path.isfile(cible):
        print("Fichier introuvable :", cible)
        sys.exit(1)
    afficher(analyser(cible, isoler="--no-quarantine" not in sys.argv))
