# DOCX-RESEARCH-MODEL-TRAINING.md — Entraînement du prototype IA_DOCX

## DOCX MODEL STATUS : RESEARCH / PFA PROTOTYPE

**NOT PRODUCTION READY. KNOWN CIC CORPUS-ARTIFACT RISK. NO EXTERNAL
VALIDATION.** Ce document décrit l'entraînement d'un **prototype de
recherche académique** (`model_docx.pkl`), explicitement autorisé malgré
les limitations documentées du dataset CIC-Trap4Phish 2025 (statut **C.
DOCX CIC DATASET UNSAFE FOR DEFENSIBLE TRAINING**, toujours en vigueur —
voir `validation/DOCX-CIC-INSPECTION.md`, qui reste marqué **⛔ NOT
APPROVED FOR MODEL TRAINING** en tant que source de production). Cette
phase ne contredit pas ce statut : elle documente une **exception
explicitement autorisée par l'utilisateur** pour produire un prototype
PFA, jamais un modèle présenté comme fiable ou prêt pour la production.

## 1. Principe directeur : fidélité entraînement/runtime absolue

Seules les colonnes CIC dont l'équivalence de **méthode** avec
`document_ml/docx/features.py` a été **prouvée par lecture du code source
officiel** (`datasets/docx/cic_reference/Doc_Feature_Extraction.ipynb`,
voir `validation/DOCX-CIC-FEATURE-DEFINITIONS.md`) ont été utilisées.
`dde_present` reste explicitement exclu (contradiction prouvée avec le
code de référence, voir `validation/DOCX-CIC-SEMANTIC-REPAIR.md` §2).
Aucune colonne identifiante (nom de fichier, hash, source) n'est utilisée.

## 2. Nouvelle caractéristique v2 : `xml_text_entropy`

`document_ml/docx/schema.py` passe en `SCHEMA_VERSION = 2` avec l'ajout de
`xml_text_entropy` : reproduction **prouvée**, caractère par caractère, de
la méthode `calculate_entropy()` du notebook officiel (cas OOXML) —
entropie de Shannon sur le texte concaténé de toutes les parties `.xml`
du conteneur. Implémentée dans `features.py` via `_entropie_caracteres()`
(distincte de `_entropie()`, qui reste une entropie sur octets, utilisée
uniquement par `vba_source_entropy`). Testée (`tests/test_docx_features.py`
reste vert après cet ajout — voir aussi §6).

**Caractéristiques CIC délibérément NON reproduites** malgré une
sémantique techniquement prouvée : `ole_object_count`/`ole_object_type_count`
(séparation TOTALE, AUC descriptive 1.0000 — zéro chevauchement entre
classes sur 20 000 échantillons, le cas le plus extrême de tous) et
`vba_keywords_count` (idem, AUC 1.0000, structurellement dérivé de
`macro_present`). Inclure une caractéristique dont la valeur ne
chevauche JAMAIS entre les deux classes reviendrait à entraîner un
identifiant de corpus, pas un classifieur — jugé indéfendable même pour
un prototype de recherche explicitement labellisé comme tel.

## 3. Modèle A (conservateur) vs Modèle B (recherche étendue)

