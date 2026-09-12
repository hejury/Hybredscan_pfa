#!/usr/bin/env python3
"""exp_leakage.py — Mise en evidence d'une fuite de donnees via l'horodatage."""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import recall_score, precision_score, f1_score, roc_auc_score
warnings.filterwarnings("ignore")

df = pd.read_csv(os.path.expanduser("~/pfe/dataset.csv"))
y = df["label"]; n_mal = int(y.sum()); SEUIL = 0.45
cv = StratifiedKFold(n_splits=min(5, n_mal // 2), shuffle=True, random_state=42)

print("=" * 72)
print("  FUITE DE DONNEES : L'HORODATAGE DE COMPILATION")
print("=" * 72)

ts_m = pd.to_datetime(df[df.label == 1].timestamp, unit="s")
ts_b = pd.to_datetime(df[df.label == 0].timestamp, unit="s")
print("\n  Mediane malveillants : %s" % ts_m.median().date())
print("  Mediane sains        : %s" % ts_b.median().date())
print("  Ecart : %d annees" % abs((ts_m.median() - ts_b.median()).days / 365))

# Pouvoir separateur de l'horodatage SEUL
seuil_t = (ts_m.median().timestamp() + ts_b.median().timestamp()) / 2
pred_naif = (df.timestamp > seuil_t).astype(int)
print("\n  Regle naive « compile apres %s => malveillant » :" % pd.to_datetime(seuil_t, unit="s").date())
print("    Rappel %.3f | Precision %.3f | F1 %.3f"
      % (recall_score(y, pred_naif), precision_score(y, pred_naif), f1_score(y, pred_naif)))
print("    -> Une seule colonne, aucun apprentissage.")

def ev(cols):
    X = df[cols]
    pr = np.zeros(len(y))
    for itr, ite in cv.split(X, y):
        m = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        m.fit(X.iloc[itr], y.iloc[itr])
        pr[ite] = m.predict_proba(X.iloc[ite])[:, 1]
    p = (pr >= SEUIL).astype(int)
    return (recall_score(y, p, zero_division=0), precision_score(y, p, zero_division=0),
            f1_score(y, p, zero_division=0), roc_auc_score(y, pr))

feat = [c for c in df.columns if c != "label"]
sans = [c for c in feat if c != "timestamp"]

print("\n" + "=" * 72)
print("  IMPACT DU RETRAIT DE L'HORODATAGE")
print("=" * 72)
print("  %-28s %8s %10s %8s %8s" % ("CONFIGURATION", "RAPPEL", "PRECISION", "F1", "AUC"))
print("  " + "-" * 66)
r1 = ev(feat);  print("  %-28s %8.3f %10.3f %8.3f %8.3f" % ("Avec timestamp (30 car.)", *r1))
r2 = ev(sans);  print("  %-28s %8.3f %10.3f %8.3f %8.3f" % ("Sans timestamp (29 car.)", *r2))
r3 = ev(["timestamp"]); print("  %-28s %8.3f %10.3f %8.3f %8.3f" % ("timestamp SEUL (1 car.)", *r3))

print("\n  Perte de F1 en retirant l'horodatage : %+.3f" % (r2[2] - r1[2]))
print("  F1 obtenu avec l'horodatage seul     : %.3f" % r3[2])

print("\n" + "=" * 72)
print("  INTERPRETATION")
print("=" * 72)
print("""
  Les echantillons malveillants proviennent de MalwareBazaar et sont
  recents par construction. Les fichiers sains proviennent de logiciels
  installes, compiles il y a plusieurs annees.

  Le modele peut donc separer les classes sur la seule date de compilation,
  sans rien apprendre du comportement des fichiers. C'est une fuite de
  donnees : une correlation valable dans le jeu, absente en production.

  En conditions reelles, cette regle echouerait sur :
    - un malware ancien           -> classe « sain »
    - un logiciel legitime recent -> classe « malveillant »

  Decision : l'horodatage est retire du jeu de caracteristiques.
""")
print("=" * 72)
