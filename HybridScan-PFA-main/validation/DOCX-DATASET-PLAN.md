# DOCX-DATASET-PLAN.md — Recherche de dataset DOCX/Office labellisé

**Statut de cette recherche : aucun dataset public identifié ne satisfait
simultanément les trois exigences de ce projet (voir §1). Aucun fichier de
dataset n'a été téléchargé. Aucun malware brut (document, archive ZIP
complète, ou macro VBA source de malware) n'a été récupéré sur cette
machine — seules des pages web publiques et des en-têtes de fichiers CSV
publics (métadonnées/valeurs numériques anonymisées, jamais du contenu
macro) ont été consultés via recherche web et requêtes HTTP `Range`.**

## 1. Exigences

Un dataset candidat doit satisfaire les trois critères suivants pour être
utilisable dans ce projet :

1. **Sans téléchargement de malware brut** : ni documents `.docx`/`.doc`
   malveillants complets, ni archives ZIP OOXML complètes de malware, ni
   même macros VBA texte extraites de malware réel, ne doivent être
   récupérés sur cette machine (contrainte dure du cahier des charges).
2. **Compatibilité de schéma** : les colonnes du dataset doivent pouvoir
   être mises en correspondance de façon prouvée (pas devinée) avec tout ou
   partie des 29 caractéristiques de `document_ml/docx/schema.py` — ou, à
   défaut, motiver une révision de schéma explicite et documentée.
3. **Qualité de labellisation** : classes bénigne/malveillante
   suffisamment représentées et fiables pour un entraînement supervisé
   (leçon du dataset PDF : une classe minoritaire de 1,55 % ou un
   sur-échantillon "UNKNOWN" massif ne permet pas un entraînement
   supervisé direct).

## 2. Constat général : aucun équivalent DOCX du dataset CIC utilisé pour PDF

Le dataset PDF utilisé dans ce projet (`CIC-Evasive-PDFMal2022` /
`PDFMalware2022.parquet`) provient du Canadian Institute for Cybersecurity
(CIC), qui publie des caractéristiques déjà extraites et documentées. **Le
CIC ne publie, à la date de cette recherche, aucun dataset équivalent pour
les documents Office/DOCX** (confirmé par recherche : les datasets CIC
identifiés — CIC-MalMem2022, CIC-AndMal2020, CIC-InvesAndMal2019 — couvrent
la mémoire, Android, et non les documents Office). Il n'existe donc pas de
source "autorité unique" comparable à celle qui a servi de base au pipeline
PDF.

## 3. Candidats évalués

### 3.1 InQuest `microsoft-office-macro-clustering` (GitHub, MIT)

<https://github.com/InQuest/microsoft-office-macro-clustering>

- Fournit `classification.csv` (hash, score VirusTotal, label
  UNKNOWN/BENIGN/MALICIOUS) et deux tables de caractéristiques déjà
  extraites : `features.csv` (~7,6 Mo) et `vba_features.csv`/
  `vba_dataframe.csv` (~46 Mo chacun).
- **Distribution des labels** (documentée dans le README du dépôt) :
  UNKNOWN 8055 (80,55 %), MALICIOUS 1790 (17,90 %), **BENIGN 155
  (1,55 %)**. Exactement le même profil de risque que celui identifié et
  documenté pendant la phase PDF (déséquilibre extrême + majorité non
  labellisée) — insuffisant pour un entraînement supervisé fiable sans
  collecte bénigne massive complémentaire.
- **Incompatibilité de schéma** : les colonnes de `vba_features.csv` sont
  un vocabulaire de comptage de mots-clés VBA (type sac-de-mots — en-tête
  inspecté : `abs, accelerator, activate, activecell, ..., document_open,
  ...` — plusieurs centaines de colonnes anonymes numériques), pas des
  caractéristiques nommées et documentées comme celles de
  `document_ml/docx/schema.py`. Une correspondance existerait uniquement
  pour un sous-ensemble de la famille "Macros/VBA" (§2.2 de
  `DOCX-FEATURES.md`), et resterait approximative (comptages de tokens
  individuels vs compteurs sémantiques agrégés) — **pas une correspondance
  prouvée**, donc non utilisable sans deviner une transformation.
- **Aucune caractéristique structurelle/relations/contenu-intégré** (nos
  familles §2.1, §2.3, §2.4) n'est présente dans ce dataset : il est
  spécifique à l'analyse de macros, pas au document OOXML entier.
- Le dépôt contient également un dossier `macros/` documenté comme
  "*raw VBA macro files, extracted from the document samples*" — **ce
  dossier n'a volontairement pas été consulté ni téléchargé** : il s'agit
  de code source de macros issues d'échantillons malveillants réels, ce
  qui correspond exactement à ce que la contrainte "pas de malware brut"
  de ce projet interdit de récupérer sur cette machine.
