# DOCX-CIC-SAFE-SUBSET.md — Sous-ensemble d'entraînement candidat

## ⛔ NOT APPROVED FOR MODEL TRAINING — voir `DOCX-CIC-INSPECTION.md`

**Résultat : aucun sous-ensemble de caractéristiques défendable n'a été
identifié dans ce dataset. Ceci est un résultat scientifique valide, pas
un échec de méthode — voir §3.**

## 1. Critères d'inclusion (rappel du cahier des charges)

Une caractéristique n'est retenue que si **toutes** ces conditions sont
remplies :

1. Sémantique prouvée (pas devinée depuis le nom de colonne).
2. Reproductible au runtime HybridScan.
3. Aucune fuite par raccourci de non-disponibilité alignée sur la classe.
4. Aucune fuite d'identifiant/source.
5. Aucune fuite d'indicateur d'échec d'extraction.
6. Unités/types compatibles.
7. Disponible de façon suffisamment constante pour l'inférence.
8. Signification sur un DOCX arbitraire (pas seulement sur ce corpus).

## 2. Évaluation des 13 colonnes complètes (0 % de valeurs manquantes)

| Colonne dataset | Caractéristique runtime | Statut compatibilité | Type/unité | Taux manquant | AUC mono-caractéristique | Décision | Motif |
|---|---|---|---|---|---|---|---|
| `file_size` | `file_size_bytes` | EXACT (méthode) | Entier, octets | 0 % | **0.9941** | **REJETÉ** | Critère 8 échoué : séparation quasi parfaite par rang malgré une méthode d'extraction identique et prouvée — signe d'artefact de corpus (voir `DOCX-CIC-SEMANTIC-REPAIR.md` §4), pas un signal de taille de fichier généralisable. |
| `macro_present` | `has_vba_macros` | EXACT (méthode) | Booléen | 0 % | **0.9999** | **REJETÉ** | Critère 8 échoué : séparation quasi totale (9997/10000 et 10000/10000) — la présence de macro est réelle et pertinente en général, mais à cette pureté statistique, elle reflète très probablement un critère de sélection du corpus ("malveillant" = échantillons macro par construction) plutôt qu'une distribution réaliste. |
| `dde_present` | `has_dde` | INCOMPATIBLE | Booléen | 0 % | 0.9997 | **REJETÉ** | Critères 1 et 3 échoués : mécanisme de génération prouvé incohérent avec le code de référence (49,97 % de combinaisons impossibles) ; direction du signal contre-intuitive. |
| `ole_object_count` | — (aucun équivalent runtime actuel) | MISSING | Entier | 0 % | **1.0000** | **REJETÉ** | Critères 2 et 8 échoués : pas de caractéristique runtime équivalente aujourd'hui, ET séparation totale (0 chez tous les bénins, ≥11 chez tous les malveillants) — signal trop parfait pour être crédible sur 20 000 échantillons réels. |
| `ole_object_type_count` | — | MISSING | Entier | 0 % | **1.0000** | **REJETÉ** | Idem, séparation totale. |
| `vba_keywords_count` | — (vocabulaire différent de `nb_suspicious_strings`) | INCOMPATIBLE | Entier | 0 % | **1.0000** | **REJETÉ** | Vocabulaire non superposable au nôtre ET séparation quasi totale. |
| `entropy` | — (INCOMPATIBLE avec `vba_source_entropy`) | INCOMPATIBLE | Flottant | 0 % | 0.9996 | **REJETÉ** | Définition incohérente au sein même du dataset (dépend du format/présence de macro, voir `DOCX-CIC-FEATURE-DEFINITIONS.md` §3) ET séparation quasi totale. |
| `struct_ContentType` | `nb_content_types_overrides` (AMBIGUOUS) | AMBIGUOUS | Entier | 0 % | 0.9984 | **REJETÉ** | Méthode non réconciliable avec notre caractéristique ET séparation quasi totale. |
| `struct_PartName` | — | MISSING | Entier | 0 % | 0.9971 | **REJETÉ** | Pas d'équivalent runtime ET séparation quasi totale. |
| `struct_val` | — | MISSING (non documentée) | Entier | 0 % | 0.9906 | **REJETÉ** | Sémantique non prouvée (needle générique "val") ET séparation quasi totale. |
| `struct_pos` | — | MISSING (non documentée) | Entier | 0 % | 0.9892 | **REJETÉ** | Idem (needle générique "pos"). |
| `struct_typeface` | — | MISSING (non documentée) | Entier | 0 % | 0.6949 | **REJETÉ** | Sémantique non prouvée (critère 1) — même si le risque de fuite est ici plus modéré, l'absence de définition documentée est déjà éliminatoire. |
| `struct_script` | — | MISSING (non documentée) | Entier | 0 % | 0.6949 | **REJETÉ** | Idem. |

