# DOCX-CIC-SEMANTIC-REPAIR.md — Réparation sémantique du contrat DOCX

## ⛔ NOT APPROVED FOR MODEL TRAINING — voir `DOCX-CIC-INSPECTION.md`

**Statut : analyse uniquement. Aucun entraînement effectué. Aucune
modification de `document_ml/docx/schema.py`/`features.py` n'a été jugée
sûre à effectuer cette phase — voir §6 pour la justification détaillée de
ce choix (une "réparation" peut légitimement conclure qu'aucun ajout n'est
sûr, ce n'est pas un échec de la phase).**

## 1. Méthode

Tous les diagnostics ci-dessous sont calculés directement sur
`datasets/docx/Word_All_features.csv` (20 000 lignes) à l'aide de
statistiques descriptives simples (tableaux croisés, corrélation de
Pearson, AUC descriptive par rang de Mann-Whitney calculée sans
entraîner aucun modèle). Aucun classifieur n'a été ajusté.

## 2. La contradiction code/données (démonstration quantifiée)

D'après `document_ml/docx/cic_reference` (§3.1 point 5 de
`DOCX-CIC-FEATURE-DEFINITIONS.md`), `dde_present` ne peut être fixé à `1`
que dans une branche de code atteinte **uniquement si** `macro_present`
vaut déjà `1`. Vérification sur les données réelles :

```
                dde_present
macro_present    0      1
0                3   9994
1            10003      0
```

**9 994 lignes sur 20 000 (49,97 %) ont `macro_present=0` ET
`dde_present=1`** — une combinaison structurellement impossible avec le
code du notebook. **Conclusion ferme : le notebook fourni n'est pas (ou
plus) le code exact ayant généré la colonne `dde_present` du CSV livré.**
Ceci retire toute confiance dans le notebook comme preuve définitive pour
`dde_present`, et affaiblit (sans l'annuler) la confiance pour les autres
colonnes dont le mécanisme de génération dans le CSV réel reste également
non entièrement expliqué (`entropy`, `struct_*`, `path_*` — voir §3).

## 3. Investigation de la non-disponibilité à ~50 % alignée sur la classe

`init_feature_row` (le seul mécanisme d'initialisation présent dans le
notebook) met **toutes** les caractéristiques à `0` par défaut — **jamais
à une valeur manquante**. Le motif de 50 % de valeurs manquantes observé
dans `Word_All_features.csv` **ne peut donc pas être expliqué par ce
notebook tel qu'écrit**. Ceci est documenté explicitement plutôt que
masqué : nous ne connaissons pas le mécanisme exact ayant produit les
valeurs manquantes dans le fichier livré. Deux hypothèses non vérifiées
(aucune confirmée, aucune infirmée — aucun document brut inspecté) :

- **Hypothèse A** : le CSV livré résulte de la concaténation de deux lots
  extraits séparément (par exemple un lot par format, ou par lot
  bénin/malveillant), chacun produit par une version du code ne
  renseignant qu'un sous-ensemble de colonnes, la fusion (`pandas.concat`
  ou équivalent) introduisant des `NaN` pour les colonnes absentes d'un
  lot.
- **Hypothèse B** : une version antérieure/différente du notebook
  (non fournie) utilisait un mécanisme d'initialisation différent
  (`NaN` par défaut plutôt que `0`) pour un sous-ensemble de
  caractéristiques selon le format détecté.

| Groupe de colonnes | Taux manquant bénin (label=0) | Taux manquant malveillant (label=1) | Raison dans le code de référence | Absence légitime ou échec ? | Utilisable pour l'entraînement | Motif |
|---|---|---|---|---|---|---|
| ~26 colonnes `path_*` (ex. `path_a-hlink`, `path_w-p`) | 100 % (la plupart) ou 0 % selon la colonne — répartition non uniforme entre les 26 colonnes elles-mêmes (leurs masques de valeurs manquantes ne sont pas tous identiques entre eux) | Inverse de la précédente pour chaque colonne | **Aucune — non reproductible par `init_feature_row`, qui ne produit jamais de NaN** | **Inconnu, non prouvé** — pourrait être une vraie absence structurelle (format sans ces parties ZIP) ou un artefact de pipeline de collecte | **NON** | Mécanisme de génération non prouvé ; corrélation à la classe trop parfaite pour être utilisée sans preuve |
| 4 colonnes `struct_{http://schemas.openxmlformats.org/wordprocessingml/2006/main}*` (`sz`, `themeFill`, `csb1`, `styleId`) | 0 % | 100 % | Idem — non reproductible | Idem | **NON** | Idem ; ces 4 colonnes partagent EXACTEMENT le même masque de valeurs manquantes entre elles (vérifié), suggérant qu'elles proviennent toutes d'une seule et même partie de document (probablement `word/theme/theme1.xml` ou `styles.xml`) — présente ou absente en bloc |

