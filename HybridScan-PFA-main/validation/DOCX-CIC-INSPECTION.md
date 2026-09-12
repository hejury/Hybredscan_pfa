# DOCX-CIC-INSPECTION.md — Inspection du dataset CIC-Trap4Phish (Word/DOCX)

## ⛔ NOT APPROVED FOR MODEL TRAINING

**Ce dataset (`datasets/docx/Word_All_features.csv`,
`Word_Top10_Features.csv`, `datasets/docx/cic_reference/`) est classé
RECHERCHE / DIAGNOSTIC UNIQUEMENT — PAS UNE SOURCE D'ENTRAÎNEMENT.**
Statut final confirmé : **C. DOCX CIC DATASET UNSAFE FOR DEFENSIBLE
TRAINING** (voir `validation/DOCX-CIC-SAFE-SUBSET.md` §3 : sous-ensemble
d'entraînement défendable vide). Les fichiers sont conservés intacts à des
fins de traçabilité et de future ré-évaluation si une clarification des
auteurs (`validation/DOCX-CIC-CLARIFICATION-REQUEST.md`) lève les
blocages identifiés — **ils ne doivent pas être utilisés pour entraîner
un `model_docx.pkl` DE PRODUCTION, sous quelque forme que ce soit.**

**Exception explicitement autorisée et documentée** : ce dataset a
ensuite été utilisé, sur décision explicite de l'utilisateur, pour
entraîner un **PROTOTYPE DE RECHERCHE PFA** (`research_only=true`,
`production_ready=false`, `known_corpus_artifact_risk=true`) — voir
`validation/DOCX-RESEARCH-MODEL-TRAINING.md`. Ceci ne lève PAS le statut
"NOT APPROVED FOR MODEL TRAINING" ci-dessus au sens production ; c'est une
dérogation ponctuelle et transparente, pas une réévaluation du dataset.

**Statut : inspection uniquement. Aucun entraînement effectué. Aucun
document brut (Source Files) téléchargé ou inspecté — seuls les deux
fichiers CSV de caractéristiques déjà extraites, fournis manuellement par
l'utilisateur, ont été copiés et analysés.**

## 1. Provenance

- **Source** : Canadian Institute for Cybersecurity, dataset
  **CIC-Trap4Phish 2025**, portail officiel
  <https://www.unb.ca/cic/datasets/trap4phish2025.html>.
- **Publication associée** : *"CIC-Trap4Phish: A Unified Multi-Format
  Dataset for Phishing and Quishing Attachment Detection"* (Nejati et al.),
  arXiv:2602.09015.
- **Acquisition** : téléchargés manuellement par l'utilisateur depuis le
  portail officiel vers `C:\Users\user\Downloads\`, puis copiés (jamais
  déplacés/modifiés à la source) dans le dépôt du projet sous
  `datasets/docx/`. Aucun fichier "Source Files"/document brut n'a été
  téléchargé ni inspecté — seuls les deux CSV de caractéristiques.
- **Échantillons sous-jacents (d'après le papier, non vérifiés
  directement)** : bénins collectés par crawl de "sources fiables (Google,
  Wikipedia)" ; malveillants sourcés depuis **MalwareBazaar** (~50 000
  téléchargés par les auteurs, 10 000 retenus). Ce projet n'a jamais
  manipulé ces documents bruts — uniquement les caractéristiques déjà
  calculées par les auteurs.

## 2. Intégrité des fichiers

| Fichier | Taille | SHA-256 |
|---|---|---|
| `C:\Users\user\Downloads\Word_All_features.csv` (original) | 2 646 616 octets | `4137e7324fe53b2a057526bd344bea34de04f2bc735a29545ce1f04370b192af` |
| `datasets/docx/Word_All_features.csv` (copie projet) | identique | `4137e7324fe53b2a057526bd344bea34de04f2bc735a29545ce1f04370b192af` (identique — copie vérifiée bit-à-bit) |
| `C:\Users\user\Downloads\Word_Top10_Features.csv` (original) | 1 197 311 octets | `d7c44bae25ae1cf62a5f1507b5b129d255595bd4cb7b3c6bc65ec541ea4ba96e` |
| `datasets/docx/Word_Top10_Features.csv` (copie projet) | identique | `d7c44bae25ae1cf62a5f1507b5b129d255595bd4cb7b3c6bc65ec541ea4ba96e` (identique) |

Les fichiers originaux dans `Downloads/` n'ont pas été modifiés (lecture
seule utilisée pour la copie et le hachage).

## 3. Schéma brut

### 3.1 `Word_All_features.csv`

- **20 000 lignes × 44 colonnes** (43 caractéristiques + `label`).
- Aucun nom de colonne dupliqué dans l'en-tête brut.
- Tous les types sont numériques (`int64`/`float64`) — **aucune colonne
  `object`**, donc aucune coercition silencieuse de chaîne vers zéro
  n'a eu lieu : pandas aurait laissé la colonne en `object` si une valeur
  non numérique existait.
- **Aucune colonne d'identifiant, de chemin, de hash ou de source n'est
  présente** dans ce fichier — ni `file_name`, ni `path`, ni `hash`, ni
  `source`.
- Colonnes : `ole_object_count`, `ole_object_type_count`, `macro_present`,
  `dde_present`, `vba_keywords_count`, `entropy`, `struct_ContentType`,
  `struct_PartName`, `file_size`, `struct_pos`, `struct_val`,
  `struct_typeface`, `struct_script`, puis **30 colonnes**
  `path_*`/`struct_{namespace}*` (chemins/attributs XML OOXML — voir §5),
  puis `label`.

### 3.2 `Word_Top10_Features.csv`

- **20 000 lignes × 12 colonnes** : `file_name`, les 10 caractéristiques
  documentées par les auteurs (Table IV du papier), et `label`.
- `file_name` : identifiant textuel `benign_NNNNNN` (10 000 valeurs
  uniques) / `malicious_NNNNNN` (10 000 valeurs uniques) — **aucune
  extension, aucun indicateur de format, aucun hash**. Jamais dupliqué,
  jamais manquant.

## 4. Étiquette (label)

- Colonne `label`, valeurs `{0, 1}` uniquement, aucune valeur manquante.
- **Parfaitement équilibré dans les deux fichiers : 10 000 (label=0,
  bénin) / 10 000 (label=1, malveillant)**, cohérent avec le papier
  ("10,000 benign and 10,000 malicious samples").

## 5. Qualité des données

### 5.1 Valeurs manquantes — motif critique

- **13 colonnes sont complètes à 100 %** (aucune valeur manquante, sur les
  20 000 lignes) : `ole_object_count`, `ole_object_type_count`,
  `macro_present`, `dde_present`, `vba_keywords_count`, `entropy`,
  `struct_ContentType`, `struct_PartName`, `file_size`, `struct_pos`,
  `struct_val`, `struct_typeface`, `struct_script`.
- **Les 30 colonnes `path_*`/`struct_{namespace}*` restantes sont
  manquantes à exactement 50 % chacune (10 000/20 000 lignes) — et ce
  taux de 50 % coïncide EXACTEMENT avec la classe** : pour chaque colonne
  de ce groupe, soit elle n'est jamais renseignée pour `label=0` et
  toujours renseignée pour `label=1` (ex. `path_a-hlink`,
  la plupart des colonnes `path_*`), soit l'inverse exact (ex. les 4
  colonnes `struct_{http://schemas.openxmlformats.org/...}*` — `sz`,
  `themeFill`, `csb1`, `styleId` — renseignées uniquement pour `label=0`).
- **Interprétation (constat, pas une supposition sur la malveillance)** :
  les échantillons bénins et malveillants semblent provenir de deux
  chaînes de génération de document structurellement très différentes —
  cohérent avec la méthodologie du papier (bénins = documents crawlés
  "naturels" avec thème/style Word complet ; malveillants = échantillons
  MalwareBazaar, vraisemblablement construits par un outil de
  "weaponization" qui ne produit pas la même richesse de parties
  thème/style, mais insère des chemins DrawingML différents). **Ce n'est
  pas prouvé ici** (aucun document brut inspecté), mais le motif est trop
  parfait (0 %/100 % exact) pour être un simple hasard d'échantillonnage —
  voir le risque de fuite documenté en §6.

### 5.2 Doublons

- **3 395 vecteurs de caractéristiques dupliqués sur 20 000 (17 %)**,
  identiques dans `Word_All_features.csv` (lignes complètes identiques,
  puisqu'il n'y a pas de colonne d'identifiant) et dans
  `Word_Top10_Features.csv` (même compte sur les 10 colonnes de
  caractéristiques, hors `file_name`/`label`).
- **0 groupe à étiquette conflictuelle** : dans aucun des deux fichiers,
  un même vecteur de caractéristiques ne porte deux étiquettes
  différentes — vérifié à la fois sur les 43 colonnes complètes du fichier
  "All" et, séparément, sur le sous-ensemble des 13 colonnes sans valeur
  manquante (le sous-ensemble le plus susceptible d'être utilisé pour un
  entraînement futur).
- Réserve : un taux de duplication de 17 % gonfle artificiellement
  l'importance de certains profils de caractéristiques si un split
  train/test naïf est utilisé plus tard (fuite train/test classique par
  duplication) — à traiter par une déduplication ou un split conscient des
  doublons, exactement comme cela a été fait pour le dataset PDF.

### 5.3 Colonnes constantes / quasi constantes

- Aucune colonne n'a une seule valeur unique sur l'ensemble du dataset.

### 5.4 Lignes suspectes (candidates à l'exclusion)

- **3 lignes** ont simultanément `file_size == 0` **et** `entropy == 0.0`
  **et** `ole_object_count == 0`, toutes étiquetées bénignes (`label=0`).
  Une taille de fichier nulle combinée à une entropie nulle est la
  signature typique d'un **échec d'extraction silencieusement conservé**
  dans le dataset plutôt qu'exclu — pas une caractéristique réelle d'un
  document bénin de 0 octet. Ces 3 lignes doivent être exclues de tout
  entraînement futur (voir `DOCX-DATASET-ACCEPTANCE.md` §1.5, indicateurs
  d'échec d'extraction jamais utilisés comme signal prédictif — ici le cas
  est plus insidieux : il n'y a pas de colonne d'erreur explicite, l'échec
  se manifeste comme une valeur "normale" en apparence).

### 5.5 Valeurs extrêmes (`file_size`)

- Minimum 0 (voir §5.4), maximum **59 592 932 octets (~59 Mo, classe
  bénigne)** contre un maximum de 3 820 032 octets (~3,8 Mo) côté
  malveillant. Plausible pour un document réel avec média intégré
  volumineux, mais à surveiller — un `.docx` de 59 Mo n'est pas
  impossible mais reste un cas extrême à documenter, pas à exclure sans
  justification.

## 6. Audit anti-fuite (résumé — voir DOCX-CIC-COMPATIBILITY.md pour le
lien avec le schéma runtime)

**Constat principal : plusieurs colonnes parmi les mieux documentées
séparent quasi parfaitement les deux classes**, ce qui est le signe soit
d'un signal réellement fort, soit (plus probable, vu l'ampleur) d'un
artefact de collecte (deux pipelines de génération de documents
différents pour bénin/malveillant, plutôt qu'un signal de comportement
malveillant généralisable) :

