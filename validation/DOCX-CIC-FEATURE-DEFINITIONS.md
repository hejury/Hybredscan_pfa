# DOCX-CIC-FEATURE-DEFINITIONS.md — Définitions fondées sur le code officiel

**Source faisant autorité : `datasets/docx/cic_reference/Doc_Feature_Extraction.ipynb`
(copie vérifiée bit-à-bit de l'original fourni par l'utilisateur — voir §0).
Notebook inspecté STATIQUEMENT UNIQUEMENT (lecture du JSON/code source) —
jamais exécuté, aucune cellule lancée.**

Ce document remplace/précise `validation/DOCX-CIC-COMPATIBILITY.md` §1 de la
phase précédente, qui reposait sur le texte du papier associé (prose,
potentiellement simplifiée). Le code source réel est une source plus
directe et plus fiable — et, comme détaillé en §4, **contredit
partiellement** le texte du papier sur au moins une caractéristique
(`entropy`).

## 0. Vérification préalable — absence de comportement dangereux

Inspection statique complète du notebook (une seule cellule) :

- **Imports** : `os, re, math, zipfile, warnings, collections.Counter,
  pandas`, plus optionnellement `oletools.olevba.VBA_Parser` et `olefile`
  (tous deux importés dans un bloc `try/except`, jamais requis).
- **Aucun** `subprocess`, `os.system`, `os.popen`, `os.startfile`,
  `win32com`, `comtypes`, `shell=True`, appel PowerShell/cmd/wscript/
  cscript/mshta, ni requête réseau (`requests`/`urllib`/`socket`).
- **Aucune exécution de macro** : `VBA_Parser` est utilisé uniquement pour
  `detect_vba_macros()` et `extract_macros()` — la même bibliothèque
  d'analyse statique que celle déjà utilisée dans
  `document_ml/docx/features.py` de ce projet, jamais un interpréteur VBA.
- La seule ligne potentiellement risquée est l'appel final
  `process_word_folder(input_folder, output_csv)` avec des valeurs
  d'espace réservé littérales (`"Put your input path here"`) — **cette
  cellule n'a pas été exécutée** ; le notebook a été lu uniquement comme
  texte/JSON.
- **Conclusion : sûr à utiliser comme référence sémantique statique.**

## 1. Schéma de caractéristiques déclaré (`FEATURE_ORDER`, 43 entrées)

Le notebook confirme un ordre de colonnes exact, strictement identique à
celui observé dans `Word_All_features.csv` (43 colonnes + `label`), ce qui
confirme que ce notebook est bien la source (ou une reconstruction fidèle
de l'ordre) du fichier livré.

**Portée du notebook (ligne 5 du commentaire d'en-tête) :
`Supports: .docx .docm .dotx .dotm .doc .dot`.**

**Ceci contredit directement la conclusion de la phase précédente**, qui
acceptait "sur la foi du texte du papier" un périmètre `.docx` uniquement.
Le README associé (`datasets/docx/cic_reference/Readme.txt`) confirme
également : *"extracts features from Microsoft Word documents (.doc,
.docx, .docm, .dotm)"*. **Le dataset livré n'a aucune colonne de format
et ne peut donc pas être filtré aux seules lignes `.docx`** (voir §6).

## 2. Utilitaires

- `calculate_entropy(text: str)` — entropie de Shannon **caractère par
  caractère sur une chaîne Python** (`Counter(text)`), PAS une entropie
  octet-par-octet sur des données binaires. Retourne `0.0` si `text` est
  vide.
- `safe_read_zip_entry` — lit une entrée ZIP et la décode en texte avec
  `errors="ignore"` ; retourne `""` en cas d'échec (jamais d'exception
  propagée).
- `init_feature_row` — **initialise LES 43 CARACTÉRISTIQUES À `0` PAR
  DÉFAUT** (`row = {c: 0 for c in ALL_COLUMNS}`), puis tente
  `os.path.getsize(filepath)` pour `file_size` (`0` en cas d'échec).
  **Point capital** : cette fonction ne produit jamais de valeur manquante
  (`NaN`/vide) pour aucune caractéristique — voir §5, ceci est en
  contradiction directe avec le motif de valeurs manquantes réellement
  observé dans `Word_All_features.csv`.

## 3. Deux chemins d'extraction distincts et non équivalents

### 3.1 Cas A — conteneur ZIP (`zipfile.is_zipfile()` vrai : `.docx/.docm/.dotx/.dotm`)

1. **`path_*`** : pour **chaque entrée de l'archive** (`z.namelist()`, TOUTES
   les entrées, pas seulement les `.xml`), le nom d'entrée est mis en
   minuscule puis testé par **correspondance de sous-chaîne brute** contre
   le "needle" (nom de colonne après `path_`, ex. `path_a-hlink` →
   needle `a-hlink`). **Aucun de ces "needles" ne correspond à la syntaxe
   réelle des chemins internes OOXML** (`word/document.xml`,
   `word/theme/theme1.xml`, `word/media/imageN.png`, etc. ne contiennent
   jamais de sous-chaîne comme `a-hlink` ou `w-p`) — voir §7 pour
   l'implication.
