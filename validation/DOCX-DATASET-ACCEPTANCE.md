# DOCX-DATASET-ACCEPTANCE.md — Contrat d'acceptation d'un futur dataset

**Statut : aucun dataset n'a encore été obtenu. Ce document définit à
l'avance ce qui devra être vérifié avant qu'un fichier CSV/Parquet reçu
(par exemple en réponse à `DOCX-DATASET-REQUEST.md`) puisse être utilisé
pour entraîner `model_docx.pkl`. Rien dans ce document ne constitue une
approbation d'un dataset — c'est une checklist à appliquer plus tard,
écrite maintenant pour ne pas improviser les critères une fois des données
réelles en main (leçon directe du pipeline PDF : la fuite `pdf_size` a été
causée par une vérification faite trop tard et de façon incomplète).**

## 1. Exigences obligatoires (bloquantes)

Un dataset candidat est **rejeté** tant que l'un de ces points n'est pas
vérifié positivement :

1. **Lignes DOCX identifiables** : une colonne de format de fichier (ou
   équivalent prouvé) doit permettre d'isoler exactement les lignes
   correspondant à des `.docx` — jamais une pool aveugle avec
   `.doc`/`.xls`/`.xlsm`/`.ppt`. Voir §7 "formats mixtes" ci-dessous.
2. **Étiquette binaire malveillant/bénin** présente et non ambiguë pour
   chaque ligne conservée (pas de label "UNKNOWN" traité comme bénin ou
   ignoré silencieusement — exclu explicitement, jamais imputé).
3. **Définitions de caractéristiques documentées** par la source (data
   dictionary, README, papier associé) — une colonne dont le sens exact ne
   peut pas être établi à partir d'une documentation fournie par les
   auteurs est exclue, jamais devinée à partir du seul nom de colonne.
4. **Aucune caractéristique de raccourci** (chemin de fichier, hash,
   identifiant de dépôt/collection source, nom de fichier, horodatage de
   collecte) n'entre dans l'entraînement — ce sont des fuites triviales
   qui encodent la provenance de la collecte plutôt qu'un signal de
   malveillance réel.
5. **Aucun indicateur d'échec d'extraction** (ex. une colonne
   `parse_error`/`extraction_failed`) n'est utilisé comme caractéristique
   prédictive — un échec de parsing corrèle avec la source de collecte, pas
   avec la malveillance ; l'utiliser reviendrait à réapprendre "d'où vient
   la ligne" plutôt que "le fichier est-il malveillant".
6. **Analyse de corrélation classe/absence de valeur** : pour chaque
   colonne retenue, vérifier si le taux de valeurs manquantes diffère
   significativement entre bénin et malveillant (même procédure que
   `validation/CIC-PDF-ANTI-LEAKAGE.md` pour PDF). Une corrélation forte
   sans explication légitime documentée est traitée comme une fuite
   potentielle, pas ignorée.
7. **Audit des doublons/vecteurs à étiquette conflictuelle** : dédupliquer
   par empreinte de caractéristiques (pas seulement par hash de fichier),
   et exclure tout groupe où des lignes identiques en caractéristiques
   portent des étiquettes différentes — jamais un vote majoritaire
   silencieux (même règle appliquée au dataset PDF, cf.
   `validation/PDF-RUNTIME-FIDELITY.md`).
