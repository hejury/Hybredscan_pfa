#!/usr/bin/env python3
"""predict.py — Inference du modele DOCX (document_ml.docx).

NON INTEGRE a analyze.py/app.py (cahier des charges §18) : ce module existe
pour permettre de tester manuellement un futur model_docx.pkl une fois
entraine, mais n'est appele par AUCUN chemin de production. DOCX continue
de suivre exactement le comportement existant (VirusTotal -> si non
concluant -> indetermine) tant qu'aucun modele DOCX valide n'a ete entraine
sur un dataset documente ET approuve pour integration.

Aucun model_docx.pkl n'existe a ce stade (voir validation/DOCX-DATASET-PLAN.md
§4) : predire() retournera systematiquement {"statut": "modele_absent", ...}
tant qu'aucun fichier n'a ete depose par un futur train.py.

Convention de retour (jamais d'exception qui remonte a l'appelant — meme
discipline defensive que document_ml.pdf.predict et analyze.etape1_virustotal
/etape2_ia) :
  {"statut": "sain"|"malveillant", "confiance": float, "features": {...}}
  {"statut": "modele_absent", "features": {...}}      # pas de model_docx.pkl sur disque
  {"statut": "erreur_extraction", "detail": "..."}     # DOCX invalide/illisible
  {"statut": "erreur_modele", "detail": "..."}         # bundle absent/corrompu/incompatible
                                                         # OU schema incompatible —
                                                         # jamais un reordonnancement ou une
                                                         # caracteristique fabriquee en silence.
"""
import pickle

from .features import extraire_features_docx
from .schema import MODEL_FILENAME, SCHEMA_VERSION, FEATURES

MODEL_FAMILLE_ATTENDUE = "RandomForestClassifier"
FORMAT_SUPPORTE_ATTENDU = "docx"


def _chemin_modele():
    """Repertoire de base partage avec analyze.py (respecte lui aussi
    HYBRIDSCAN_BASE_DIR) — model_docx.pkl vivrait a cote de model.pkl/
    model_pdf.pkl/history.csv, jamais dans un chemin different. Ce module
    n'est appele par aucun chemin de production a ce stade ; cette fonction
    existe pour que le meme contrat soit teste des maintenant."""
    from analyze import BASE
    return BASE / MODEL_FILENAME


def _verifier_contrat_schema(bundle):
    """Verification de securite au chargement : version de schema, noms ET
    ordre exact des caracteristiques, famille de modele, format supporte.
    Ne corrige JAMAIS en reordonnant ou en fabriquant une valeur par
    defaut — un echec ici retourne toujours un message d'erreur explicite,
    jamais un vecteur silencieusement corrige.

    Retourne None si le contrat est respecte, sinon une chaine expliquant
    le probleme (utilisee comme "detail" de erreur_modele)."""
    meta = bundle.get("metadata")
    if not isinstance(meta, dict):
        return "metadonnees de modele absentes ou invalides"

    version_bundle = meta.get("feature_schema_version")
    if version_bundle != SCHEMA_VERSION:
        return ("version de schema incompatible : modele entraine pour la version %r, "
                "code courant en version %r" % (version_bundle, SCHEMA_VERSION))

    if meta.get("model_family") != MODEL_FAMILLE_ATTENDUE:
        return "famille de modele inattendue : %r" % meta.get("model_family")

    formats = meta.get("supported_formats")
    if not isinstance(formats, list) or FORMAT_SUPPORTE_ATTENDU not in formats:
        return "format supporte inattendu : %r (attendu une liste contenant %r)" % (
            formats, FORMAT_SUPPORTE_ATTENDU)

    colonnes = bundle.get("features")
    if not isinstance(colonnes, list) or not colonnes:
        return "liste de caracteristiques du modele absente ou vide"

    # Chaque caracteristique du modele doit etre un nom reconnu, et l'ORDRE
    # relatif dans schema.FEATURES doit etre respecte (le modele peut
    # utiliser un SOUS-ENSEMBLE, mais jamais un ordre different ou un nom
    # inconnu).
    inconnues = [c for c in colonnes if c not in FEATURES]
    if inconnues:
        return "caracteristiques inconnues du schema courant : %s" % inconnues
    indices = [FEATURES.index(c) for c in colonnes]
    if indices != sorted(indices):
        return "ordre des caracteristiques du modele incompatible avec schema.FEATURES"

    return None


def predire(path):
    """Extraction -> verification de schema -> modele DOCX (si present) ->
    verdict. Ne leve jamais d'exception. Rappel : cette fonction n'est
    appelee par aucun chemin de production (voir docstring du module)."""
    feats = extraire_features_docx(path)
    if "_erreur" in feats:
        return {"statut": "erreur_extraction", "detail": feats["_erreur"]}

    modele_path = _chemin_modele()
    if not modele_path.exists():
        return {"statut": "modele_absent", "features": feats}

    try:
        # Meme pattern deja etabli pour PE (analyze.py::etape2_ia) et PDF
        # (document_ml/pdf/predict.py) : ce fichier serait un artefact
        # genere et depose par notre propre pipeline d'entrainement dans
        # BASE, jamais televerse par un utilisateur ni accessible depuis
        # l'interface — ce n'est pas une entree non fiable. pickle est le
        # format de persistance standard pour un estimateur scikit-learn ;
        # aucune alternative JSON-native n'existe pour un objet de ce type.
        with open(modele_path, "rb") as fh:
            bundle = pickle.load(fh)
    except Exception as e:
        return {"statut": "erreur_modele", "detail": "bundle illisible : %s" % e}

    probleme_schema = _verifier_contrat_schema(bundle)
    if probleme_schema:
        return {"statut": "erreur_modele", "detail": "schema incompatible : %s" % probleme_schema}

    model = bundle["model"]
    colonnes = bundle["features"]
    seuil = bundle["seuil"]

    try:
        vecteur = [[feats[c] for c in colonnes]]
    except KeyError as e:
        return {"statut": "erreur_modele", "detail": "caracteristique manquante : %s" % e}

    try:
        import pandas as pd
        df = pd.DataFrame(vecteur, columns=colonnes)
        proba = float(model.predict_proba(df)[0][1])
    except Exception as e:
        return {"statut": "erreur_modele", "detail": "echec d'inference : %s" % e}

    return {"statut": "malveillant" if proba >= seuil else "sain",
            "confiance": round(proba, 4), "features": feats}