2. **`struct_*`** : pour chaque entrée se terminant par `.xml`, le texte
   décodé est concaténé dans `text_all`, puis **pour chaque caractéristique
   `struct_*`, le nombre d'occurrences de la sous-chaîne brute** (needle =
   nom après `struct_`, ex. `struct_ContentType` → needle `ContentType`)
   **est compté dans le texte concaténé via `str.count()`** — un comptage de
   sous-chaîne SANS respect des limites de mot, d'attribut ou d'élément XML.
3. **`entropy`** : entropie de Shannon calculée sur **`text_all`**, c'est-à-dire
   le texte concaténé de TOUTES les parties `.xml` du document — **PAS
   l'entropie du fichier brut entier** (contredit le texte du papier de la
   phase précédente) et **PAS l'entropie du seul source VBA** (contredit
   toute hypothèse d'équivalence avec `vba_source_entropy`).
4. **`ole_object_count`/`ole_object_type_count`** : entrées dont le chemin
   contient `/embeddings/` (sous-chaîne, insensible à la casse) ;
   `ole_object_type_count` = nombre d'extensions de fichier distinctes
   parmi ces entrées.
5. **Macros/DDE** : `VBA_Parser(filepath)` sur le conteneur entier ;
   `macro_present = 1` si `detect_vba_macros()` est vrai. **Seulement si**
   des macros sont détectées, le source VBA est extrait et concaténé
   (`vba_text`), puis :
   - `vba_keywords_count` = nombre d'occurrences (limites de mot, `re.IGNORECASE`)
     de `CreateObject|Shell|AppActivate|Environ|Execute|FileCopy|Dir|Kill|Put|Get|Open`
     dans `vba_text`.
   - `dde_present = int(("DDEAUTO" in vba_text) or ("DDE" in vba_text))`
     — **recherche de sous-chaîne dans le SOURCE VBA UNIQUEMENT, et
     seulement atteignable si `vba_text` est non vide, donc seulement si
     `macro_present` est déjà à 1.** Voir §5 pour la contradiction
     quantifiée avec les données réellement livrées.

### 3.2 Cas B — OLE legacy (`.doc`/`.dot`, PAS un fichier ZIP)

Chemin de code **entièrement différent** :

- `ole_object_count`/`ole_object_type_count` via `olefile` — heuristique
  de dénombrement des flux/stockages OLE dont le nom contient
  `objectpool`/`ole`/`\x01ole`.
- Macros/DDE : même appel `VBA_Parser`, mais **`entropy` est alors
  recalculée sur `vba_text` (source VBA) au lieu du texte XML** — un
  troisième comportement distinct pour la même colonne `entropy` selon le
  format et la présence de macro.
- **`path_*`/`struct_*` ne sont JAMAIS renseignées dans ce chemin de
  code** — elles restent à leur valeur d'initialisation `0`.

**Conséquence directe** : la définition de `entropy` (et la disponibilité
de `path_*`/`struct_*`) **n'est pas une définition unique et cohérente à
travers le dataset** — elle dépend du format réel du fichier ET de la
présence de macros. Un dataset mélangeant `.doc`/`.docx`/etc. sans colonne
de format (§1) rend cette incohérence invisible et non filtrable après
coup.

## 4. Tableau des 10 caractéristiques les plus documentées