8. **Comparaison caractéristique-par-caractéristique entraînement/runtime**
   : chaque colonne retenue pour l'entraînement doit être reproduite par
   `document_ml/docx/features.py` avec une méthode de calcul prouvée
   équivalente (même unité, même définition booléen-vs-comptage, même
   traitement de l'absence de macro/relation/embedding). Voir le tableau
   de compatibilité §8.
9. **Unités et sémantique booléen/comptage prouvées**, jamais supposées.
   Toute colonne dont l'unité ne peut pas être confirmée par une source
   faisant autorité (documentation du dataset, code de génération des
   auteurs) est exclue de l'entraînement — pas transformée par une
   conversion non prouvée.
10. **`file_size_bytes` reste exclu** de l'entraînement sauf preuve
    explicite et documentée de l'unité exacte de la colonne équivalente du
    dataset (octets vs Ko vs autre). Rappel direct de la leçon `pdf_size`
    (`document_ml/pdf/cic_schema.py` v3→v4,
    `validation/PDF-RUNTIME-FIDELITY.md`).
11. **Formats Office mixtes jamais poolés silencieusement** : si le
    dataset couvre `.doc`/`.docx`/`.xls`/`.xlsm`/`.ppt` ensemble, un modèle
    entraîné sur l'ensemble mélangé sans distinction de format n'est PAS
    acceptable comme `model_docx.pkl` — soit le sous-ensemble `.docx` est
    isolé et entraîné seul, soit le format est ajouté comme caractéristique
    et documenté comme tel, jamais mélangé en silence en prétendant que le
    modèle résultant est "DOCX".

## 2. Procédure de vérification (dans l'ordre)

1. Lisibilité du fichier (CSV/Parquet), calcul et enregistrement du
   SHA-256, du nombre de lignes/colonnes, des types de colonnes.
2. Isolement des lignes DOCX (exigence §1.1) et recomptage classe par
   classe sur ce sous-ensemble uniquement — les statistiques globales
   toutes-formats-confondues ne sont pas pertinentes pour ce projet.
3. Application du tableau de compatibilité (§8) : chaque colonne du
   dataset est classée EXACT/EQUIVALENT/DERIVABLE/AMBIGUOUS/INCOMPATIBLE/
   MISSING par rapport à `document_ml/docx/schema.py`.
4. Exécution des exigences bloquantes §1.4 à §1.9 (fuite, doublons,
   missingness) — production d'un document
   `validation/DOCX-DATA-QUALITY.md` et `validation/DOCX-ANTI-LEAKAGE.md`
   suivant le même format que les équivalents PDF.
5. Décision explicite : **A. compatible et propre — entraînement
   autorisé**, **B. compatible sous réserve d'exclusions documentées**, ou
   **C. incompatible — dataset rejeté**. Aucune décision "C" n'est
   contournée par une conversion ou une imputation improvisée.

## 3. Tableau de compatibilité — modèle à remplir

**Aucune valeur réelle n'est renseignée ici : aucun dataset n'a encore été
obtenu.** Le tableau liste les 29 caractéristiques actuelles de
`document_ml/docx/schema.py` (`SCHEMA_VERSION = 1`) ; chaque ligne devra
être complétée avec le nom de colonne correspondant du dataset reçu (ou
"MISSING") et un statut, au moment où un dataset réel sera examiné.

Définitions des statuts :
- **EXACT** : même nom sémantique, même méthode de calcul, même unité —
  aucune transformation nécessaire.
- **EQUIVALENT** : méthode de calcul différente mais résultat
  mathématiquement identique (ex. comptage regex vs comptage XML natif
  produisant la même valeur) — équivalence prouvée, pas supposée.
- **DERIVABLE** : peut être recalculé de façon prouvée à partir d'une ou
  plusieurs colonnes du dataset (ex. `has_any_autoexec` dérivable de
  `nb_autoexec_keywords > 0`).
- **AMBIGUOUS** : une correspondance plausible existe mais la sémantique
  exacte (unité, comptage vs booléen, périmètre de recherche) n'est pas
  confirmée par la documentation du dataset — traité comme non entraînable
  tant que l'ambiguïté n'est pas levée.
- **INCOMPATIBLE** : une colonne existe mais mesure quelque chose de
  différent (périmètre, granularité, source) et ne peut pas être
  réconciliée.
- **MISSING** : aucune colonne correspondante dans le dataset.

| # | Caractéristique (`schema.FEATURES`) | Colonne dataset | Statut | Notes |
|---|---|---|---|---|
| 1 | `file_size_bytes` | _(à renseigner)_ | MISSING | Exclusion par défaut tant que l'unité n'est pas prouvée (§1.10) |
| 2 | `zip_entry_count` | | MISSING | |
| 3 | `xml_entry_count` | | MISSING | |
| 4 | `rels_entry_count` | | MISSING | |
| 5 | `has_core_properties` | | MISSING | |
| 6 | `has_app_properties` | | MISSING | |
| 7 | `has_custom_properties` | | MISSING | |
| 8 | `nb_content_types_overrides` | | MISSING | |
| 9 | `has_customxml` | | MISSING | |
| 10 | `has_vba_macros` | | MISSING | |
| 11 | `nb_vba_modules` | | MISSING | |
| 12 | `vba_source_length` | | MISSING | |
| 13 | `nb_autoexec_keywords` | | MISSING | |
| 14 | `has_any_autoexec` | | MISSING | |
| 15 | `nb_relationships_total` | | MISSING | |
| 16 | `nb_relationships_external` | | MISSING | |
| 17 | `nb_hyperlink_relationships` | | MISSING | |
| 18 | `has_attached_template` | | MISSING | |
| 19 | `nb_remote_targets_rels` | | MISSING | |
| 20 | `has_oleobject_relationship` | | MISSING | |
| 21 | `has_embeddings_dir` | | MISSING | |
| 22 | `embedded_entry_count` | | MISSING | |
| 23 | `has_activex` | | MISSING | |
| 24 | `nb_executable_like_embedded_names` | | MISSING | |
| 25 | `nb_suspicious_strings` | | MISSING | |
| 26 | `nb_url_like_strings` | | MISSING | |
| 27 | `has_dde` | | MISSING | |
| 28 | `nb_long_base64_tokens` | | MISSING | |
| 29 | `vba_source_entropy` | | MISSING | |

**Règle de décision à l'issue du remplissage** : l'entraînement n'utilise
que les caractéristiques classées EXACT ou EQUIVALENT (DERIVABLE accepté
seulement si la dérivation est implémentée et testée comme le reste de
`features.py`). AMBIGUOUS/INCOMPATIBLE/MISSING sont exclues de
l'entraînement — jamais imputées ou approximées. Si le nombre de
caractéristiques EXACT/EQUIVALENT/DERIVABLE tombe en dessous d'un seuil
permettant un modèle défendable (à juger au cas par cas, documenté
explicitement, jamais un chiffre arbitraire choisi après coup pour
justifier un résultat), le dataset est classé **C. incompatible** au sens
de la procédure §2.5, même s'il est par ailleurs sûr et bien étiqueté.

## 4. Ce que ce document ne fait pas

Il n'évalue aucun dataset réel (aucun n'est disponible). Il ne remplace
pas `validation/DOCX-DATA-QUALITY.md`/`DOCX-ANTI-LEAKAGE.md`, qui seront
écrits avec de vraies statistiques une fois un dataset obtenu. Il
n'autorise aucun entraînement par lui-même.
