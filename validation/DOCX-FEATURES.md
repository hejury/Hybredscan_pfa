# DOCX-FEATURES.md — Schéma de caractéristiques statiques DOCX

**Statut : `model_docx.pkl` existe — un PROTOTYPE DE RECHERCHE PFA
(`research_only=true`, `production_ready=false`), jamais un modèle de
production. Voir `validation/DOCX-RESEARCH-MODEL-TRAINING.md` et
`validation/DOCX-RUNTIME-VALIDATION.md`. Ce document décrit le schéma de
caractéristiques (`SCHEMA_VERSION = 2`, 30 caractéristiques).**

> **Historique — revue CIC-Trap4Phish 2025** : ce schéma (alors
> `SCHEMA_VERSION = 1`, 29 caractéristiques) a été comparé
> caractéristique par caractéristique au dataset CIC-Trap4Phish 2025
> (code source officiel inspecté). `file_size_bytes` et `has_vba_macros`
> ont une correspondance de MÉTHODE exacte prouvée avec le code officiel
> (`os.path.getsize()`, `VBA_Parser.detect_vba_macros()`). Une
> caractéristique a ensuite été ajoutée (`SCHEMA_VERSION` 1 → 2) :
> `xml_text_entropy`, reproduction prouvée de la méthode `entropy` du
> notebook officiel (cas OOXML) — voir la documentation de la
> caractéristique dans `FEATURE_DOC` ci-dessous et
> `validation/DOCX-RESEARCH-MODEL-TRAINING.md` §2. Les caractéristiques
> les plus discriminantes du dataset CIC (`ole_object_count`,
> `ole_object_type_count`, `vba_keywords_count`, `dde_present`) n'ont
> volontairement PAS été ajoutées au schéma — séparation totale ou quasi
> totale entre classes (AUC descriptive jusqu'à 1.0000), jugée
> caractéristique d'un artefact de corpus plutôt que d'un signal de
> malveillance généralisable, même pour un prototype de recherche — voir
> `validation/DOCX-CIC-COMPATIBILITY.md`, `validation/DOCX-CIC-SAFE-SUBSET.md`
> et `validation/DOCX-CIC-SEMANTIC-REPAIR.md` pour le détail complet.

Portée : fichiers `.docx` (OOXML WordprocessingML) uniquement. Le format
legacy `.doc` (OLE/CFB binaire) n'est **pas** couvert par ce document ni par
`document_ml/docx/`.

Toutes les caractéristiques sont extraites de façon **purement statique** :
métadonnées d'archive ZIP (`zipfile.namelist()`, tailles), texte brut de
parties internes lu en mémoire (jamais interprété comme XML exécutable,
jamais de résolution d'entité externe), et analyse VBA/DDE via `oletools`
(bibliothèques d'analyse statique publiées — décompilation de p-code /
tokenisation de source, jamais un interpréteur VBA). **Aucune macro n'est
jamais exécutée. Aucune relation externe n'est jamais suivie. Aucun processus
n'est jamais lancé** (pas de PowerShell/cmd/wscript/cscript/Office).

Implémentation : [`document_ml/docx/schema.py`](../document_ml/docx/schema.py)
(liste ordonnée + documentation courte) et
[`document_ml/docx/features.py`](../document_ml/docx/features.py) (extraction).
Validation structurelle préalable :
[`document_ml/docx/validate.py`](../document_ml/docx/validate.py).

---

## 1. Contrat général

- `extraire_features_docx(path)` retourne **soit** un dict des 29
  caractéristiques dans l'ordre exact de `schema.FEATURES`, **soit**
  `{"_erreur": "<motif>"}` si le fichier n'est pas un DOCX structurellement
  valide (voir `validate.py`) ou si une étape d'extraction échoue.
- **Aucune valeur n'est jamais fabriquée en cas d'échec.** Une erreur
  `oletools` sur un conteneur pourtant valide (ZIP correct, parties OOXML
  présentes, mais `vbaProject.bin` corrompu par exemple) est *rapportée*
  via `_erreur`, jamais convertie silencieusement en `has_vba_macros = 0`.
  Confirmé par test (voir §8, cas 4).
- Absence réelle d'information (ex. aucune macro présente) produit une
  **valeur réelle** (`0`, `0.0`, chaîne vide → longueur `0`), pas un
  sentinel arbitraire. C'est différent d'un échec d'extraction.

## 2. Familles de caractéristiques

### 2.1 Structure générale (conteneur ZIP / parties OOXML) — 9

| # | Nom | Type | Extraction |
|---|---|---|---|
| 1 | `file_size_bytes` | int | `os.path.getsize(path)`. **ATTENTION** : voir §3 — ne pas entraîner sans confirmation d'unité du dataset choisi. |
| 2 | `zip_entry_count` | int | `len(namelist())` |
| 3 | `xml_entry_count` | int | entrées se terminant par `.xml` |
| 4 | `rels_entry_count` | int | entrées se terminant par `.rels` |
| 5 | `has_core_properties` | bool(0/1) | présence de `docProps/core.xml` |
| 6 | `has_app_properties` | bool(0/1) | présence de `docProps/app.xml` |
| 7 | `has_custom_properties` | bool(0/1) | présence de `docProps/custom.xml` |
| 8 | `nb_content_types_overrides` | int | occurrences de `<Override` dans `[Content_Types].xml` (texte brut, regex) |
| 9 | `has_customxml` | bool(0/1) | une entrée commence par `customXml/` |

### 2.2 Macros / VBA (`oletools.olevba.VBA_Parser`, jamais exécutées) — 5

| # | Nom | Type | Extraction |
|---|---|---|---|
| 10 | `has_vba_macros` | bool(0/1) | `VBA_Parser.detect_vba_macros()` |
| 11 | `nb_vba_modules` | int | nombre de tuples retournés par `extract_macros()` |
| 12 | `vba_source_length` | int | longueur du source VBA concaténé (caractères) ; `0` si aucune macro |
| 13 | `nb_autoexec_keywords` | int (0–4) | occurrences insensibles à la casse de `AutoOpen`/`Document_Open`/`Document_Close`/`AutoClose` dans le source VBA |
| 14 | `has_any_autoexec` | bool(0/1) | `nb_autoexec_keywords > 0` |

`extract_macros()` décompresse et tokenise le p-code VBA stocké dans
`vbaProject.bin` — c'est une opération de **lecture/décompilation statique**
documentée par le format MS-OVBA, strictement équivalente à décompresser un
fichier ZIP : le code n'est à aucun moment envoyé à un interpréteur VBA ou à
Word.

### 2.3 Relations OOXML (texte brut des `*.rels`, jamais suivies) — 6

| # | Nom | Type | Extraction |
|---|---|---|---|
| 15 | `nb_relationships_total` | int | occurrences de `<Relationship` dans toutes les parties `*.rels` concaténées |
| 16 | `nb_relationships_external` | int | occurrences de `TargetMode="External"` |
| 17 | `nb_hyperlink_relationships` | int | relations dont `Type` contient `hyperlink` |
| 18 | `has_attached_template` | bool(0/1) | relation dont `Type` contient `attachedTemplate` (technique connue d'injection de modèle distant) |
| 19 | `nb_remote_targets_rels` | int | valeurs `Target="http(s)://..."` dans les `.rels` |
| 20 | `has_oleobject_relationship` | bool(0/1) | relation dont `Type` contient `oleObject` |

Toutes ces valeurs proviennent d'une **recherche par expression régulière
sur le texte brut** des parties `.rels` (jamais un parseur XML complet,
jamais de résolution d'URL — aucune requête réseau n'est émise).

### 2.4 Contenu intégré (métadonnée d'archive uniquement) — 4

| # | Nom | Type | Extraction |
|---|---|---|---|
| 21 | `has_embeddings_dir` | bool(0/1) | une entrée commence par `word/embeddings/` |
| 22 | `embedded_entry_count` | int | nombre d'entrées sous `word/embeddings/` |
| 23 | `has_activex` | bool(0/1) | une entrée commence par `word/activeX/` |
| 24 | `nb_executable_like_embedded_names` | int | entrées sous `embeddings/`/`activeX/` dont le **nom** se termine par une extension exécutable-like (`.exe/.scr/.bat/.cmd/.vbs/.js/.jar/.ps1/.dll`) — nom de fichier uniquement, le contenu n'est jamais ouvert |

### 2.5 Chaînes suspectes / DDE / obfuscation (source VBA uniquement) — 5

| # | Nom | Type | Extraction |
|---|---|---|---|
| 25 | `nb_suspicious_strings` | int | occurrences (insensible casse) de `powershell`/`cmd.exe`/`wscript`/`cscript`/`mshta`/`rundll32`/`regsvr32`/`certutil`/`bitsadmin`/`shell`/`createobject` **dans le source VBA extrait uniquement** |
| 26 | `nb_url_like_strings` | int | occurrences de `http://`/`https://` dans le source VBA extrait |
| 27 | `has_dde` | bool(0/1) | `oletools.msodde.process_file()` détecte un lien DDE/DDEAUTO |
| 28 | `nb_long_base64_tokens` | int | sous-chaînes contiguës ≥ 40 caractères de l'alphabet base64 dans le source VBA |
| 29 | `vba_source_entropy` | float | entropie de Shannon (bits) du source VBA ; `0.0` si aucune macro (valeur réelle d'une chaîne vide, pas un sentinel) |

**Décision de conception : source VBA uniquement, jamais le corps du
document.** Les caractéristiques 25/26/28/29 sont volontairement bornées au
source VBA extrait (jamais au texte du corps `word/document.xml`) pour
éviter le bruit de faux positifs qu'introduirait un document légitime
contenant des URLs, du texte encodé ou des citations dans sa prose normale.
`nb_remote_targets_rels` (canal `.rels`, §2.3) est délibérément tenu séparé
de `nb_url_like_strings` (canal VBA, §2.5) : ce sont deux canaux distincts
et ne doivent pas être fusionnés — un document peut avoir l'un sans l'autre,
et les combiner masquerait cette distinction utile au modèle.

`msodde.process_file()` est un détecteur statique de texte de champ `DDE`
publié par oletools — il repère la présence du motif dans le XML, il ne
lance jamais Excel/Word et ne résout jamais la commande référencée.

## 3. Caractéristique à risque : `file_size_bytes`

`file_size_bytes` est **exclue de tout entraînement futur tant que l'unité
exacte de la colonne équivalente du dataset choisi n'est pas confirmée par
une source faisant autorité** (documentation officielle du dataset, ou schéma
de génération du dataset). C'est exactement la leçon tirée du défaut
`pdf_size` du pipeline PDF (voir `document_ml/pdf/cic_schema.py`, v3→v4,
et `validation/PDF-RUNTIME-FIDELITY.md`) : une caractéristique de taille de
fichier dont l'unité d'entraînement (octets vs kilo-octets) ne pouvait pas
être prouvée a provoqué un décalage silencieux train/runtime qui a
misclassé des PDF bénins réels. La caractéristique reste **présente dans le
schéma et l'extracteur** (elle est peu coûteuse à extraire et pourrait être
utile une fois l'unité prouvée), mais tout script d'entraînement futur doit
soit (a) obtenir une preuve documentée de l'unité, soit (b) l'exclure du
jeu d'entraînement, exactement comme `pdf_size` l'a été.

## 4. Dépendances et mode d'échec

- `oletools` (`olevba.VBA_Parser`, `msodde`) est une dépendance **dure**
  pour 9 des 29 caractéristiques (10–14, 25–29 sauf DDE qui dépend de
  `msodde` spécifiquement). Si `oletools` n'est pas importable, l'extraction
  entière échoue avec `_erreur` — elle ne bascule jamais silencieusement
  sur une valeur `0`.
- Toute exception levée par `VBA_Parser` (ouverture, détection, ou
  extraction du source) est capturée et convertie en `_erreur` explicite ;
  jamais absorbée en un résultat partiel fabriqué.
- `valider_docx()` (voir `validate.py`) est appelé en tout premier ; un
  fichier structurellement invalide ne déclenche **aucune** tentative
  d'extraction plus poussée (pas d'appel `oletools` sur un ZIP non-OOXML).

## 5. Garantie d'identité entraînement/runtime

Aucun modèle n'existe encore : cette garantie ne peut être vérifiée qu'une
fois un dataset réel importé et un pipeline de génération de features
équivalent construit pour ce dataset (comme cela a été fait pour PDF via
`document_ml/pdf/cic_cleaning.py` + `cic_features.py`). Ce document liste
l'intention ; `DOCX-DATASET-PLAN.md` traite la compatibilité effective une
fois un dataset candidat identifié.

## 6. Tests d'extraction effectués (fondation)

Exécuté via un script de fumée sur des fixtures **synthétiques**, construites
localement avec `zipfile` — aucun échantillon réel ni malware téléchargé :

1. **DOCX minimal sans macro** → toutes les caractéristiques macro/VBA à
   `0`/`0.0`, aucune erreur.
2. **DOCX avec relations externes** (`attachedTemplate` + `hyperlink`
   externes) → `nb_relationships_external=2`, `has_attached_template=1`,
   `nb_hyperlink_relationships=1`, `nb_remote_targets_rels=2`.
3. **DOCX avec `word/embeddings/`, `word/activeX/`, et un nom de fichier
   intégré exécutable-like** → `has_embeddings_dir=1`,
   `embedded_entry_count=2`, `has_activex=1`,
   `nb_executable_like_embedded_names=1`.
4. **`vbaProject.bin` corrompu** (en-tête OLE2 valide mais tronqué) →
   `VBA_Parser` lève une exception à l'ouverture → `{"_erreur": "..."}`
   retourné, **aucune valeur fabriquée**. (Note : des octets purement
   aléatoires sans en-tête OLE2 ne déclenchent PAS d'exception — oletools
   les reconnaît légitimement comme "pas un flux VBA", ce qui est un vrai
   négatif et non une fabrication.)
5. **Fichier texte brut renommé `.docx`** → rejeté dès `validate.py`
   (`"signature ZIP absente"`), `_erreur` retourné sans tentative
   d'extraction.
6. **Logique pure (regex/entropie) validée directement** sur une chaîne VBA
   littérale contenant des mots-clés suspects, une URL, un jeton base64
   long, et un mot-clé d'auto-exécution — confirmée sans dépendre d'un
   flux `vbaProject.bin` réellement décompilable par oletools (voir note
   ci-dessous).

**Limite connue de cette phase de test** : fabriquer un flux `vbaProject.bin`
réel et *positivement* décompilable par `oletools` (contenant un vrai
module VBA avec des mots-clés suspects) nécessiterait de reproduire le
format binaire MS-OVBA (compression + conteneur OLE2/CFB) d'Office — un
travail d'ingénierie hors du périmètre de cette phase de fondation, et qui
n'a pas été fait en récupérant un échantillon externe (aucun téléchargement,
conformément à la contrainte "pas de malware brut"). En conséquence, la
voie de code "détection positive de macro + mots-clés suspects" est validée
**au niveau de la logique pure** (§ cas 6) et **au niveau du branchement
`VBA_Parser`** (cas 1 : chemin sans macro ; cas 4 : chemin d'échec), mais
pas encore par un bout-en-bout complet sur un vrai document macro
malveillant ou bénin. Cela devra être comblé avec de vraies fixtures issues
du dataset retenu (voir `DOCX-DATASET-PLAN.md`) avant tout entraînement.