| Colonne | Corrélation avec `label` | Séparation |
|---|---|---|
| `ole_object_type_count` | 0.9997 | **Totale** : bénin toujours 0, malveillant toujours dans [2,3] |
| `macro_present` | 0.9997 | Quasi totale : 9997/10000 bénins à 0, 10000/10000 malveillants à 1 |
| `dde_present` | −0.9994 | Quasi totale, **et contre-intuitive** : 9994/10000 bénins ont `dde_present=1`, 10000/10000 malveillants ont `dde_present=0` |
| `ole_object_count` | 0.9528 | **Totale** : bénin toujours 0, malveillant toujours ≥ 11 |
| `struct_PartName` | −0.9835 | Forte, chevauchement partiel |
| `struct_ContentType` | −0.9712 | Forte, chevauchement partiel |
| `vba_keywords_count` | 0.9773 | Forte, chevauchement partiel |
| `entropy` | −0.9574 | Forte, chevauchement partiel (bénin ~7.35 en moyenne, malveillant ~5.36) |
| `file_size` | +0.092 | Faible — pas de fuite évidente ici |

Le cas `dde_present` est le plus alarmant : il est **inversé** par rapport
à l'intuition de sécurité (présence de DDE → très majoritairement associée
au label BÉNIN dans ce dataset, alors que DDE est une technique
d'attaque connue). Cela ne prouve pas une erreur d'étiquetage, mais
suggère fortement que les deux classes proviennent de populations de
documents structurellement différentes plutôt que d'un signal de
comportement malveillant en soi — un modèle entraîné directement dessus
risquerait d'apprendre "ce fichier vient-il de MalwareBazaar" plutôt que
"ce fichier est-il malveillant". Ce risque doit être résolu (ou au moins
explicitement mesuré, ex. par une validation croisée par source) avant tout
entraînement — non traité dans cette phase, qui est inspection seule.

