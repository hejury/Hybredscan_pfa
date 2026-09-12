#!/usr/bin/env python3
"""explain.py — Explication des decisions du modele PDF (document_ml.pdf).

INDEPENDANT de explain.py (PE, racine du depot) : ce module n'importe rien
du pipeline PE, n'est jamais appele pour un PE, et n'utilise que
model_pdf.pkl + cic_schema/cic_features. verifie technique (SHAP
TreeExplainer sur un RandomForestClassifier a 17 caracteristiques) —
techniquement fiable dans cet environnement (meme famille de modele que le
PE, verifie directement avant d'ecrire ce module), donc implemente plutot
que laisse absent.

Convention de retour (jamais d'exception qui remonte a l'appelant) :
  {"proba": float, "contribs": [(nom, valeur_shap, valeur_brute), ...]}
  {"erreur": "..."}
"""
import pickle

from .cic_features import extraire_caracteristiques_cic
from .predict import _chemin_modele, _verifier_contrat_schema


def expliquer(path, top=10):
    """Retourne la contribution SHAP de chaque caracteristique retenue par
    le modele PDF pour ce fichier. Ne leve jamais d'exception -- retourne
    {"erreur": "..."} pour toute condition d'echec (extraction, modele
    absent/incompatible, echec SHAP), jamais une explication fabriquee."""
    feats = extraire_caracteristiques_cic(path)
    if "_erreur" in feats:
        return {"erreur": feats["_erreur"]}

    modele_path = _chemin_modele()
    if not modele_path.exists():
        return {"erreur": "model_pdf.pkl introuvable"}

    try:
        # Meme artefact de confiance que predict.py (voir sa justification) :
        # genere par notre propre pipeline, jamais televerse par un
        # utilisateur.
        with open(modele_path, "rb") as fh:
            bundle = pickle.load(fh)
    except Exception as e:
        return {"erreur": "bundle illisible : %s" % e}

    probleme_schema = _verifier_contrat_schema(bundle)
    if probleme_schema:
        return {"erreur": "schema incompatible : %s" % probleme_schema}

    model = bundle["model"]
    colonnes = bundle["features"]

    try:
        vecteur = [feats[c] for c in colonnes]
    except KeyError as e:
        return {"erreur": "caracteristique manquante : %s" % e}

    try:
        import pandas as pd
        import shap
        X = pd.DataFrame([vecteur], columns=colonnes)
        proba = float(model.predict_proba(X)[0][1])

        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        # Meme convention que le module PE (voir explain.py racine) : sklearn
        # recent renvoie (1, n_features, 2) -> on prend la classe 1 (malveillant).
        vals = sv[0][:, 1] if getattr(sv, "ndim", 0) == 3 else sv[1][0]
    except Exception as e:
        return {"erreur": "echec SHAP : %s" % e}

    contribs = sorted(zip(colonnes, vals, X.iloc[0].values),
                       key=lambda t: -abs(t[1]))[:top]
    return {"proba": proba, "contribs": contribs}
