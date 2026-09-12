#!/usr/bin/env python3
"""
exp_taille.py — Influence de la taille du jeu de donnees sur les performances.
Repond a la question : combien d'echantillons faudrait-il ?
"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import recall_score, precision_score, f1_score, roc_auc_score
warnings.filterwarnings("ignore")

CSV = os.path.expanduser("~/pfe/dataset.csv")
df = pd.read_csv(CSV)
n_mal_tot = int(df["label"].sum())
SEUIL = 0.45
N_REP = 10   # repetitions pour lisser l'aleatoire de l'echantillonnage

print("=" * 76)
print("  INFLUENCE DE LA TAILLE DU JEU DE DONNEES")
print("=" * 76)
print("  Malveillants disponibles : %d" % n_mal_tot)
print("  Protocole : sous-echantillonnage progressif, %d repetitions par palier\n" % N_REP)

# Paliers adaptes au nombre disponible
paliers = [p for p in [8, 12, 16, 20, 25, 30, 40, 50, 75, 100, 150, 200] if p <= n_mal_tot]
if n_mal_tot not in paliers:
    paliers.append(n_mal_tot)

mal = df[df["label"] == 1]
sain = df[df["label"] == 0]
RATIO = len(sain) / n_mal_tot   # on conserve le desequilibre reel

print("  %8s %8s %15s %11s %8s %8s" % ("MALW.", "SAINS", "RAPPEL", "PRECISION", "F1", "AUC"))
print("  " + "-" * 66)

lignes = []
for n in paliers:
    n_sain = min(int(n * RATIO), len(sain))
    R, P, F, A = [], [], [], []
    for rep in range(N_REP):
        rs = 42 + rep
        sub = pd.concat([mal.sample(n, random_state=rs),
                         sain.sample(n_sain, random_state=rs)])
        X, y = sub.drop("label", axis=1), sub["label"]
        k = min(5, n // 2)
        if k < 2: continue
        cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=rs)
        pr = np.zeros(len(y))
        for itr, ite in cv.split(X, y):
            m = RandomForestClassifier(n_estimators=200, random_state=rs, n_jobs=-1)
            m.fit(X.iloc[itr], y.iloc[itr])
            pr[ite] = m.predict_proba(X.iloc[ite])[:, 1]
        p = (pr >= SEUIL).astype(int)
        R.append(recall_score(y, p, zero_division=0))
        P.append(precision_score(y, p, zero_division=0))
        F.append(f1_score(y, p, zero_division=0))
        A.append(roc_auc_score(y, pr))
    if R:
        lignes.append({"Malwares": n, "Sains": n_sain,
                       "Rappel": np.mean(R), "Rappel_sd": np.std(R),
                       "Precision": np.mean(P), "F1": np.mean(F), "AUC": np.mean(A)})
        print("  %8d %8d %.3f (+-%.3f) %10.3f %8.3f %8.3f"
              % (n, n_sain, np.mean(R), np.std(R), np.mean(P), np.mean(F), np.mean(A)))

t = pd.DataFrame(lignes)

# --- Graphique ASCII du rappel
print("\n" + "=" * 76)
print("  COURBE D'APPRENTISSAGE — RAPPEL")
print("=" * 76)
LARG = 52
for _, r in t.iterrows():
    b = int(r["Rappel"] * LARG)
    e = int(r["Rappel_sd"] * LARG)
    print("  %4d malw. |%s%s %.3f  +-%.3f"
          % (r["Malwares"], "#" * b, "~" * min(e, LARG - b), r["Rappel"], r["Rappel_sd"]))
print("             +" + "-" * LARG)
print("             0" + " " * (LARG // 2 - 3) + "0.5" + " " * (LARG // 2 - 4) + "1.0")

# --- Analyse de la tendance
print("\n" + "=" * 76)
print("  ANALYSE")
print("=" * 76)
if len(t) >= 2:
    p, d = t.iloc[0], t.iloc[-1]
    print("\n  Du plus petit au plus grand palier (%d -> %d malwares) :"
          % (p["Malwares"], d["Malwares"]))
    print("    Rappel    : %.3f -> %.3f  (%+.3f)" % (p["Rappel"], d["Rappel"], d["Rappel"] - p["Rappel"]))
    print("    Precision : %.3f -> %.3f  (%+.3f)" % (p["Precision"], d["Precision"], d["Precision"] - p["Precision"]))
    print("    Ecart-type: %.3f -> %.3f  (%+.3f)" % (p["Rappel_sd"], d["Rappel_sd"], d["Rappel_sd"] - p["Rappel_sd"]))

    # La courbe a-t-elle atteint un plateau ?
    if len(t) >= 3:
        pente = (t["Rappel"].iloc[-1] - t["Rappel"].iloc[-3]) / (t["Malwares"].iloc[-1] - t["Malwares"].iloc[-3])
        print("\n  Pente sur les 3 derniers paliers : %+.5f rappel / echantillon" % pente)
        if pente > 0.002:
            reste = (0.90 - d["Rappel"]) / pente
            print("  -> La courbe croit encore : le modele n'a pas convergé.")
            if reste > 0:
                print("  -> Extrapolation lineaire : ~%d malwares supplementaires" % int(reste))
                print("     seraient necessaires pour atteindre un rappel de 0.90.")
                print("     (Extrapolation indicative : la courbe sature en pratique.)")
        else:
            print("  -> La courbe plafonne : ajouter des echantillons n'apporte plus grand-chose.")
            print("     Le facteur limitant est ailleurs (caracteristiques, modele).")

print("\n  Lecture : un ecart-type eleve traduit une forte instabilite.")
print("  Avec peu d'echantillons, chaque erreur pese lourd dans la metrique.")

out = os.path.expanduser("~/pfe/resultats_taille.csv")
t.round(4).to_csv(out, index=False)
print("\n  Resultats enregistres : %s" % out)
print("=" * 76)
