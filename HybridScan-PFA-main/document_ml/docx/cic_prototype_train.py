#!/usr/bin/env python3
"""cic_prototype_train.py — Entrainement du PROTOTYPE de recherche DOCX
(document_ml.docx), a partir du dataset CIC-Trap4Phish 2025.

NE CONSTITUE PAS UN PIPELINE DE PRODUCTION. Ce script est un artefact de
recherche ponctuel (comme document_ml/pdf/cic_features.py/cic_cleaning.py
l'ont ete pour PDF), distinct du pipeline generique reutilisable
train.py/evaluate.py (qui reste pour un futur dataset propre).

Source : datasets/docx/Word_All_features.csv (voir
validation/DOCX-CIC-INSPECTION.md -- dataset marque "NOT APPROVED FOR
MODEL TRAINING" en tant que source de PRODUCTION, mais explicitement
autorise cette phase pour un PROTOTYPE DE RECHERCHE PFA documente comme
tel -- voir validation/DOCX-RESEARCH-MODEL-TRAINING.md).

Seules les colonnes CIC dont l'equivalence de methode avec
document_ml/docx/features.py a ete PROUVEE par lecture du code source
officiel (datasets/docx/cic_reference/Doc_Feature_Extraction.ipynb) sont
utilisees -- voir validation/DOCX-CIC-COMPATIBILITY.md. AUCUNE colonne
identifiante (file_name/hash/source) n'est utilisee. `dde_present` est
EXCLU explicitement (contradiction prouvee avec le code de reference)."""
import json
import pickle
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (confusion_matrix, precision_score, recall_score,
                              f1_score, fbeta_score, roc_auc_score)
from sklearn.model_selection import train_test_split
import sklearn

PROJECT_ROOT = r"C:\Users\user\Desktop\PFA_PRJECT-main\PFA_PRJECT-main\Desktop\project_pfa\pfe"
CIC_CSV = PROJECT_ROOT + r"\datasets\docx\Word_All_features.csv"
SEED = 42

MODEL_A_MAP = {
    "file_size": "file_size_bytes",
    "macro_present": "has_vba_macros",
}
MODEL_B_MAP = dict(MODEL_A_MAP)
MODEL_B_MAP["entropy"] = "xml_text_entropy"


def _charger_donnees_brutes():
    df = pd.read_csv(CIC_CSV)
    n_avant = len(df)
    masque_echec = (df["file_size"] == 0) & (df["entropy"] == 0.0) & (df["ole_object_count"] == 0)
    n_echec = int(masque_echec.sum())
    df = df[~masque_echec].reset_index(drop=True)
    return df, n_avant, n_echec


def _construire_table(df, mapping):
    cols_cic = list(mapping.keys())
    cols_runtime = list(mapping.values())
    sous_df = df[cols_cic + ["label"]].copy()
    sous_df.columns = cols_runtime + ["label"]
    groupes = sous_df.groupby(cols_runtime, dropna=False).ngroup()
    X = sous_df[cols_runtime].astype(float)
    y = sous_df["label"].astype(int)
    return X, y, groupes.values, cols_runtime


def split_group_aware(y, groupes, seed=SEED):
    """Split 70/15/15 au niveau des GROUPES (vecteurs de caracteristiques
    distincts), stratifie par la classe du groupe (chaque groupe est pur
    -- 0 groupe a etiquette conflictuelle, verifie prealablement). Retourne
    des masques booleens (train, val, test) au niveau des LIGNES."""
    df_g = pd.DataFrame({"groupe": groupes, "label": y})
    label_par_groupe = df_g.groupby("groupe")["label"].first()
    groupes_uniques = label_par_groupe.index.values
    labels_uniques = label_par_groupe.values

    g_train, g_temp, l_train, l_temp = train_test_split(
        groupes_uniques, labels_uniques, test_size=0.30, random_state=seed, stratify=labels_uniques)
    g_val, g_test, _, _ = train_test_split(
        g_temp, l_temp, test_size=0.50, random_state=seed, stratify=l_temp)

    s_train, s_val, s_test = set(g_train), set(g_val), set(g_test)
    assert not (s_train & s_val) and not (s_train & s_test) and not (s_val & s_test), \
        "fuite de groupe entre splits"

    m_train = pd.Series(groupes).isin(s_train).values
    m_val = pd.Series(groupes).isin(s_val).values
    m_test = pd.Series(groupes).isin(s_test).values
    return m_train, m_val, m_test


def _seuil_f2(y_val, proba_val):
    """Seuil choisi sur la VALIDATION SEULE, en maximisant le F2-score
    (rappel pondere 2x plus que la precision) -- coherent avec la
    priorite donnee au rappel malware tout en evitant un taux de faux
    positifs catastrophique (verifie a posteriori, pas optimise
    directement)."""
    candidats = sorted(set(np.round(proba_val, 4)) | {0.5})
    meilleur_seuil, meilleur_f2 = 0.5, -1.0
    for s in candidats:
        pred = (proba_val >= s).astype(int)
        f2 = fbeta_score(y_val, pred, beta=2, zero_division=0)
        if f2 > meilleur_f2:
            meilleur_seuil, meilleur_f2 = float(s), float(f2)
    return meilleur_seuil, meilleur_f2