| | Modèle A | Modèle B |
|---|---|---|
| Caractéristiques | `file_size_bytes`, `has_vba_macros` | + `xml_text_entropy` |
| Statut de compatibilité | EXACT (méthode), robuste au risque de format mixte (voir §4) | EXACT + une caractéristique HIGH_RISK (proven mais contaminée par l'ambiguïté de format, voir §4) |
| AUC mono-caractéristique (train) | `file_size_bytes` 0.9937, `has_vba_macros` 1.0000 | + `xml_text_entropy` 0.0002 (≈ non informatif une fois les deux autres présentes) |

**Robustesse au risque de mélange de formats** (rappel : le CSV livré
mélange `.doc/.dot/.docx/.docm/.dotx/.dotm` sans colonne de format, voir
`DOCX-CIC-FEATURE-DEFINITIONS.md` §6) : `file_size` et `macro_present`
sont calculés de façon **identique** dans les deux branches de code du
notebook officiel (OOXML et OLE legacy), donc robustes à cette ambiguïté.
`entropy` en revanche a une définition **différente selon le format**
(texte XML concaténé pour OOXML, source VBA seul pour OLE legacy avec
macro, `0` sans macro) — une contamination possible si une fraction des
lignes d'entraînement sont en réalité des `.doc` legacy. C'est un risque
documenté, pas résolu, du Modèle B.

## 4. Préparation des données

Source : `datasets/docx/Word_All_features.csv` (jamais `Word_Top10_Features.csv`
par jointure de position de ligne — l'inspection précédente a prouvé que
les deux fichiers ne sont pas alignés ligne à ligne).

- **20 000 lignes brutes.** 3 lignes exclues (`file_size=0` ET
  `entropy=0.0` ET `ole_object_count=0`, échec d'extraction probable
  conservé silencieusement dans le dataset d'origine — même critère que
  l'inspection précédente, re-vérifié).
- **19 997 lignes retenues** : 10 000 malveillant / 9 997 sain.
- Groupement par vecteur de caractéristiques RETENU (spécifique à chaque
  modèle) pour garantir qu'aucun doublon ne traverse les splits.

## 5. Split, entraînement, seuil

Split groupé (jamais un doublon de vecteur ne traverse un split),
stratifié par classe au niveau des groupes, **70/15/15**,
`random_state=42` :

| | Modèle A | Modèle B |
|---|---|---|
| Train | 13 115 (malveillant 6 864 / sain 6 251) | 13 877 (7 000 / 6 877) |
| Validation | 3 326 (1 505 / 1 821) | 3 129 (1 500 / 1 629) |
| Test | 3 556 (1 631 / 1 925) | 2 991 (1 500 / 1 491) |

RandomForestClassifier, petite grille (`n_estimators∈{100,300}`,
`max_depth∈{None,8,15}`, `class_weight="balanced"`, `random_state=42`),
sélectionnée sur la **validation uniquement** (F2-score, rappel pondéré
2×). Seuil également choisi sur la validation uniquement (F2-score),
**jamais 0.5 par défaut sans justification** — dans les deux cas le
F2-optimum est atteint à 0.5 (validation déjà quasi parfaitement séparée).

Meilleurs hyperparamètres retenus (les deux modèles) : `n_estimators=100`,
`max_depth=None`.

## 6. Évaluation

**Résultats quasi parfaits sur les deux modèles — validation ET test tenu
à l'écart :** accuracy/précision/rappel/F1/ROC-AUC = 1.0000, 0 faux
positif, 0 faux négatif, pour Modèle A comme Modèle B.

**⚠️ Cette performance quasi parfaite N'EST PAS présentée comme une
preuve de qualité du modèle.** Conformément à l'audit de fuite de la
phase précédente (`DOCX-CIC-SEMANTIC-REPAIR.md` §4), **le risque
d'artefact de construction du corpus CIC reste l'explication la plus
probable** : `has_vba_macros` sépare déjà les classes à AUC 0.9999-1.0000
dans le dataset brut, indépendamment de tout entraînement. Un modèle
entraîné sur une caractéristique qui sépare déjà presque parfaitement les
classes obtiendra necéssairement des métriques quasi parfaites, que le
signal sous-jacent soit généralisable ou non.

### Preuve anti-fuite de doublons

0 vecteur de caractéristiques partagé entre train/validation/test (les
deux modèles) — vérifié deux fois (par construction du split ET par
comparaison directe des valeurs après entraînement).

### Test de permutation des étiquettes (sanité)

Entraînement sur étiquettes mélangées (graine fixe) : ROC-AUC validation
= **0.4865 (Modèle A) / 0.4795 (Modèle B)** — proche du hasard (0.5),
confirmant que le pipeline lui-même n'a PAS de bug de fuite structurel
(le split/l'entraînement/l'évaluation sont corrects) ; la performance
quasi parfaite du modèle réel vient bien du signal des données, pas d'un
défaut de la procédure.

### AUC mono-caractéristique

Modèle A : `file_size_bytes` 0.9937, `has_vba_macros` 1.0000.
Modèle B : idem + `xml_text_entropy` 0.0002.

### Ablation de la caractéristique dominante (`has_vba_macros`)

- **Modèle A sans `has_vba_macros`** (`file_size_bytes` seul) : test —
  accuracy 0.9972, précision 0.9945, rappel 0.9994, F1 0.9969, ROC-AUC
  0.9995, FP=9, FN=1. **`file_size_bytes` seul reste quasi parfaitement
  discriminant** — confirme que ce n'est pas une caractéristique unique
  qui "porte" tout le signal artificiel, mais probablement les deux
  ensemble (cohérent avec l'hypothèse d'artefact de corpus : deux
  populations de documents entièrement différentes, séparables par
  plusieurs axes indépendants).
- **Modèle B sans `has_vba_macros`** (`file_size_bytes` + `xml_text_entropy`) :
  test — toujours accuracy/précision/rappel/F1/ROC-AUC = 1.0000.

## 7. Sélection du prototype

**Modèle A retenu.** Conformément à la priorité de sélection imposée
(fidélité sémantique runtime > absence de raccourci de fuite direct >
comportement runtime bénin > performance) :

1. Les deux modèles atteignent une performance test identique
   (indiscernable) — la performance ne départage donc rien.
2. Modèle A est **robuste à l'ambiguïté de format** du CSV CIC (`file_size`
   et `macro_present` calculés identiquement quel que soit le format dans
   le code de référence), alors que Modèle B ajoute `xml_text_entropy`,
   dont la sémantique n'est prouvée que pour le cas OOXML.
3. Modèle A est plus simple (2 caractéristiques vs 3), donc plus
   interprétable et plus facile à auditer pour un prototype PFA.

**Modèle B n'a PAS été sélectionné automatiquement malgré une performance
égale** — conformément à la consigne explicite de ne jamais choisir le
modèle le plus complexe uniquement parce que ses métriques sont bonnes.

## 8. Artefacts produits

- `model_docx_candidate.pkl` (racine du projet) — bundle intermédiaire,
  conservé pour traçabilité.
- `model_docx.pkl` (racine du projet, même emplacement que `model.pkl`/
  `model_pdf.pkl`) — **promu après validation runtime réussie** (voir
  `validation/DOCX-RUNTIME-VALIDATION.md`). SHA-256 :
  `7ef9f2702af4e7fa28bbf61eb9a88cb08f698ab3e64d7bb6e95c6a3a50f9dde9`
  (identique pour les deux fichiers, la promotion est une copie directe).
- `datasets/docx/cic_prototype_train.py` — script d'entraînement (Modèles
  A et B, split, seuil, évaluation, tests de sanité).