**Conclusion §3** : la non-disponibilité à ~50 % **n'est pas expliquée**
par le code de référence fourni. Conformément à la consigne "ne jamais
convertir NaN en 0 sans preuve que 0 représente une absence légitime",
**ces 30 colonnes restent exclues de tout entraînement**, exactement
comme dans la phase précédente — cette phase ne fait que documenter plus
précisément POURQUOI la preuve manque, elle ne la fournit pas.

## 4. Revue des signaux quasi parfaits

AUC descriptive (sans entraînement de modèle, statistique de rang de
Mann-Whitney, orientée dans le sens le plus favorable) sur les 13 colonnes
complètes (0 % de valeurs manquantes) :

| Caractéristique | AUC descriptive | Séparation zéro/non-zéro | Classification |
|---|---|---|---|
| `ole_object_count` | **1.0000** | Bénin toujours à 0 (10000/10000) ; malveillant toujours ≠0 (10000/10000) | **EXCLUDE** |
| `ole_object_type_count` | **1.0000** | Idem, séparation totale | **EXCLUDE** |
| `vba_keywords_count` | **1.0000** | Bénin 10000/10000 à 0 (1 exception malveillante) ; malveillant 9999/10000 ≠0 | **EXCLUDE** |
| `macro_present` | 0.9999 | 9997/10000 bénins à 0 ; 10000/10000 malveillants à 1 | **HIGH_RISK** |
| `dde_present` | 0.9997 | Voir contradiction §2 — direction contre-intuitive (DDE → bénin) | **EXCLUDE** |
| `entropy` | 0.9996 | Chevauchement partiel mais quasi-total séparation par rang | **EXCLUDE** |
| `struct_ContentType` | 0.9984 | — | **EXCLUDE** (non documentée individuellement + quasi-parfaite) |
| `struct_PartName` | 0.9971 | — | **EXCLUDE** (idem) |
| `file_size` | **0.9941** | Chevauchement en valeur brute (Pearson r=0.09 seulement) mais séparation quasi parfaite en RANG | **HIGH_RISK** |
| `struct_val` | 0.9906 | — | **EXCLUDE** (non documentée) |
| `struct_pos` | 0.9892 | — | **EXCLUDE** (non documentée, needle bruyant "pos") |
| `struct_typeface` | 0.6949 | — | **EXCLUDE** (non documentée ; needle "typeface") |
| `struct_script` | 0.6949 | — | **EXCLUDE** (non documentée ; needle "script") |

**Découverte majeure et inattendue : `file_size` (AUC 0.9941) est PRESQUE
AUSSI SÉPARATEUR que les colonnes déjà suspectées.** La corrélation de
Pearson (0.09, calculée dans la phase précédente) avait masqué cette
séparation car elle est **non linéaire** (quelques valeurs bénignes
extrêmes, ex. 59 592 932 octets, écrasent la corrélation linéaire sans
réduire la séparation par rang). Ceci est la preuve la plus importante de
cette phase : **même la caractéristique jugée la plus "sûre" par
correspondance de méthode exacte (`os.path.getsize`, EXACT au sens
`DOCX-CIC-COMPATIBILITY.md`) s'avère être, dans CE dataset précis,
également un proxy quasi parfait de l'origine de collecte.**

