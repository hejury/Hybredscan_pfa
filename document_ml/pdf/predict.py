#!/usr/bin/env python3
"""predict.py — Inference du modele PDF (document_ml.pdf).

Appele uniquement par analyze.py::_predire_pdf(), lui-meme uniquement
invoque pour un PDF deja valide structurellement (identifier_fichier) et
pour lequel VirusTotal n'a pas conclu. N'importe et n'utilise a aucun moment
model.pkl (PE) ; charge exclusivement model_pdf.pkl.

Phase 7 (entrainement final) : utilise desormais le pipeline CIC valide sur
donnees reelles — cic_features.extraire_caracteristiques_cic() et
cic_schema (v3) — au lieu de l'ancien features.py/schema.py de la phase 2
(21 caracteristiques HybridScan-natives, jamais entraine, aucun modele
associe). features.py/schema.py/train.py/evaluate.py restent dans le
depot pour memoire historique mais ne sont plus utilises par l'inference
de production — voir validation/PDF-MODEL-FINAL-EVALUATION.md.

Convention de retour (jamais d'exception qui remonte a l'appelant — meme
discipline defensive que analyze.etape1_virustotal/etape2_ia) :
  {"statut": "sain"|"malveillant", "confiance": float, "features": {...}}
  {"statut": "modele_absent", "features": {...}}     # pas de model_pdf.pkl sur disque
  {"statut": "erreur_extraction", "detail": "..."}    # PDF illisible/vide
  {"statut": "erreur_modele", "detail": "..."}        # bundle absent/corrompu/incompatible
                                                        # OU schema incompatible (§12) —
                                                        # jamais un reordonnancement ou une
                                                        # caracteristique fabriquee en silence.
"""
import pickle

from .cic_features import extraire_caracteristiques_cic
from .cic_schema import MODEL_FILENAME, CIC_SCHEMA_VERSION, CIC_FEATURES

MODEL_FAMILLE_ATTENDUE = "RandomForestClassifier"
FORMAT_SUPPORTE_ATTENDU = "pdf"


def _chemin_modele():
    """Repertoire de base partage avec analyze.py (respecte lui aussi
    HYBRIDSCAN_BASE_DIR) — model_pdf.pkl vit a cote de model.pkl/history.csv,
    jamais dans un chemin different qui degraderait la portabilite deja
    etablie pour le reste de l'application."""
    from analyze import BASE
    return BASE / MODEL_FILENAME


def _verifier_contrat_schema(bundle):
    """Verification de securite au chargement (cahier des charges §12) :
    version de schema, noms ET ordre exact des caracteristiques, famille de
    modele, format supporte. Ne verifie JAMAIS en reordonnant ou en
    fabriquant une valeur par defaut — un echec ici retourne toujours un
    message d'erreur explicite, jamais un vecteur silencieusement corrige.

    Retourne None si le contrat est respecte, sinon une chaine expliquant
    le probleme (utilisee comme "detail" de erreur_modele)."""
    meta = bundle.get("metadata")
    if not isinstance(meta, dict):
        return "metadonnees de modele absentes ou invalides"

    version_bundle = meta.get("schema_version")
    if version_bundle != CIC_SCHEMA_VERSION:
        return ("version de schema incompatible : modele entraine pour la version %r, "
                "code courant en version %r" % (version_bundle, CIC_SCHEMA_VERSION))

    if meta.get("model_family") != MODEL_FAMILLE_ATTENDUE:
        return "famille de modele inattendue : %r" % meta.get("model_family")

    if meta.get("supported_format") != FORMAT_SUPPORTE_ATTENDU:
        return "format supporte inattendu : %r (attendu %r)" % (
            meta.get("supported_format"), FORMAT_SUPPORTE_ATTENDU)

    colonnes = bundle.get("features")
    if not isinstance(colonnes, list) or not colonnes:
        return "liste de caracteristiques du modele absente ou vide"

    # Chaque caracteristique du modele doit etre un nom CIC reconnu, et
    # l'ORDRE relatif dans CIC_FEATURES doit etre respecte (le modele peut
    # utiliser un SOUS-ENSEMBLE, ex. Modele B a 17/19, mais jamais un ordre
    # different ou un nom inconnu).
    inconnues = [c for c in colonnes if c not in CIC_FEATURES]
    if inconnues:
        return "caracteristiques inconnues du schema courant : %s" % inconnues
    indices = [CIC_FEATURES.index(c) for c in colonnes]
    if indices != sorted(indices):
        return "ordre des caracteristiques du modele incompatible avec cic_schema.CIC_FEATURES"

    return None


def predire(path):
    """Extraction -> verification de schema -> modele PDF (si present) ->
    verdict. Ne leve jamais d'exception."""
    feats = extraire_caracteristiques_cic(path)
    if "_erreur" in feats:
        return {"statut": "erreur_extraction", "detail": feats["_erreur"]}

    modele_path = _chemin_modele()
    if not modele_path.exists():
        return {"statut": "modele_absent", "features": feats}

    try:
        # Meme pattern deja etabli pour le modele PE (analyze.py::etape2_ia
        # charge model.pkl de la meme facon) : ce fichier est un artefact
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