def entrainer_petite_grille(X_train, y_train, X_val, y_val, seed=SEED):
    """Petite grille raisonnable (2x3=6 combinaisons), selectionnee UNIQUEMENT
    sur la validation (F2), jamais sur le test."""
    grille = [(n, d) for n in (100, 300) for d in (None, 8, 15)]
    meilleur = None
    for n_estimators, max_depth in grille:
        model = RandomForestClassifier(
            n_estimators=n_estimators, max_depth=max_depth, random_state=seed,
            class_weight="balanced", n_jobs=-1)
        model.fit(X_train, y_train)
        proba_val = model.predict_proba(X_val)[:, 1]
        seuil, f2 = _seuil_f2(y_val, proba_val)
        if meilleur is None or f2 > meilleur["f2_validation"]:
            meilleur = {"model": model, "n_estimators": n_estimators, "max_depth": max_depth,
                        "seuil": seuil, "f2_validation": f2}
    return meilleur


def evaluer(model, X, y, seuil):
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= seuil).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    try:
        roc_auc = float(roc_auc_score(y, proba)) if len(set(y)) == 2 else None
    except ValueError:
        roc_auc = None
    return {
        "seuil": seuil,
        "accuracy": float((tn + tp) / len(y)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": roc_auc,
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else None,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) else None,
        "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
        "proba_mean_classe0": float(proba[y == 0].mean()) if (y == 0).any() else None,
        "proba_mean_classe1": float(proba[y == 1].mean()) if (y == 1).any() else None,
        "proba_std_classe0": float(proba[y == 0].std()) if (y == 0).any() else None,
        "proba_std_classe1": float(proba[y == 1].std()) if (y == 1).any() else None,
    }


def auc_descriptive(y, x):
    s = pd.Series(x)
    ranks = s.rank().values
    n1 = int((y == 1).sum())
    n0 = int((y == 0).sum())
    if n1 == 0 or n0 == 0:
        return None
    sum_ranks_pos = ranks[y == 1].sum()
    auc = (sum_ranks_pos - n1 * (n1 + 1) / 2) / (n1 * n0)
    return float(auc)


