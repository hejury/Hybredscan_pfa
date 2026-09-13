# DOCX-CIC-COMPATIBILITY.md — Compatibilité CIC-Trap4Phish vs schema.py

## ⛔ NOT APPROVED FOR MODEL TRAINING

**Voir `validation/DOCX-CIC-INSPECTION.md` en tête de fichier. Ce dataset
est classé RECHERCHE / DIAGNOSTIC UNIQUEMENT (statut final C). Ne pas
entraîner `model_docx.pkl` à partir de ces données.**

**Statut : analyse uniquement, mise à jour après inspection du code source
officiel (`Doc_Feature_Extraction.ipynb`). Aucun entraînement effectué.**
Compare `datasets/docx/Word_All_features.csv` /
`Word_Top10_Features.csv` (CIC-Trap4Phish 2025) à
`document_ml/docx/schema.py` (`SCHEMA_VERSION = 1`, 29 caractéristiques).

**Cette révision remplace les conclusions de la version précédente de ce
document, fondée sur le texte du papier associé, par des conclusions
fondées sur le code source officiel** (`datasets/docx/cic_reference/`,
voir `validation/DOCX-CIC-FEATURE-DEFINITIONS.md` pour l'analyse complète
et `validation/DOCX-CIC-SEMANTIC-REPAIR.md` pour les diagnostics
quantifiés). Deux changements majeurs par rapport à la version précédente :

1. **Le périmètre "DOCX uniquement" est invalidé.** Le notebook officiel et
   son README déclarent explicitement couvrir
   `.doc/.dot/.docx/.docm/.dotx/.dotm` mélangés, sans colonne de format —
   contredisant le texte du papier utilisé précédemment.
2. **`has_dde` rétrogradé d'EQUIVALENT à INCOMPATIBLE** : une contradiction
   quantifiée prouve que le code fourni ne peut pas avoir produit les
   valeurs de `dde_present` réellement présentes dans le CSV (49,97 % des
   lignes ont une combinaison logiquement impossible avec ce code).
3. **`file_size_bytes` et `has_vba_macros` confirmés comme correspondance
   de MÉTHODE exacte** (le code utilise littéralement `os.path.getsize()`
   et `VBA_Parser.detect_vba_macros()`, identiques à notre implémentation)
   — mais tous deux reclassés **HIGH_RISK pour l'entraînement** après
   découverte d'une séparabilité quasi parfaite par rang (AUC descriptive
   0.994–0.9999), signe probable d'un artefact de corpus plutôt que d'un
   signal de malveillance généralisable (voir
   `DOCX-CIC-SEMANTIC-REPAIR.md` §4).

## 1. Tableau de compatibilité complet (29/29 caractéristiques)

