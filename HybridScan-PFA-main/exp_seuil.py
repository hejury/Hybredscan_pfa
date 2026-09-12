#!/usr/bin/env python3
"""
exp_seuil.py — Optimisation du seuil de decision.
Le seuil 0.5 est un choix par defaut, non un optimum. Cette etude le demontre.
"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (recall_score, precision_score, f1_score,
                             roc_curve, auc, precision_recall_curve, confusion_matrix)
warnings.filterwarnings("ignore")

CSV = os.path.expanduser("~/pfe/dataset.csv")
df = pd.read_csv(CSV)
X, y = df.drop("label", axis=1), df["label"]
n_mal = int(y.sum())

print("=" * 70)
print("  OPTIMISATION DU SEUIL DE DECISION")
print("=" * 70)
print("  Jeu : %d lignes | Sains : %d | Malveillants : %d"
      % (len(df), len(y) - n_mal, n_mal))

k = min(5, n_mal // 2)
cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)

# --- Probabilites hors-echantillon (out-of-fold)
proba = np.zeros(len(y))
for itr, ite in cv.split(X, y):
    m = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    m.fit(X.iloc[itr], y.iloc[itr])
    proba[ite] = m.predict_proba(X.iloc[ite])[:, 1]

fpr, tpr, _ = roc_curve(y, proba)
print("  ROC-AUC (validation croisee) : %.4f\n" % auc(fpr, tpr))

# --- Balayage du seuil
print("  %8s %9s %11s %8s %7s %7s" % ("SEUIL", "RAPPEL", "PRECISION", "F1", "FN", "FP"))
print("  " + "-" * 58)
lignes = []
for s in np.arange(0.05, 0.96, 0.05):
    p = (proba >= s).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, p).ravel()
    r = recall_score(y, p, zero_division=0)
    pr = precision_score(y, p, zero_division=0)
    f = f1_score(y, p, zero_division=0)
    lignes.append({"Seuil": round(s, 2), "Rappel": r, "Precision": pr,
                   "F1": f, "FN": fn, "FP": fp})
    mark = "  <<<" if abs(s - 0.5) < 0.001 else ""
    print("  %8.2f %9.3f %11.3f %8.3f %7d %7d%s" % (s, r, pr, f, fn, fp, mark))

t = pd.DataFrame(lignes)

# --- Trois criteres de choix
print("\n" + "=" * 70)
print("  CHOIX DU SEUIL SELON LE CRITERE RETENU")
print("=" * 70)

s_f1 = t.loc[t["F1"].idxmax()]
print("\n  [A] Maximiser le F1 (compromis equilibre)")
print("      Seuil %.2f -> rappel %.3f | precision %.3f | FN=%d FP=%d"
      % (s_f1["Seuil"], s_f1["Rappel"], s_f1["Precision"], s_f1["FN"], s_f1["FP"]))

# Rappel >= 0.90 avec la meilleure precision possible
cible = t[t["Rappel"] >= 0.90]
if len(cible):
    s_r = cible.loc[cible["Precision"].idxmax()]
    print("\n  [B] Garantir un rappel >= 0.90 (priorite securite)")
    print("      Seuil %.2f -> rappel %.3f | precision %.3f | FN=%d FP=%d"
          % (s_r["Seuil"], s_r["Rappel"], s_r["Precision"], s_r["FN"], s_r["FP"]))
else:
    print("\n  [B] Aucun seuil n'atteint un rappel de 0.90")

# Youden : maximise (sensibilite + specificite - 1)
fpr2, tpr2, thr2 = roc_curve(y, proba)
j = np.argmax(tpr2 - fpr2)
print("\n  [C] Indice de Youden (optimum theorique de la courbe ROC)")
print("      Seuil %.3f -> sensibilite %.3f | specificite %.3f"
      % (thr2[j], tpr2[j], 1 - fpr2[j]))

# --- Comparaison au defaut
d = t[abs(t["Seuil"] - 0.5) < 0.001].iloc[0]
print("\n" + "-" * 70)
print("  COMPARAISON AU SEUIL PAR DEFAUT")
print("  Seuil 0.50 (defaut) : rappel %.3f | precision %.3f | %d malwares manques"
      % (d["Rappel"], d["Precision"], d["FN"]))
print("  Seuil %.2f (F1 max) : rappel %.3f | precision %.3f | %d malwares manques"
      % (s_f1["Seuil"], s_f1["Rappel"], s_f1["Precision"], s_f1["FN"]))
gain = s_f1["Rappel"] - d["Rappel"]
print("  Gain de rappel : %+.3f (%+.1f points)" % (gain, gain * 100))

out = os.path.expanduser("~/pfe/resultats_seuil.csv")
t.round(4).to_csv(out, index=False)
print("\n  Resultats enregistres : %s" % out)
print("=" * 70)