| Colonne | Définition exacte (code) | Type | Unité | Comportement en absence | Comportement en échec |
|---|---|---|---|---|---|
| `file_size` | `os.path.getsize(filepath)` | Entier | **Octets, prouvé par le code** | N/A (toujours calculable si le fichier existe) | `0` par défaut si exception — **jamais distingué d'un fichier réellement vide** |
| `entropy` | Entropie de Shannon **caractère par caractère** sur le texte XML concaténé (Cas A) OU sur le source VBA (Cas B, si macro) OU `0` (Cas B, sans macro) | Flottant | Bits/caractère (PAS bits/octet — texte str, pas bytes) | `0.0` si aucun texte | Silencieux (jamais d'erreur explicite) |
| `macro_present` | `VBA_Parser.detect_vba_macros()` | Booléen (0/1) | — | `0` | `0` implicite si `oletools` absent (`HAVE_OLEVBA=False`) — **échec de dépendance = "pas de macro" fabriqué silencieusement** |
| `dde_present` | `"DDEAUTO" in vba_text or "DDE" in vba_text`, **atteignable uniquement si macro_present==1** | Booléen (0/1) | — | `0` si pas de macro (branche jamais atteinte) | Idem |
| `vba_keywords_count` | `len(re.findall(r"\b(CreateObject\|Shell\|AppActivate\|Environ\|Execute\|FileCopy\|Dir\|Kill\|Put\|Get\|Open)\b", vba_text, re.IGNORECASE))` | Entier | Compte de correspondances | `0` si pas de macro | Idem |
| `struct_ContentType` | `text_all.count("ContentType")` (sous-chaîne brute, tout le XML concaténé) | Entier | Compte de sous-chaîne | `0` | `0` par défaut, jamais NaN dans ce code |
| `struct_PartName` | `text_all.count("PartName")` | Entier | Compte de sous-chaîne | `0` | idem |
| `struct_pos` | `text_all.count("pos")` — **sous-chaîne générique, correspond aussi à "position", "compose", "purpose", etc.** | Entier | Compte de sous-chaîne (bruyant) | `0` | idem |
| `ole_object_count` | Cas A : `len([n for n in names if "/embeddings/" in n.lower()])` ; Cas B : heuristique `olefile` | Entier | Compte | `0` | idem |
| `ole_object_type_count` | Extensions distinctes parmi les entrées `/embeddings/` (Cas A) ou heuristique `olefile` (Cas B) | Entier | Compte | `0` | idem |

## 5. Caractéristiques restantes (33 colonnes) — mécanisme générique

Toutes les colonnes `struct_val`, `struct_typeface`, `struct_script`,
`struct_ang`, `struct_dist`, `struct_Extension`, `struct_w`, `struct_name`,
`struct_{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz`,
`...themeFill`, `...csb1`, `...styleId`, et les 26 colonnes `path_*`
suivent le même mécanisme générique (§3.1 points 1–2) :

- `struct_*` = comptage de sous-chaîne brute dans le texte XML concaténé.
  Plusieurs needles sont **dangereusement génériques** :
  `struct_w` (needle `"w"`, une seule lettre — compte essentiellement la
  fréquence du caractère "w" dans tout le XML, pas une caractéristique
  structurelle significative), `struct_val` (needle `"val"`, correspond
  aussi à "value", "eval", "interval"...), `struct_name` (needle `"name"`,
  correspond aussi à "PartName", "typeface"... eux-mêmes déjà comptés
  ailleurs — chevauchement).
- `path_*` = comptage de sous-chaîne brute dans les noms d'entrée ZIP
  (chemins), avec des needles (`a-hlink`, `w-p`, `a-accent3`...) qui **ne
  correspondent à aucune syntaxe de chemin OOXML réelle standard** — un
  chemin interne authentique ne contient jamais littéralement la
  sous-chaîne `"a-hlink"`. Soit ces colonnes seraient structurellement
  toujours à `0` sur un document standard, soit les échantillons
  malveillants (armés par un outil tiers) utilisent des noms de partie
  non standard qui, par coïncidence ou par construction propre à l'outil
  d'armement, contiennent ces sous-chaînes — **aucune des deux hypothèses
  n'est vérifiable sans inspecter les documents bruts, ce qui est exclu**.

**Aucune de ces 33 colonnes n'est documentée individuellement par le
papier** ; le code en donne le mécanisme mais pas de justification
sémantique/sécurité (pourquoi compter "pos" ou "w" serait pertinent pour
la détection de malware n'est expliqué nulle part). Statut : **AMBIGUOUS
à INCOMPATIBLE selon la colonne** — voir `DOCX-CIC-COMPATIBILITY.md`.

## 6. Vérification du périmètre DOCX — conclusion révisée

**Le notebook et le README établissent, sans ambiguïté, que le dataset
livré couvre `.doc`/`.dot`/`.docx`/`.docm`/`.dotx`/`.dotm` mélangés, sans
aucune colonne permettant de séparer les lignes par format.** Ceci
**annule** la conclusion précédente ("périmètre DOCX accepté sur la foi du
papier") — le papier et le code officiel du même projet CIC se
contredisent sur ce point précis, et le code (plus détaillé, plus
vérifiable) l'emporte. Voir §8 de `DOCX-CIC-INSPECTION.md` (mise à jour
requise) et le statut final de `DOCX-CIC-COMPATIBILITY.md`.

## 7. Incohérence code/données — la découverte critique de cette phase

Voir `validation/DOCX-CIC-SEMANTIC-REPAIR.md` §2 pour la démonstration
quantifiée : **le code de `dde_present` exige `macro_present==1` comme
prérequis structurel (imbrication du bloc), mais 9 994 lignes sur 20 000
(49,97 % du dataset entier) ont `macro_present=0` ET `dde_present=1`
simultanément — une combinaison impossible à produire avec ce code tel
qu'écrit.** Ce notebook ne peut donc pas être le code exact ayant produit
`dde_present` dans `Word_All_features.csv` — ni, par extension, une preuve
fiable pour `entropy`/`struct_*`/`path_*`, dont le mécanisme de valeurs
manquantes (§5.1 de `DOCX-CIC-INSPECTION.md`) n'est pas non plus reproduit
par `init_feature_row` (qui ne produit jamais de `NaN`, uniquement des `0`).
