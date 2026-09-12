#!/usr/bin/env python3
"""
exp_imbalance.py — Etude comparative des strategies de reequilibrage.
Compare 5 approches sur le meme jeu de donnees, en validation croisee.
"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import recall_score, precision_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline as SkPipeline
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek
warnings.filterwarnings("ignore")

CSV = os.path.expanduser("~/pfe/dataset.csv")
df = pd.read_csv(CSV)
X, y = df.drop("label", axis=1), df["label"]
n_mal = int(y.sum()); n_sain = len(y) - n_mal

print("=" * 68)
print("  ETUDE COMPARATIVE DES STRATEGIES DE REEQUILIBRAGE")
print("=" * 68)
print("  Jeu de donnees : %d lignes, %d caracteristiques" % X.shape)
print("  Sains : %d | Malveillants : %d | Ratio : 1 pour %.1f"
      % (n_sain, n_mal, n_sain / max(n_mal, 1)))

# k adapte au nombre de malwares (au moins 2 par pli)
k = min(5, n_mal // 2) if n_mal >= 4 else 2
print("  Validation croisee stratifiee : %d plis\n" % k)

def rf(**kw):
    return RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, **kw)

STRATEGIES = {
    "1. Baseline (aucun traitement)":
        SkPipeline([("clf", rf())]),
    "2. Class weights (ponderation)":
        SkPipeline([("clf", rf(class_weight="balanced"))]),
    "3. Random UnderSampling":
        ImbPipeline([("ech", RandomUnderSampler(random_state=42)), ("clf", rf())]),
    "4. SMOTE (sur-echantillonnage)":
        ImbPipeline([("ech", SMOTE(random_state=42, k_neighbors=min(5, n_mal - 1))), ("clf", rf())]),
    "5. SMOTE + Tomek Links":
        ImbPipeline([("ech", SMOTETomek(random_state=42,
                      smote=SMOTE(random_state=42, k_neighbors=min(5, n_mal - 1)))), ("clf", rf())]),
}

cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
resultats = []

for nom, pipe in STRATEGIES.items():
    rec, pre, f1s, auc = [], [], [], []
    for itr, ite in cv.split(X, y):
        Xtr, Xte = X.iloc[itr], X.iloc[ite]
        ytr, yte = y.iloc[itr], y.iloc[ite]
        try:
            pipe.fit(Xtr, ytr)
            p = pipe.predict(Xte)
            pr = pipe.predict_proba(Xte)[:, 1]
            rec.append(recall_score(yte, p, zero_division=0))
            pre.append(precision_score(yte, p, zero_division=0))
            f1s.append(f1_score(yte, p, zero_division=0))
            auc.append(roc_auc_score(yte, pr) if len(set(yte)) > 1 else np.nan)
        except Exception as e:
            print("  ! %s : %s" % (nom, e)); break
    if rec:
        resultats.append({
            "Strategie": nom,
            "Rappel": np.mean(rec), "Rappel_sd": np.std(rec),
            "Precision": np.mean(pre), "F1": np.mean(f1s),
            "ROC-AUC": np.nanmean(auc),
        })

res = pd.DataFrame(resultats)

print("  %-34s %14s %10s %8s %8s" % ("STRATEGIE", "RAPPEL", "PRECISION", "F1", "AUC"))
print("  " + "-" * 64)
for _, r in res.iterrows():
    print("  %-34s %.3f (+-%.3f) %8.3f %8.3f %8.3f"
          % (r["Strategie"], r["Rappel"], r["Rappel_sd"],
             r["Precision"], r["F1"], r["ROC-AUC"]))

best = res.loc[res["Rappel"].idxmax()]
print("\n  Meilleur rappel : %s (%.3f)" % (best["Strategie"], best["Rappel"]))
best_f1 = res.loc[res["F1"].idxmax()]
print("  Meilleur F1     : %s (%.3f)" % (best_f1["Strategie"], best_f1["F1"]))

out = os.path.expanduser("~/pfe/resultats_imbalance.csv")
res.round(4).to_csv(out, index=False)
print("\n  Resultats enregistres : %s" % out)
print("=" * 68)