- **Conclusion** : source de référence intéressante pour la méthodologie
  (validée la pertinence de nos familles de caractéristiques face à un
  travail de recherche comparable), mais **non retenue comme dataset
  d'entraînement** — ni le schéma ni la qualité de labellisation ne
  conviennent.

### 3.2 DikeDataset (GitHub, `iosifache/DikeDataset`, MIT)

<https://github.com/iosifache/DikeDataset>

- Ne contient **que des hash/labels/métadonnées CSV** ; les dossiers
  `files/benign/` et `files/malware/` sont vides dans le dépôt.
- Les échantillons OLE/Office malveillants doivent être **téléchargés
  séparément depuis MalwareBazaar** — c'est-à-dire exactement le
  téléchargement de malware brut que ce projet interdit. **Disqualifié
  d'office par le critère 1.**
- Même en écartant ce blocage, les échantillons bénins Office ne sont
  qu'environ une centaine, collectés manuellement — volume insuffisant.

### 3.3 ALDOCX (Nissim et al., 2017)

- Méthodologie la plus proche philosophiquement de notre schéma
  (caractéristiques dérivées des chemins internes de l'archive ZIP OOXML
  pour docx/xlsx/pptx — même principe que notre famille "Structure
  générale", §2.1). Publiée avec de bons résultats (VP 93,6 %, FP 0,19 %).
- **Aucun lien de téléchargement du dataset original n'a été trouvé** lors
  de cette recherche ; l'article/travaux ultérieurs ne semblent pas
  accompagnés d'une publication de données ouverte. Non exploitable en
  l'état — à re-vérifier périodiquement, ce n'est pas une impossibilité
  définitive, seulement une indisponibilité constatée à ce jour.

### 3.4 Autres pistes rejetées sans investigation plus poussée

- **MaliciousMacroBot** (`egaus/MaliciousMacroBot`) : ~40 000 échantillons
  macro-activés + ~10 000 bénins mentionnés dans la littérature, mais la
  disponibilité en tant que *caractéristiques déjà extraites* (plutôt que
  fichiers bruts) n'a pas pu être confirmée sans inspection plus profonde ;
  à ré-évaluer si une phase future élargit le budget de recherche.
- Corpus académiques cités par des articles (ex. ~5 millions de documents
  sourcés depuis VirusTotal) : non publiés publiquement, accès nécessitant
  probablement un abonnement VirusTotal Intelligence — hors de portée.

## 4. Conclusion de la recherche dataset

**Aucun dataset public identifié à ce jour ne satisfait simultanément les
trois exigences du §1.** Le blocage n'est pas un manque d'existence de
recherche sur le sujet (plusieurs papiers 2017-2024 traitent exactement de
ce problème), mais un manque de **publication ouverte de caractéristiques
déjà extraites, avec un schéma documenté et des classes équilibrées, sans
nécessiter de télécharger des échantillons Office malveillants bruts**.

Ceci reproduit, en pire, la situation initiale du pipeline PDF : le dataset
PDF finalement utilisé (`PDFMalware2022.parquet`) n'a pas été trouvé par
recherche autonome mais **fourni directement par l'utilisateur** après
vérification. Aucun équivalent DOCX n'a été fourni à ce stade.

## 5. Recommandation

Deux voies, non mutuellement exclusives, pour lever ce blocage dans une
phase future :

1. **Dataset fourni par l'utilisateur** (comme pour PDF) : si un fichier de
   caractéristiques DOCX déjà extraites, labellisé, et documenté est
   disponible côté utilisateur (ou identifié par lui via un accès dont il
   dispose, ex. VirusTotal Intelligence, un laboratoire académique), la
   même chaîne de vérification que pour PDF (lisibilité, schéma, qualité de
   classe, anti-fuite) peut être appliquée telle quelle.
2. **Collecte bénigne autonome + réévaluation** : constituer un corpus de
   fichiers `.docx` **légitimes** réels (aucune contrainte de sécurité ici)
   pour au moins valider la distribution des 29 caractéristiques sur des
   documents sains (cf. `features.py`, déjà capable de les extraire), et
   documenter séparément, sans agir dessus dans cette phase, la question de
   la source malveillante — qui nécessiterait une décision explicite de
   l'utilisateur sur la manière d'obtenir des échantillons malveillants de
   façon sûre (environnement isolé dédié, hors du périmètre de cette
   machine et de cette phase).

**Aucune des deux voies n'est entreprise dans cette phase** — conformément
à la consigne de ne pas deviner/fabriquer un dataset et de s'arrêter pour
rapporter si un dataset sûr n'est pas trouvé.