## 7. Comparaison All-features vs Top10

- Mêmes 20 000 lignes dans les deux fichiers.
- Les 10 colonnes de caractéristiques de `Word_Top10_Features.csv` sont
  bien un **sous-ensemble exact** des colonnes de même nom dans
  `Word_All_features.csv` — confirmé par comparaison **en tant que
  multi-ensemble** (tri des deux tables sur les 10 colonnes communes +
  label, puis comparaison ligne à ligne après tri : identique).
- **Attention : les deux fichiers ne sont PAS alignés ligne à ligne dans
  leur ordre d'origine** (l'ordre des lignes diffère entre les deux CSV —
  confirmé : la comparaison directe positionnelle, sans tri préalable,
  échoue). Toute jointure entre les deux fichiers doit se faire par
  correspondance de valeurs (ou en supposant que `Word_All_features.csv`
  est un export indépendant sans `file_name`, donc **non joignable de
  façon fiable à `Word_Top10_Features.csv` ligne par ligne** — seule une
  comparaison stochastique/statistique est possible, jamais une
  correspondance certaine ligne-à-ligne).
- Conséquence pratique : `Word_All_features.csv` ne peut pas être relié à
  un identifiant de fichier individuel. Seul `Word_Top10_Features.csv`
  (via `file_name`) offre une forme de traçabilité, mais celle-ci reste
  purement un identifiant séquentiel synthétique (`benign_NNNNNN`), pas un
  identifiant de fichier réel (pas de hash, pas de nom de fichier
  d'origine).

## 8. Vérification du périmètre DOCX (voir §3 de la demande utilisateur)

> **MISE À JOUR (phase suivante, code source officiel inspecté) : la
> conclusion ci-dessous est INVALIDÉE. Le notebook officiel
> `Doc_Feature_Extraction.ipynb` et son `Readme.txt`
> (`datasets/docx/cic_reference/`) déclarent explicitement couvrir
> `.doc/.dot/.docx/.docm/.dotx/.dotm` mélangés, sans colonne de format
> dans le CSV livré. Voir `validation/DOCX-CIC-FEATURE-DEFINITIONS.md` §1
> et §6, et `validation/DOCX-CIC-COMPATIBILITY.md`, qui font foi. La
> section suivante est conservée telle quelle pour l'historique
> (transparence sur ce qui a été conclu à tort à l'époque, et pourquoi),
> mais ne doit plus être utilisée comme référence.**

- **Aucune colonne indicatrice de format** (extension, MIME, dossier
  source) n'existe dans `Word_All_features.csv`. `Word_Top10_Features.csv`
  ne fournit qu'un identifiant `benign_*`/`malicious_*`, sans indication de
  format.
- **Le périmètre DOCX n'est donc pas vérifiable ligne par ligne** à partir
  des CSV seuls.
- **Cependant, le papier associé (arXiv:2602.09015) déclare explicitement
  dans sa méthodologie** : *"The crawled content was saved in .docx format
  to be prepared for feature extraction process"* — aucune mention de
  `.doc` (OLE legacy) n'apparaît dans la description de la collecte Word.
  Ceci constitue une **preuve documentaire de la source (le papier), pas
  une vérification indépendante par ce projet** — nous n'avons pas
  inspecté un seul document brut pour le confirmer nous-mêmes (conforme à
  l'interdiction de télécharger les Source Files). Le périmètre DOCX est
  donc accepté **sur la foi de la documentation des auteurs**, avec cette
  réserve explicitement tracée plutôt que passée sous silence.
- Les colonnes `path_*` (ex. `path_w-p`, `path_a-hlink`) sont, par leur
  syntaxe, cohérentes avec des noms de balises XML OOXML (`w:p`, `a:hlink`)
  — une structure qui n'existe pas dans le format `.doc` binaire (OLE/CFB).
  Ceci **corrobore indirectement** (sans le prouver formellement) la
  déclaration du papier.

## 9. Conclusion de cette inspection

Voir `validation/DOCX-CIC-COMPATIBILITY.md` pour le tableau de
compatibilité complet avec `document_ml/docx/schema.py` et la
recommandation finale.
