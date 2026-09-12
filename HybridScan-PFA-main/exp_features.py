#!/usr/bin/env python3
"""
exp_features.py — Selection de caracteristiques.
Combien des 30 caracteristiques sont reellement utiles ?
"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import recall_score, precision_score, f1_score, roc_auc_score
from sklearn.feature_selection import mutual_info_classif, RFECV
warnings.filterwarnings("ignore")

CSV = os.path.expanduser("~/pfe/dataset.csv")
df = pd.read_csv(CSV)
X, y = df.drop("label", axis=1), df["label"]
n_mal = int(y.sum()); SEUIL = 0.45
k = min(5, n_mal // 2)
cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)

print("=" * 76)
print("  SELECTION DES CARACTERISTIQUES")
print("=" * 76)
print("  Caracteristiques disponibles : %d | Malveillants : %d\n" % (X.shape[1], n_mal))

def evaluer(cols, rs=42):
    """Evaluation en validation croisee sur un sous-ensemble de colonnes."""
    Xs = X[cols]
    pr = np.zeros(len(y))
    for itr, ite in cv.split(Xs, y):
        m = RandomForestClassifier(n_estimators=200, random_state=rs, n_jobs=-1)
        m.fit(Xs.iloc[itr], y.iloc[itr])
        pr[ite] = m.predict_proba(Xs.iloc[ite])[:, 1]
    p = (pr >= SEUIL).astype(int)
    return (recall_score(y, p, zero_division=0), precision_score(y, p, zero_division=0),
            f1_score(y, p, zero_division=0), roc_auc_score(y, pr))

# --- 1. Caracteristiques constantes (aucune information)
const = [c for c in X.columns if X[c].nunique() <= 1]
print("  [1] Caracteristiques constantes : %d" % len(const))
for c in const:
    print("      %s (valeur unique : %s)" % (c, X[c].iloc[0]))
if not const:
    print("      Aucune")

# --- 2. Information mutuelle
mi = mutual_info_classif(X, y, random_state=42)
mi_s = pd.Series(mi, index=X.columns).sort_values(ascending=False)
print("\n  [2] Information mutuelle avec la classe — 12 premieres")
print("      %-26s %8s" % ("CARACTERISTIQUE", "MI"))
print("      " + "-" * 36)
for n, v in mi_s.head(12).items():
    barre = "#" * int(v / max(mi_s.max(), 1e-9) * 22)
    print("      %-26s %7.4f %s" % (n, v, barre))
nulles = (mi_s < 0.001).sum()
print("\n      Caracteristiques a information quasi nulle (< 0.001) : %d" % nulles)

# --- 3. Correlations fortes (redondance)
corr = X.corr().abs()
haut = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
paires = [(c, r, haut.loc[r, c]) for c in haut.columns for r in haut.index
          if pd.notna(haut.loc[r, c]) and haut.loc[r, c] > 0.9]
print("\n  [3] Paires fortement correlees (|r| > 0.9) : %d" % len(paires))
for a, b, v in sorted(paires, key=lambda x: -x[2])[:6]:
    print("      %-22s <-> %-22s r=%.3f" % (a, b, v))
if not paires:
    print("      Aucune")

# --- 4. Performance selon le nombre de caracteristiques
print("\n" + "=" * 76)
print("  PERFORMANCE SELON LE NOMBRE DE CARACTERISTIQUES (par ordre de MI)")
print("=" * 76)
print("  %6s %9s %11s %8s %8s" % ("NB", "RAPPEL", "PRECISION", "F1", "AUC"))
print("  " + "-" * 48)
lignes = []
for n in [3, 5, 8, 10, 15, 20, 25, X.shape[1]]:
    if n > X.shape[1]: continue
    cols = list(mi_s.head(n).index)
    r, p, f, a = evaluer(cols)
    lignes.append({"Nb": n, "Rappel": r, "Precision": p, "F1": f, "AUC": a})
    mark = "  <- complet" if n == X.shape[1] else ""
    print("  %6d %9.3f %11.3f %8.3f %8.3f%s" % (n, r, p, f, a, mark))

t = pd.DataFrame(lignes)
comp = t.iloc[-1]

# --- 5. Le plus petit sous-ensemble sans perte notable
print("\n" + "=" * 76)
print("  ANALYSE")
print("=" * 76)
seuil_perte = 0.02
suff = t[t["F1"] >= comp["F1"] - seuil_perte]
if len(suff):
    m = suff.iloc[0]
    print("\n  Modele complet (%d caracteristiques) : F1 = %.3f" % (comp["Nb"], comp["F1"]))
    print("  Plus petit sous-ensemble a moins de %.0f%% de perte : %d caracteristiques (F1 = %.3f)"
          % (seuil_perte * 100, m["Nb"], m["F1"]))
    if m["Nb"] < comp["Nb"]:
        print("\n  -> %d caracteristiques sur %d suffisent (reduction de %.0f%%)."
              % (m["Nb"], comp["Nb"], (1 - m["Nb"] / comp["Nb"]) * 100))
        print("     Les caracteristiques retenues :")
        for i, c in enumerate(mi_s.head(int(m["Nb"])).index, 1):
            print("       %2d. %s" % (i, c))

# --- 6. RFECV : nombre optimal determine automatiquement
print("\n  [RFECV] Elimination recursive avec validation croisee...")
try:
    sel = RFECV(RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
                step=1, cv=cv, scoring="f1", min_features_to_select=2, n_jobs=-1)
    sel.fit(X, y)
    print("  Nombre optimal retenu par RFECV : %d" % sel.n_features_)
    gardees = list(X.columns[sel.support_])
    print("  Caracteristiques : %s" % ", ".join(gardees[:10]))
    if len(gardees) > 10:
        print("                     ... et %d autres" % (len(gardees) - 10))
except Exception as e:
    print("  RFECV indisponible : %s" % str(e)[:60])

out = os.path.expanduser("~/pfe/resultats_features.csv")
t.round(4).to_csv(out, index=False)
mi_s.round(5).to_csv(os.path.expanduser("~/pfe/resultats_mi.csv"))
print("\n  Resultats enregistres : %s" % out)
print("=" * 76)