def executer_modele(nom, mapping, df, seed=SEED):
    print("\n" + "#" * 70)
    print("#  %s" % nom)
    print("#" * 70)

    X, y, groupes, cols = _construire_table(df, mapping)
    y = y.values

    m_train, m_val, m_test = split_group_aware(y, groupes, seed=seed)
    X_train, y_train = X[m_train], y[m_train]
    X_val, y_val = X[m_val], y[m_val]
    X_test, y_test = X[m_test], y[m_test]

    print("Split -- train: %d (mal=%d, sain=%d)  val: %d (mal=%d, sain=%d)  "
          "test: %d (mal=%d, sain=%d)" % (
              len(X_train), (y_train == 1).sum(), (y_train == 0).sum(),
              len(X_val), (y_val == 1).sum(), (y_val == 0).sum(),
              len(X_test), (y_test == 1).sum(), (y_test == 0).sum()))

    # Preuve de non-fuite de doublons entre splits (au niveau des groupes,
    # deja garanti par construction dans split_group_aware -- verifie ici
    # une seconde fois de facon independante sur les VALEURS reelles,
    # pas seulement les indices de groupe).
    vecteurs_train = set(map(tuple, X_train.values.tolist()))
    vecteurs_val = set(map(tuple, X_val.values.tolist()))
    vecteurs_test = set(map(tuple, X_test.values.tolist()))
    chevauchement = (vecteurs_train & vecteurs_val) | (vecteurs_train & vecteurs_test) | (vecteurs_val & vecteurs_test)
    print("Preuve anti-fuite de doublons : vecteurs partages entre splits =", len(chevauchement))
    assert len(chevauchement) == 0, "FUITE DE DOUBLONS ENTRE SPLITS DETECTEE"

    meilleur = entrainer_petite_grille(X_train, y_train, X_val, y_val, seed=seed)
    model, seuil = meilleur["model"], meilleur["seuil"]
    print("Meilleurs hyperparametres (choisis sur validation, F2) : n_estimators=%d max_depth=%s"
          % (meilleur["n_estimators"], meilleur["max_depth"]))

    rapport_val = evaluer(model, X_val, y_val, seuil)
    print("Seuil retenu (validation, F2) : %.4f" % seuil)
    print("Validation :", json.dumps(rapport_val, indent=2))

    rapport_test = evaluer(model, X_test, y_test, seuil)
    print("Test tenu a l'ecart (touche UNE SEULE FOIS) :", json.dumps(rapport_test, indent=2))

    # --- A. Test de sanite par permutation des etiquettes ---
    rng = np.random.RandomState(seed)
    y_train_shuffle = rng.permutation(y_train)
    model_shuffle = RandomForestClassifier(
        n_estimators=meilleur["n_estimators"], max_depth=meilleur["max_depth"],
        random_state=seed, class_weight="balanced", n_jobs=-1)
    model_shuffle.fit(X_train, y_train_shuffle)
    proba_val_shuffle = model_shuffle.predict_proba(X_val)[:, 1]
    try:
        auc_shuffle = float(roc_auc_score(y_val, proba_val_shuffle))
    except ValueError:
        auc_shuffle = None
    print("Test permutation des etiquettes -- ROC-AUC validation (attendu ~0.5) :", auc_shuffle)

    # --- B. AUC descriptive par caracteristique individuelle ---
    auc_par_feature = {c: auc_descriptive(y_train, X_train[c].values) for c in cols}
    print("AUC descriptive individuelle (train) :", json.dumps(auc_par_feature, indent=2))

    # --- C. Ablation de la caracteristique dominante ---
    dominante = max(auc_par_feature, key=lambda c: abs(auc_par_feature[c] - 0.5))
    cols_sans_dominante = [c for c in cols if c != dominante]
    ablation = None
    if cols_sans_dominante:
        model_abl = RandomForestClassifier(
            n_estimators=meilleur["n_estimators"], max_depth=meilleur["max_depth"],
            random_state=seed, class_weight="balanced", n_jobs=-1)
        model_abl.fit(X_train[cols_sans_dominante], y_train)
        proba_val_abl = model_abl.predict_proba(X_val[cols_sans_dominante])[:, 1]
        seuil_abl, _ = _seuil_f2(y_val, proba_val_abl)
        rapport_abl = evaluer(model_abl, X_test[cols_sans_dominante], y_test, seuil_abl)
        ablation = {"caracteristique_retiree": dominante, "colonnes_restantes": cols_sans_dominante,
                    "test_sans_cette_caracteristique": rapport_abl}
        print("Ablation de '%s' -- test :" % dominante, json.dumps(rapport_abl, indent=2))
    else:
        print("Ablation impossible : une seule caracteristique dans ce modele.")

    return {
        "nom": nom,
        "colonnes": cols,
        "mapping_cic": mapping,
        "n_train": int(len(X_train)), "n_val": int(len(X_val)), "n_test": int(len(X_test)),
        "classes_train": {"malveillant": int((y_train == 1).sum()), "sain": int((y_train == 0).sum())},
        "classes_val": {"malveillant": int((y_val == 1).sum()), "sain": int((y_val == 0).sum())},
        "classes_test": {"malveillant": int((y_test == 1).sum()), "sain": int((y_test == 0).sum())},
        "hyperparametres": {"n_estimators": meilleur["n_estimators"], "max_depth": meilleur["max_depth"],
                             "random_state": seed, "class_weight": "balanced"},
        "seuil": seuil,
        "f2_validation": meilleur["f2_validation"],
        "metrics_validation": rapport_val,
        "metrics_test": rapport_test,
        "duplicate_leakage_proof_overlap": len(chevauchement),
        "label_shuffle_auc_validation": auc_shuffle,
        "single_feature_auc": auc_par_feature,
        "ablation": ablation,
        "model_object": model,
    }


if __name__ == "__main__":
    df, n_avant, n_echec = _charger_donnees_brutes()
    print("Lignes avant exclusion :", n_avant)
    print("Lignes exclues (extraction manifestement echouee) :", n_echec)
    print("Lignes retenues :", len(df))

    resultat_a = executer_modele("MODELE A -- CONSERVATEUR", MODEL_A_MAP, df)
    resultat_b = executer_modele("MODELE B -- RECHERCHE ETENDUE", MODEL_B_MAP, df)

    # Sauvegarde des resultats (sans les objets modele, non serialisables
    # proprement en JSON) pour documentation.
    def _sans_model(d):
        return {k: v for k, v in d.items() if k != "model_object"}

    with open(PROJECT_ROOT + r"\datasets\docx\cic_prototype_results.json", "w", encoding="utf-8") as fh:
        json.dump({"modele_a": _sans_model(resultat_a), "modele_b": _sans_model(resultat_b),
                    "n_lignes_avant_exclusion": n_avant, "n_lignes_exclues": n_echec,
                    "n_lignes_retenues": len(df)}, fh, indent=2, ensure_ascii=False)

    with open(PROJECT_ROOT + r"\datasets\docx\cic_prototype_model_a.pkl", "wb") as fh:
        pickle.dump(resultat_a["model_object"], fh)
    with open(PROJECT_ROOT + r"\datasets\docx\cic_prototype_model_b.pkl", "wb") as fh:
        pickle.dump(resultat_b["model_object"], fh)

    print("\nResultats ecrits dans datasets/docx/cic_prototype_results.json")
