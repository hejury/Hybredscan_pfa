#!/usr/bin/env python3
"""train.py — Entrainement du modele PDF (document_ml.pdf).

NE PAS EXECUTER sans un dataset dont la provenance est documentee dans
validation/DOCUMENT-DATASET-PLAN.md (BF §5/§12 du cahier des charges
document-ML). Ce script n'invente, ne telecharge et n'execute aucun
echantillon : il attend un fichier CSV de caracteristiques DEJA extraites
(colonnes = document_ml.pdf.schema.FEATURES + une colonne d'etiquette), ou,
a defaut, un dossier de PDF bruts deja labellises par l'appelant (voir
--pdf-dir) sur lesquels ce module applique son propre extracteur statique
(jamais un fichier "arbitraire du poste utilisateur" — l'appelant est
responsable de la provenance et de l'etiquetage de ce dossier).

Usage (dataset de caracteristiques pre-extraites, mode prefere) :
    python3 train.py --data features.csv --label-col label \
        --provenance provenance.json --out model_pdf.pkl

Usage (dossier de PDF bruts labellises par sous-dossier benign/ et
malicious/, extraction via document_ml.pdf.features au moment de
l'entrainement) :
    python3 train.py --pdf-dir dataset/ --provenance provenance.json \
        --out model_pdf.pkl

`provenance.json` doit documenter la source du dataset (voir
validation/DOCUMENT-DATASET-PLAN.md) ; son contenu est copie tel quel dans
les metadonnees du modele produit.
"""
import argparse
import json
import pickle
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Execute toujours comme un script (`python3 train.py ...`), jamais importe
# comme sous-module de document_ml.pdf : Python place automatiquement le
# repertoire de ce fichier (document_ml/pdf/) en tete de sys.path, ce qui
# rend schema.py/features.py directement importables ci-dessous sans
# manipulation supplementaire.
from schema import FEATURES, MODEL_FILENAME, SCHEMA_VERSION


def _charger_depuis_csv(chemin_csv, colonne_label):
    import pandas as pd
    df = pd.read_csv(chemin_csv)
    manquantes = [c for c in FEATURES if c not in df.columns]
    if manquantes:
        raise ValueError("colonnes de caracteristiques manquantes dans le CSV : %s" % manquantes)
    if colonne_label not in df.columns:
        raise ValueError("colonne d'etiquette '%s' absente du CSV" % colonne_label)
    X = df[FEATURES].copy()
    y_brut = df[colonne_label]
    y = y_brut.map({"malveillant": 1, "malicious": 1, "sain": 0, "benign": 0, 1: 1, 0: 0, "1": 1, "0": 0})
    if y.isna().any():
        raise ValueError("valeurs d'etiquette non reconnues dans la colonne '%s' "
                          "(attendu : malveillant/malicious/1 ou sain/benign/0)" % colonne_label)
    return X, y.astype(int)


def _charger_depuis_pdf_dir(dossier):
    """Extrait les caracteristiques de PDF bruts organises en
    <dossier>/benign/*.pdf et <dossier>/malicious/*.pdf. Utilise
    UNIQUEMENT document_ml.pdf.features (extraction statique deja utilisee
    en production) — aucun autre traitement du contenu."""
    from features import extraire_features_pdf
    import pandas as pd

    dossier = Path(dossier)
    lignes, etiquettes, ignores = [], [], []
    for sous_dossier, label in (("benign", 0), ("malicious", 1)):
        for p in sorted((dossier / sous_dossier).glob("*.pdf")):
            feats = extraire_features_pdf(str(p))
            if "_erreur" in feats:
                ignores.append((str(p), feats["_erreur"]))
                continue
            lignes.append(feats)
            etiquettes.append(label)
    if ignores:
        print("Fichiers ignores (extraction impossible) : %d" % len(ignores), file=sys.stderr)
        for chemin, motif in ignores[:20]:
            print("  - %s : %s" % (chemin, motif), file=sys.stderr)
    if not lignes:
        raise ValueError("aucun PDF exploitable trouve sous %s/{benign,malicious}/" % dossier)
    X = pd.DataFrame(lignes, columns=FEATURES)
    y = pd.Series(etiquettes, name="label")
    return X, y


def _seuil_optimal(y_val, proba_val):
    """Determine le seuil de decision a partir des donnees de validation
    (jamais copie du seuil PE 0.45 — BF §6) : balaye les seuils candidats
    issus des probabilites de validation elles-memes et retient celui qui
    maximise le F1-score sur cet ensemble de validation. Retourne
    (seuil, f1_a_ce_seuil)."""
    from sklearn.metrics import f1_score

    candidats = sorted(set(np.round(proba_val, 4)) | {0.5})
    meilleur_seuil, meilleur_f1 = 0.5, -1.0
    for s in candidats:
        pred = (proba_val >= s).astype(int)
        f1 = f1_score(y_val, pred, zero_division=0)
        if f1 > meilleur_f1:
            meilleur_seuil, meilleur_f1 = float(s), float(f1)
    return meilleur_seuil, meilleur_f1


