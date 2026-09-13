#!/usr/bin/env python3
"""evaluate.py — Re-evaluation independante d'un model_pdf.pkl deja entraine.

Usage :
    python3 evaluate.py --model model_pdf.pkl --data test_set.csv --label-col label

Charge un bundle modele produit par train.py et un jeu de test EXTERNE
(idealement un jeu tenu a l'ecart de l'entrainement, ou un nouveau jeu de
validation independant obtenu apres coup) et rapporte les memes metriques
que train.py (BF §7) sans jamais reentrainer le modele. Sert a verifier
qu'un modele deploye n'a pas derive, ou a evaluer sur un dataset de test
different de celui utilise a l'entrainement.

Ne pretend jamais qu'un modele est pret pour la production si le jeu de
test fourni est trop petit ou desequilibre pour etre defendable — voir
l'avertissement affiche dans ce cas (BF §7 : "If the dataset is too weak to
support defensible evaluation, say so").
"""
import argparse
import json
import pickle

from schema import FEATURES
from train import evaluer_modele


AVERTISSEMENT_TAILLE_MIN = 30  # sous ce seuil, aucune metrique n'est defendable statistiquement


def charger_jeu_test(chemin_csv, colonne_label):
    import pandas as pd
    df = pd.read_csv(chemin_csv)
    manquantes = [c for c in FEATURES if c not in df.columns]
    if manquantes:
        raise ValueError("colonnes de caracteristiques manquantes dans le CSV : %s" % manquantes)
    X = df[FEATURES].copy()
    y = df[colonne_label].map({"malveillant": 1, "malicious": 1, "sain": 0, "benign": 0, 1: 1, 0: 0})
    if y.isna().any():
        raise ValueError("valeurs d'etiquette non reconnues dans la colonne '%s'" % colonne_label)
    return X, y.astype(int)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="Chemin du bundle model_pdf.pkl a evaluer")
    ap.add_argument("--data", required=True, help="CSV de test (colonnes = schema.FEATURES + label)")
    ap.add_argument("--label-col", default="label")
    args = ap.parse_args()

    with open(args.model, "rb") as fh:
        bundle = pickle.load(fh)

    if list(bundle["features"]) != list(FEATURES):
        print("AVERTISSEMENT : le schema de caracteristiques du modele charge ne correspond pas "
              "au schema courant de document_ml/pdf/schema.py — resultats potentiellement invalides.")

    X_test, y_test = charger_jeu_test(args.data, args.label_col)

    if len(X_test) < AVERTISSEMENT_TAILLE_MIN or len(set(y_test)) < 2:
        print("AVERTISSEMENT : jeu de test trop petit ou a une seule classe (%d echantillons) — "
              "les metriques ci-dessous ne constituent PAS une evaluation defendable. Ne pas "
              "presenter ce modele comme pret pour la production sur cette seule base." % len(X_test))

    rapport = evaluer_modele(bundle["model"], X_test, y_test, bundle["seuil"])
    print(json.dumps(rapport, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