Matrice de corrélation (Pearson) entre les 13 colonnes complètes :
inter-corrélations extrêmement fortes (0.88–0.99 en valeur absolue) entre
`ole_object_count`, `ole_object_type_count`, `macro_present`,
`dde_present`, `vba_keywords_count`, `entropy`, `struct_ContentType`,
`struct_PartName` — ces 8 colonnes ne portent pas 8 signaux indépendants,
mais mesurent très probablement **une seule et même variable latente**
(le plus probable : "quel pipeline de collecte/traitement a produit ce
fichier"), pas 8 propriétés de sécurité distinctes.

### Interprétation

Un taux de séparation de 0.95–1.0 sur la quasi-totalité des colonnes
complètes d'un dataset de 20 000 échantillons réels, mesuré simultanément
sur des colonnes censées mesurer des propriétés de sécurité *a priori*
indépendantes (présence de macro, présence de DDE, entropie, nombre
d'objets OLE, taille de fichier), est le signe caractéristique d'un
**artefact de construction de corpus** (deux populations de documents
structurellement différentes selon leur origine de collecte — cf.
méthodologie du papier : bénins crawlés depuis Google/Wikipedia,
malveillants sourcés depuis MalwareBazaar) plutôt qu'un signal de
comportement malveillant généralisable. Un modèle entraîné sur ces
colonnes apprendrait vraisemblablement à distinguer "ce fichier vient-il
du corpus MalwareBazaar 2025" plutôt que "ce fichier est-il malveillant" —
conformément à l'avertissement explicite de la tâche ("ne pas sélectionner
une caractéristique simplement parce que son AUC est élevé").

## 5. Réparation du contrat runtime — décisions

### 5.1 Mises à jour de confiance sur les correspondances EXISTANTES (aucun changement de code)

| Caractéristique `schema.py` | Statut précédent | Statut révisé | Justification |
|---|---|---|---|
| `file_size_bytes` | EQUIVALENT | **EXACT (méthode)** mais **HIGH_RISK (entraînement)** | Le code confirme `os.path.getsize()`, identique à notre `os.path.getsize(path)` — correspondance de méthode prouvée, pas seulement d'unité. Mais voir §4 : cette colonne est presque aussi séparatrice (par rang) que les colonnes déjà exclues — la correspondance de méthode n'implique pas la sécurité d'entraînement. |
| `has_vba_macros` | EQUIVALENT | **EXACT (méthode)** mais **HIGH_RISK (entraînement)** | Le code confirme `VBA_Parser.detect_vba_macros()`, identique à notre propre appel. Mais §4 : séparation quasi totale (AUC 0.9999) — risque d'artefact de corpus. |
| `has_dde` | EQUIVALENT | **INCOMPATIBLE** | Contradiction quantifiée §2 : le code fourni ne peut pas avoir produit les valeurs réellement observées ; en outre notre `has_dde` utilise `oletools.msodde` sur le document entier, une méthode différente et plus appropriée que la recherche de sous-chaîne "DDE"/"DDEAUTO" dans le seul source VBA imbriquée sous condition de présence de macro. |

### 5.2 Aucune nouvelle caractéristique ajoutée à `schema.py`/`features.py`

Conformément à la consigne "implémenter le plus petit équivalent runtime
correct" **uniquement** pour une caractéristique CIC ayant à la fois (a)
une sémantique prouvée, (b) une extraction statique déterministe, (c) une
reproductibilité runtime sûre, ET (d) **aucune dépendance au corpus** —
**aucune caractéristique de ce dataset ne satisfait le critère (d)**
d'après §4 : les seules colonnes avec une sémantique suffisamment prouvée
pour être candidates (`file_size`, `macro_present`, `vba_keywords_count`,
`ole_object_count`) sont précisément celles qui échouent le critère (d)
(HIGH_RISK ou EXCLUDE). Les colonnes qui pourraient être exemptes de
risque de corpus (`struct_typeface`/`struct_script`, AUC modéré à 0.69)
n'ont pas de définition documentée par les auteurs (§5 de
`DOCX-CIC-FEATURE-DEFINITIONS.md`) et échouent donc le critère (a).

**Aucune ligne de `document_ml/docx/schema.py` ou
`document_ml/docx/features.py` n'a donc été modifiée.**
`SCHEMA_VERSION` reste à `1` — aucun changement de contrat de
caractéristiques, donc aucune raison de l'incrémenter (règle du projet :
incrémenter uniquement quand une caractéristique est ajoutée/retirée pour
une raison documentée ; ici, aucune ne l'est).

Le pipeline PE/PDF n'a naturellement pas été touché (hors du périmètre de
cette tâche de toute façon).