def entrainer(X, y, seed=42, test_size=0.2, val_size=0.2, provenance=None):
    """Entraine un RandomForestClassifier avec repartition stratifiee
    train/validation/test, determine le seuil sur la validation (jamais sur
    le test), puis evalue sur le test tenu a l'ecart (BF §6/§7). Retourne
    (bundle_modele, rapport_evaluation)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    import sklearn

    if len(set(y)) < 2:
        raise ValueError("le dataset ne contient qu'une seule classe — impossible d'entrainer "
                          "un classifieur binaire defendable")

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=(test_size + val_size), random_state=seed, stratify=y)
    part_test_relative = test_size / (test_size + val_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=part_test_relative, random_state=seed, stratify=y_temp)

    model = RandomForestClassifier(
        n_estimators=300, random_state=seed, class_weight="balanced", n_jobs=-1)
    model.fit(X_train, y_train)

    proba_val = model.predict_proba(X_val)[:, 1]
    seuil, f1_val = _seuil_optimal(y_val, proba_val)

    rapport = evaluer_modele(model, X_test, y_test, seuil)
    rapport["f1_validation_au_seuil_retenu"] = f1_val
    rapport["taille_train"] = int(len(X_train))
    rapport["taille_validation"] = int(len(X_val))
    rapport["taille_test"] = int(len(X_test))

    bundle = {
        "model": model,
        "features": list(FEATURES),
        "seuil": seuil,
        "metadata": {
            "model_family": "RandomForestClassifier",
            "supported_formats": ["pdf"],
            "feature_schema_version": SCHEMA_VERSION,
            "training_date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "random_seed": seed,
            "class_distribution_full_dataset": {
                "sain (0)": int((y == 0).sum()), "malveillant (1)": int((y == 1).sum())},
            "threshold": seuil,
            "evaluation_metrics": rapport,
            "library_versions": {
                "python": platform.python_version(),
                "scikit_learn": sklearn.__version__,
                "numpy": np.__version__,
            },
            "dataset_provenance": provenance or {"AVERTISSEMENT": "provenance non fournie a l'entrainement"},
        },
    }
    return bundle, rapport


def evaluer_modele(model, X_test, y_test, seuil):
    """Calcule les metriques d'evaluation sur un jeu de test tenu a l'ecart
    (BF §7) : matrice de confusion, precision, rappel, F1, ROC-AUC, taux de
    faux positifs, nombre de faux negatifs, distribution des classes,
    seuil utilise. Reutilisable independamment de entrainer() par
    evaluate.py pour re-evaluer un modele deja sauvegarde sur un nouveau
    jeu de test."""
    from sklearn.metrics import (confusion_matrix, precision_score, recall_score,
                                  f1_score, roc_auc_score)

    proba_test = model.predict_proba(X_test)[:, 1]
    pred_test = (proba_test >= seuil).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, pred_test, labels=[0, 1]).ravel()
    try:
        roc_auc = float(roc_auc_score(y_test, proba_test)) if len(set(y_test)) == 2 else None
    except ValueError:
        roc_auc = None

    return {
        "seuil": seuil,
        "confusion_matrix": {"vrai_negatif": int(tn), "faux_positif": int(fp),
                              "faux_negatif": int(fn), "vrai_positif": int(tp)},
        "precision": float(precision_score(y_test, pred_test, zero_division=0)),
        "recall": float(recall_score(y_test, pred_test, zero_division=0)),
        "f1": float(f1_score(y_test, pred_test, zero_division=0)),
        "roc_auc": roc_auc,
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else None,
        "false_negative_count": int(fn),
        "class_distribution_test": {"sain (0)": int((y_test == 0).sum()),
                                     "malveillant (1)": int((y_test == 1).sum())},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--data", help="CSV de caracteristiques pre-extraites (colonnes = schema.FEATURES + label)")
    src.add_argument("--pdf-dir", help="Dossier <dir>/benign/*.pdf et <dir>/malicious/*.pdf a extraire")
    ap.add_argument("--label-col", default="label", help="Nom de la colonne d'etiquette dans --data (defaut: label)")
    ap.add_argument("--provenance", required=True,
                     help="Chemin d'un JSON documentant la provenance du dataset (obligatoire — BF §6)")
    ap.add_argument("--out", default=MODEL_FILENAME, help="Chemin de sortie du bundle modele")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--val-size", type=float, default=0.2)
    args = ap.parse_args()

    with open(args.provenance, encoding="utf-8") as fh:
        provenance = json.load(fh)

    if args.data:
        X, y = _charger_depuis_csv(args.data, args.label_col)
    else:
        X, y = _charger_depuis_pdf_dir(args.pdf_dir)

    bundle, rapport = entrainer(X, y, seed=args.seed, test_size=args.test_size,
                                 val_size=args.val_size, provenance=provenance)

    with open(args.out, "wb") as fh:
        pickle.dump(bundle, fh)

    print(json.dumps(rapport, indent=2, ensure_ascii=False))
    print("\nModele ecrit : %s" % args.out)
    print("Seuil retenu (determine sur la validation, PAS copie du seuil PE 0.45) : %.4f" % bundle["seuil"])


if __name__ == "__main__":
    main()