| # | `schema.FEATURES` | Colonne dataset la plus proche | Statut | Notes |
|---|---|---|---|---|
| 1 | `file_size_bytes` | `file_size` | **EXACT (méthode)** — voir HIGH_RISK entraînement §3 | Code confirmé : `os.path.getsize(filepath)`, identique à notre implémentation. |
| 2 | `zip_entry_count` | — | **MISSING** | |
| 3 | `xml_entry_count` | — | **MISSING** | |
| 4 | `rels_entry_count` | — | **MISSING** | |
| 5 | `has_core_properties` | — | **MISSING** | |
| 6 | `has_app_properties` | — | **MISSING** | |
| 7 | `has_custom_properties` | — | **MISSING** | |
| 8 | `nb_content_types_overrides` | `struct_ContentType` | **AMBIGUOUS** | Code confirmé : `text_all.count("ContentType")` sur le texte XML concaténé de TOUTES les parties `.xml` — portée bien plus large que notre comptage de `<Override` dans `[Content_Types].xml` seul. Méthodes différentes, non réconciliables sans redéfinition. |
| 9 | `has_customxml` | — | **MISSING** | |
| 10 | `has_vba_macros` | `macro_present` | **EXACT (méthode)** — voir HIGH_RISK entraînement §3 | Code confirmé : `VBA_Parser.detect_vba_macros()`, appel identique à notre implémentation. |
| 11 | `nb_vba_modules` | — | **MISSING** | |
| 12 | `vba_source_length` | — | **MISSING** | |
| 13 | `nb_autoexec_keywords` | — | **MISSING** | `vba_keywords_count` du dataset est un concept différent (voir #25). |
| 14 | `has_any_autoexec` | — | **MISSING** | |
| 15 | `nb_relationships_total` | — | **MISSING** | |
| 16 | `nb_relationships_external` | — | **MISSING** | |
| 17 | `nb_hyperlink_relationships` | `path_a-hlink` | **INCOMPATIBLE** | Code confirmé : comptage de sous-chaîne brute `"a-hlink"` dans les **noms d'entrées ZIP** (chemins), pas dans le contenu XML ni dans les relations `.rels`. Un chemin OOXML standard ne contient jamais cette sous-chaîne — mécanisme fondamentalement différent de notre caractéristique (comptage de relations `.rels` de Type hyperlink). |
| 18 | `has_attached_template` | — | **MISSING** | |
| 19 | `nb_remote_targets_rels` | — | **MISSING** | |
| 20 | `has_oleobject_relationship` | `ole_object_count` (indirect) | **AMBIGUOUS** | Code confirmé : compte les entrées ZIP dont le chemin contient `/embeddings/` — pas une relation `.rels` de Type `oleObject`. Concept apparenté, mécanisme différent. |
| 21 | `has_embeddings_dir` | `ole_object_count` (indirect) | **EQUIVALENT (probable)** | `ole_object_count > 0` devrait, dans la grande majorité des cas réels, coïncider avec la présence du dossier `word/embeddings/` (même logique de recherche de sous-chaîne `/embeddings/`). Non classé EXACT par prudence : le dataset compte le NOMBRE d'entrées, nous ne calculons qu'un booléen ; l'équivalence logique (compte>0 ⟺ booléen vrai) n'a pas été testée sur les données réelles de ce dataset (pas de document brut disponible). |
| 22 | `embedded_entry_count` | `ole_object_count` | **EQUIVALENT (probable)** | Même mécanisme de recherche que notre `embedded_entry_count` (préfixe `word/embeddings/` vs sous-chaîne `/embeddings/` — quasiment toujours équivalent en pratique), mais non vérifié empiriquement sur des fichiers réels de ce dataset. |
| 23 | `has_activex` | — | **MISSING** | |
| 24 | `nb_executable_like_embedded_names` | — | **MISSING** | Le code du dataset ne conserve aucun nom de fichier interne dans le CSV livré. |
| 25 | `nb_suspicious_strings` | `vba_keywords_count` | **INCOMPATIBLE** | Code confirmé : liste de mots-clés `CreateObject\|Shell\|AppActivate\|Environ\|Execute\|FileCopy\|Dir\|Kill\|Put\|Get\|Open` — recoupe seulement 2 mots (`CreateObject`, `Shell`) avec notre liste de 11 mots-clés (`powershell`/`cmd.exe`/`wscript`/`cscript`/`mshta`/`rundll32`/`regsvr32`/`certutil`/`bitsadmin`/`shell`/`createobject`). Vocabulaires différents et non superposables → substitution invalide. |
| 26 | `nb_url_like_strings` | — | **MISSING** | |
| 27 | `has_dde` | `dde_present` | **INCOMPATIBLE** | **Rétrogradé.** Contradiction quantifiée (`DOCX-CIC-SEMANTIC-REPAIR.md` §2) : le code exige `macro_present==1` comme prérequis structurel pour que `dde_present` puisse valoir 1, mais 49,97 % des lignes réelles ont `macro_present=0` ET `dde_present=1` — combinaison impossible avec ce code. Le mécanisme réel de génération de cette colonne dans le CSV livré reste inconnu ; aucune confiance sémantique ne peut lui être accordée. |
| 28 | `nb_long_base64_tokens` | — | **MISSING** | |
| 29 | `vba_source_entropy` | `entropy` | **INCOMPATIBLE** | Code confirmé : entropie de Shannon **caractère par caractère sur le texte XML concaténé de toutes les parties `.xml`** (cas OOXML), ou sur le source VBA uniquement si le fichier est un `.doc`/`.dot` legacy avec macro (cas OLE) — deux définitions différentes selon le format, aucune des deux identique à notre `vba_source_entropy` (VBA seul, toujours, quel que soit le format). |

## 2. Synthèse des statuts (schéma / dataset)

| Statut | Nombre | Caractéristiques |
|---|---|---|
| EXACT (méthode) | 2 | `file_size_bytes`, `has_vba_macros` — **voir §3, tous deux HIGH_RISK pour l'entraînement malgré la méthode exacte** |
| EQUIVALENT (probable, non vérifié empiriquement) | 2 | `has_embeddings_dir`, `embedded_entry_count` |
| AMBIGUOUS | 2 | `nb_content_types_overrides`, `has_oleobject_relationship` |
| INCOMPATIBLE | 4 | `nb_hyperlink_relationships`, `nb_suspicious_strings`, `has_dde`, `vba_source_entropy` |
| MISSING | 19 | tout le reste |

## 3. La correspondance de méthode ne suffit pas — voir l'audit de fuite

Un statut **EXACT (méthode)** signifie que le code de génération du
dataset et notre extracteur runtime calculent, prouvé par lecture directe
du code, **la même grandeur**. Cela ne dit RIEN sur la question séparée
"cette grandeur, DANS CE DATASET, est-elle un signal de malveillance sûr à
apprendre, ou un artefact de la façon dont les échantillons ont été
collectés ?" — cette seconde question est traitée intégralement dans
`validation/DOCX-CIC-SEMANTIC-REPAIR.md` §4, avec le résultat suivant :

- `file_size` : AUC descriptive **0.9941** (quasi-séparation par rang,
  malgré une corrélation de Pearson faible de 0.09 en raison de quelques
  valeurs bénignes extrêmes) → **HIGH_RISK**.
- `macro_present` : AUC descriptive **0.9999** → **HIGH_RISK**.

Aucune des deux n'est classée EXCLUDE au sens strict (contrairement à
`ole_object_count`/`ole_object_type_count`/`vba_keywords_count`/
`dde_present`, séparation totale ou quasi totale et/ou incohérence
prouvée), mais aucune n'est non plus un candidat sûr pour un entraînement
défendable en l'état — voir `validation/DOCX-CIC-SAFE-SUBSET.md` pour la
décision finale.

## 4. Aucune modification de code effectuée

Conformément à `DOCX-CIC-SEMANTIC-REPAIR.md` §5 : aucune caractéristique
de ce dataset ne satisfait simultanément (a) sémantique prouvée, (b)
extraction déterministe, (c) reproductibilité runtime sûre, ET (d) absence
de dépendance au corpus. `document_ml/docx/schema.py` et
`document_ml/docx/features.py` restent donc **inchangés** ;
`SCHEMA_VERSION` reste à `1`.

## 5. Statut final

Voir `validation/DOCX-CIC-SAFE-SUBSET.md` pour le sous-ensemble
d'entraînement candidat (résultat : aucun sous-ensemble défendable
identifié) et le rapport final pour le statut A/B/C définitif de cette
phase.
