#!/usr/bin/env python3
"""
exp_modeles.py — Comparaison de familles d'algorithmes.
Justifie empiriquement le choix du modele retenu.
"""
import os, time, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import recall_score, precision_score, f1_score, roc_auc_score
warnings.filterwarnings("ignore")

CSV = os.path.expanduser("~/pfe/dataset.csv")
df = pd.read_csv(CSV)
X, y = df.drop("label", axis=1), df["label"]
n_mal = int(y.sum())
SEUIL = 0.45

print("=" * 78)
print("  COMPARAISON DES FAMILLES D'ALGORITHMES")
print("=" * 78)
print("  Jeu : %d lignes, %d caracteristiques | Malveillants : %d"
      % (X.shape[0], X.shape[1], n_mal))
print("  Seuil de decision : %.2f | Validation croisee : %d plis\n"
      % (SEUIL, min(5, n_mal // 2)))

def sc(m):
    """Mise a l'echelle requise pour les modeles sensibles aux distances."""
    return Pipeline([("sc", StandardScaler()), ("clf", m)])

MODELES = {
    "Random Forest":       RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    "Extra Trees":         ExtraTreesClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    "Gradient Boosting":   GradientBoostingClassifier(random_state=42),
    "Arbre de decision":   DecisionTreeClassifier(random_state=42),
    "Regression log.":     sc(LogisticRegression(max_iter=2000, random_state=42)),
    "SVM (RBF)":           sc(SVC(probability=True, random_state=42)),
    "k-NN (k=5)":          sc(KNeighborsClassifier(n_neighbors=5)),
    "Naive Bayes":         sc(GaussianNB()),
}

try:
    from xgboost import XGBClassifier
    MODELES["XGBoost"] = XGBClassifier(n_estimators=200, random_state=42,
                                       eval_metric="logloss", verbosity=0)
except ImportError:
    print("  (XGBoost indisponible)\n")

cv = StratifiedKFold(n_splits=min(5, n_mal // 2), shuffle=True, random_state=42)
res = []

for nom, mod in MODELES.items():
    rec, pre, f1s, auc, tps = [], [], [], [], []
    for itr, ite in cv.split(X, y):
        t0 = time.time()
        try:
            mod.fit(X.iloc[itr], y.iloc[itr])
            pr = mod.predict_proba(X.iloc[ite])[:, 1]
            p = (pr >= SEUIL).astype(int)
            yte = y.iloc[ite]
            rec.append(recall_score(yte, p, zero_division=0))
            pre.append(precision_score(yte, p, zero_division=0))
            f1s.append(f1_score(yte, p, zero_division=0))
            auc.append(roc_auc_score(yte, pr) if len(set(yte)) > 1 else np.nan)
            tps.append(time.time() - t0)
        except Exception as e:
            print("  ! %s : %s" % (nom, str(e)[:50])); break
    if rec:
        res.append({"Modele": nom, "Rappel": np.mean(rec), "Rappel_sd": np.std(rec),
                    "Precision": np.mean(pre), "F1": np.mean(f1s),
                    "AUC": np.nanmean(auc), "Temps_s": np.mean(tps)})

t = pd.DataFrame(res).sort_values("F1", ascending=False)

print("  %-20s %15s %10s %8s %8s %8s" % ("MODELE", "RAPPEL", "PRECISION", "F1", "AUC", "TEMPS"))
print("  " + "-" * 72)
for _, r in t.iterrows():
    print("  %-20s %.3f (+-%.3f) %9.3f %8.3f %8.3f %7.2fs"
          % (r["Modele"], r["Rappel"], r["Rappel_sd"], r["Precision"],
             r["F1"], r["AUC"], r["Temps_s"]))

print("\n" + "=" * 78)
b_f1 = t.iloc[0]; b_r = t.loc[t["Rappel"].idxmax()]; b_a = t.loc[t["AUC"].idxmax()]
print("  Meilleur F1     : %-20s %.3f" % (b_f1["Modele"], b_f1["F1"]))
print("  Meilleur rappel : %-20s %.3f" % (b_r["Modele"], b_r["Rappel"]))
print("  Meilleur AUC    : %-20s %.3f" % (b_a["Modele"], b_a["AUC"]))

rf = t[t["Modele"] == "Random Forest"]
if len(rf):
    rf = rf.iloc[0]
    d = b_f1["F1"] - rf["F1"]
    print("\n  Random Forest (modele retenu) : F1 = %.3f" % rf["F1"])
    if d > 0.001:
        print("  Ecart avec le meilleur (%s) : %+.3f" % (b_f1["Modele"], -d))
        print("  -> A discuter : cet ecart justifie-t-il un changement de modele ?")
    else:
        print("  -> Random Forest est le meilleur choix sur ce jeu.")

out = os.path.expanduser("~/pfe/resultats_modeles.csv")
t.round(4).to_csv(out, index=False)
print("\n  Resultats enregistres : %s" % out)
print("=" * 78)