- `datasets/docx/cic_prototype_build_bundle.py` — assemblage du bundle
  final avec métadonnées de transparence.
- `datasets/docx/cic_prototype_results.json` — résultats bruts complets
  (métriques, AUC par caractéristique, ablation) pour les deux modèles.

## 9. Champs de transparence du bundle (jamais à retirer/assouplir)

```
research_only: true
production_ready: false
external_validation: false
known_corpus_artifact_risk: true
```

Plus une liste `known_limitations` explicite dans les métadonnées du
bundle (contamination de format possible, séparation quasi parfaite
probablement liée au corpus, absence de validation externe, `dde_present`
exclu, jamais "production-ready"/"certifié"/un pourcentage de fiabilité).

## 10. Limite connue la plus concrète : documents macro légitimes

Dans le corpus d'entraînement, 9 997/10 000 lignes à `macro_present=0`
sont bénignes et 10 000/10 003 lignes à `macro_present=1` sont
malveillantes. **Le prototype va très probablement classer TOUT document
contenant une macro VBA détectée comme malveillant**, y compris des
documents professionnels légitimes utilisant des macros (modèles de
facture, publipostage, feuilles de calcul intégrées). Ce n'est pas un bug
de ce prototype — c'est directement hérité de la composition du corpus
CIC-Trap4Phish, et une limitation à communiquer explicitement dans tout
usage de ce prototype.
