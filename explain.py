#!/usr/bin/env python3
"""
explain.py — BF8 : explication des decisions du modele (valeurs de Shapley).
Usage : python3 explain.py <fichier>
"""
import os, sys, pickle
from pathlib import Path
import pandas as pd
import shap

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import extraire_features, MODEL_PATH

def expliquer(path, top=8):
    """Retourne la contribution de chaque caracteristique a la decision."""
    with open(MODEL_PATH, "rb") as fh:
        bundle = pickle.load(fh)
    model, colonnes = bundle["model"], bundle["features"]

    feats = extraire_features(path)
    if "_erreur" in feats:
        return {"erreur": feats["_erreur"]}

    X = pd.DataFrame([[feats[c] for c in colonnes]], columns=colonnes)
    proba = float(model.predict_proba(X)[0][1])

    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X)
    # sklearn recent : shape (1, n_features, 2) -> on prend la classe 1
    vals = sv[0][:, 1] if getattr(sv, "ndim", 0) == 3 else sv[1][0]

    contribs = sorted(zip(colonnes, vals, X.iloc[0].values),
                      key=lambda t: -abs(t[1]))[:top]
    return {"proba": proba, "contribs": contribs}

def afficher(path, res):
    if "erreur" in res:
        print("Erreur :", res["erreur"]); return
    verdict = "MALVEILLANT" if res["proba"] >= 0.5 else "SAIN"
    print("=" * 64)
    print("  Fichier : %s" % os.path.basename(path))
    print("  Verdict : %s  (confiance %.1f%%)" % (verdict, res["proba"]*100))
    print("=" * 64)
    print("\n  Contribution de chaque caracteristique a la decision :\n")
    print("  %-26s %14s %12s" % ("Caracteristique", "Valeur", "Impact"))
    print("  " + "-" * 54)
    for nom, sval, val in res["contribs"]:
        sens = "-> malveillant" if sval > 0 else "-> sain"
        print("  %-26s %14s %+12.4f  %s" % (nom, str(val)[:14], sval, sens))
    print()
    print("  Impact positif = pousse vers 'malveillant'")
    print("  Impact negatif = pousse vers 'sain'")
    print("=" * 64)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 explain.py <fichier>"); sys.exit(1)
    p = sys.argv[1]
    if not os.path.isfile(p):
        print("Fichier introuvable :", p); sys.exit(1)
    afficher(p, expliquer(p))