## 3. Résultat

**0 caractéristique sur 13 satisfait l'ensemble des critères.** Les deux
seules caractéristiques ayant une correspondance de méthode EXACTE et
prouvée avec notre extracteur runtime (`file_size_bytes`, `has_vba_macros`)
échouent toutes deux uniquement sur le critère de généralisabilité
(risque d'artefact de corpus), pas sur la faisabilité technique. Ce n'est
pas un échec de méthodologie de repérage — c'est la conclusion honnête
d'un audit qui a spécifiquement cherché ce type de risque et l'a trouvé de
façon quantifiée et reproductible (AUC descriptive, tableaux croisés,
contradiction code/données).

**Aucun sous-ensemble d'entraînement n'est donc proposé.** Conformément à
la consigne "un sous-ensemble plus petit mais fiable est préférable à un
sous-ensemble plus grand mais fuyant" — ici, le sous-ensemble fiable est
**vide**, ce qui est une réponse valide, pas un contournement à combler
artificiellement (ex. en baissant les critères après coup).

## 4. Diagnostics pré-entraînement (cahier des charges §9)

Demandés sur "le sous-ensemble sûr candidat" — celui-ci étant vide, ces
diagnostics ne peuvent pas être produits de façon significative (aucune
caractéristique à entraîner). Ce qui suit remplace la section demandée par
une explication de pourquoi elle est vide plutôt que par un tableau
arbitrairement rempli :

- **Lignes retenues** : 0 (aucune caractéristique retenue → aucun jeu
  d'entraînement à constituer).
- **Caractéristiques retenues** : 0 / 29.
- **Duplicats/conflits/corrélations** : déjà calculés sur l'ensemble du
  dataset dans `DOCX-CIC-INSPECTION.md` (17 % de doublons de vecteurs, 0
  groupe à étiquette conflictuelle, matrice de corrélation dans
  `DOCX-CIC-SEMANTIC-REPAIR.md` §4) — ces chiffres restent valides comme
  documentation du dataset, mais ne débouchent sur aucun plan
  d'entraînement puisqu'aucune caractéristique n'est retenue.
- **Plan de split futur (train/val/test 70/15/15, groupé par vecteur de
  caractéristiques, `random_state=42`)** : la méthode est documentée et
  prête à être appliquée (même approche group-aware que pour PDF), **mais
  n'a pas de sens à exécuter sur un sous-ensemble de caractéristiques
  vide** — reportée à une phase où un sous-ensemble non vide existera
  (nouveau dataset, ou clarification obtenue auprès des auteurs CIC
  levant le statut AMBIGUOUS/MISSING d'assez de colonnes).

## 5. Ce qui débloquerait une phase future

1. **Clarification des auteurs CIC** (voir `DOCX-DATASET-REQUEST.md`, à
   étendre avec les questions précises de
   `DOCX-CIC-FEATURE-DEFINITIONS.md`) sur le mécanisme exact de génération
   des valeurs manquantes et sur la définition individuelle des colonnes
   `struct_*`/`path_*` non documentées.
2. **Un dataset (ou sous-échantillon) où format ET source de collecte sont
   documentés par ligne**, permettant de vérifier si la séparabilité
   quasi parfaite persiste au sein d'un même sous-groupe homogène
   (par exemple uniquement des `.docx` de MalwareBazaar vs uniquement des
   `.docx` bénins d'une source comparable) — actuellement impossible
   puisque ni le format ni la sous-source ne sont dans le CSV livré.
3. **Extension motivée de `document_ml/docx/schema.py`** avec une famille
   "objets OLE embarqués" si un futur dataset propre montre que ce concept
   reste discriminant hors de tout artefact de corpus.
