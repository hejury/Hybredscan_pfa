# DOCX-DATASET-REQUEST.md — Demandes préparées, NON envoyées

**Statut : ces deux messages sont des brouillons, TOUJOURS ACTIFS et NON
ENVOYÉS. Aucun e-mail n'a été envoyé automatiquement — l'envoi est une
action visible par un tiers et reste entièrement à la discrétion de
l'utilisateur.**

**Mise à jour** : une troisième demande, ciblant spécifiquement les
auteurs du dataset CIC-Trap4Phish 2025 (utilisé et rejeté pour
l'entraînement — voir `validation/DOCX-CIC-INSPECTION.md`), a été préparée
séparément dans `validation/DOCX-CIC-CLARIFICATION-REQUEST.md`. Les deux
demandes ci-dessous (Koutsokostas et al. / ALDOCX-SFEM) restent
pertinentes et n'ont pas été remplacées — les trois pistes sont
indépendantes et peuvent être poursuivies en parallèle.

---

## 1. Investigation "features seules" — résultat

Vérifié via l'API Zenodo (métadonnées uniquement, `GET
https://zenodo.org/api/records/4559436` et `.../versions` — aucun
téléchargement de l'archive elle-même) :

- Le dépôt Zenodo `10.5281/zenodo.4559436` ne contient **qu'un seul
  fichier** : `Malicious MS Office documents dataset.zip` (2 813 397 010
  octets, soit ~2,8 Go, MD5 `370a255d61e90819712b2f009b719b5b`).
- **Aucun fichier CSV/Parquet individuellement adressable n'existe dans ce
  dépôt.** Zenodo n'expose pas de "vue interne" d'une archive ZIP — seul
  le fichier tel que déposé par les auteurs est listé par l'API `files`.
- Une seule version du dépôt existe (`conceptrecid 4559435`, une seule
  entrée dans `relations.version`) — pas de version antérieure avec un
  découpage de fichiers différent.
- Recherche de document supplémentaire de la publication associée
  (*Koutsokostas et al., "Invoice #31415 attached: Automated analysis of
  malicious Microsoft Office documents", Computers & Security 114 (2022)
  102582*) : aucune "Supplementary data" distincte (Mendeley Data ou
  fichier ScienceDirect séparé) n'a été trouvée référençant ce jeu de
  données. La page ScienceDirect de l'article est elle-même payante et n'a
  pas pu être inspectée au-delà des métadonnées publiques.
- **Conclusion de cette étape : aucun accès "features seules" public
  n'existe aujourd'hui pour ce dépôt.** La description Zenodo confirme
  elle-même que les caractéristiques extraites (format CSV, d'après le
  texte de la publication) sont empaquetées **avec** les documents Office
  bruts dans la même archive — obtenir le CSV suppose de télécharger
  l'archive contenant des documents malveillants réels, ce qui est exclu
  par les contraintes de ce projet. **Aucun octet de cette archive n'a été
  téléchargé.**

Ce constat motive les deux demandes ci-dessous.

---

## 2. Demande — Koutsokostas et al. (Zenodo 10.5281/zenodo.4559436)

**Contact identifié (source faisant autorité) :**
Constantinos Patsakis, Professeur associé, Département d'Informatique,
Université du Pirée — auteur correspondant probable (dernier auteur,
profil académique public le plus complet parmi les co-auteurs).
- E-mail (page personnelle officielle, <https://kpatsakis.github.io/>) :
  **kpatsak@unipi.gr**
- Autres co-auteurs identifiés (Vasilios Koutsokostas, Nikolaos Lykousas,
  Fran Casino — Université du Pirée ; Gabriele Orazi, Mauro Conti —
  Université de Padoue ; Amrita Ghosal — Université de Limerick) : aucune
  adresse e-mail directe trouvée par recherche publique au-delà de leurs
  affiliations institutionnelles ; M. Patsakis est le point de contact le
  plus fiable actuellement identifié.

**Message proposé (à adapter et envoyer manuellement si approuvé) :**

> Objet : Demande d'accès aux caractéristiques extraites uniquement — dataset Zenodo 10.5281/zenodo.4559436
>
> Bonjour Professeur Patsakis,
>
> Je vous contacte au sujet du jeu de données "Malicious MS Office
> documents dataset" que vous avez publié sur Zenodo
> (DOI : 10.5281/zenodo.4559436), associé à votre article "Invoice #31415
> attached: Automated analysis of malicious Microsoft Office documents"
> (Computers & Security, 2022).
>
> Je travaille sur un projet académique de détection de logiciels
> malveillants (HybridScan, projet de fin d'études) portant spécifiquement
> sur les documents DOCX. Pour des raisons de sécurité, je ne peux pas
> manipuler de documents Office malveillants réels sur ma machine de
> développement — mon environnement n'est pas isolé pour l'analyse de
> malware actif.
>
> L'archive Zenodo actuelle (~2,8 Go) semble contenir à la fois les
> documents Office bruts et les caractéristiques extraites par analyse
> statique. Serait-il possible d'obtenir séparément :
>
> 1. uniquement le(s) fichier(s) CSV/tableau contenant les caractéristiques
>    déjà extraites (sans les documents bruts) ;
> 2. les étiquettes malveillant/bénin associées à chaque ligne ;
> 3. un dictionnaire de données / la définition exacte de chaque
>    caractéristique (méthode de calcul, unité, type) ;
> 4. un indicateur de format de fichier permettant d'isoler les lignes
>    correspondant spécifiquement à des documents .docx (par opposition à
>    .doc/.xls/.ppt/etc.) ?
>
> Pour être clair : je n'ai besoin à aucun moment des documents Office
> malveillants eux-mêmes, uniquement des caractéristiques déjà calculées et
> de leurs étiquettes.
>
> Je vous remercie par avance pour votre temps, et reste à votre
> disposition pour toute précision sur l'usage prévu (recherche académique,
> aucune redistribution).
>
> Cordialement,
> [Nom de l'utilisateur]

---

## 3. Demande — ALDOCX / SFEM (Nissim, Cohen, Rokach, Elovici — BGU)

**Contexte :** ALDOCX (Nissim et al., IEEE TIFS 2017) et SFEM (Cohen &
Nissim, Expert Systems with Applications, 2016) sont les travaux dont la
méthodologie de caractéristiques (structure ZIP/XML des documents OOXML)
est la plus proche de `document_ml/docx/schema.py`. **Aucun jeu de données
public n'a été localisé** pour ces deux publications (ni Zenodo, ni
GitHub, ni IEEE DataPort, ni la page du laboratoire) — ceci n'est pas
supposé, c'est le résultat direct de la recherche menée dans la session
précédente et reconfirmé ici : aucune hypothèse de disponibilité n'est
faite.

**Contact identifié (source faisant autorité) :**
Nir Nissim, Senior Lecturer, Department of Industrial Engineering and
Management, Ben-Gurion University of the Negev — responsable du
"Malware Lab", Cyber Security Research Center (CSRC).
- Page de profil institutionnelle officielle :
  <https://cris.bgu.ac.il/en/persons/nir-nissim/>
- L'adresse e-mail y est affichée sous une forme volontairement obfusquée
  par le portail BGU (protection anti-collecte automatisée) ; **elle n'a
  donc pas été reconstruite ou devinée ici**. Avant tout envoi, récupérer
  l'adresse exacte directement sur cette page officielle (ou via le
  formulaire de contact du CSRC, <https://cyber.bgu.ac.il/labs/>) plutôt
  que de supposer un format (prénom.nom@bgu.ac.il ou équivalent).
- Site "malware-lab.com" (mentionné dans la littérature comme page du
  laboratoire) : inaccessible au moment de cette recherche (404) — ne pas
  utiliser comme source de contact.

**Message proposé (à adapter et envoyer manuellement si approuvé, après
vérification de l'adresse exacte) :**

> Objet : Demande concernant la disponibilité du jeu de données ALDOCX/SFEM (documents DOCX)
>
> Bonjour Docteur Nissim,
>
> Je vous contacte au sujet de vos travaux sur la détection de documents
> Microsoft Office malveillants, en particulier ALDOCX ("Detection of
> Unknown Malicious Microsoft Office Documents Using Designated Active
> Learning Methods Based on New Structural Feature Extraction
> Methodology", IEEE TIFS 2017) et SFEM (Cohen & Nissim, Expert Systems
> with Applications, 2016).
>
> Je développe un projet académique (HybridScan, projet de fin d'études)
> de détection de malware pour les documents .docx, fondé sur des
> caractéristiques structurelles statiques extraites de l'archive
> OOXML (structure ZIP, macros VBA, relations, contenu intégré) — une
> approche méthodologiquement très proche de celle décrite dans ALDOCX/SFEM.
>
> N'ayant trouvé aucune publication ouverte du jeu de données original
> (16 811-16 938 documents .docx mentionnés dans vos articles), je me
> permets de vous demander s'il serait envisageable de partager, à des
> fins de recherche académique :
>
> 1. les caractéristiques structurelles déjà extraites (pas les documents
>    bruts) et leurs étiquettes malveillant/bénin ;
> 2. la définition exacte de chaque caractéristique utilisée.
>
> Je comprends parfaitement si ce jeu de données ne peut pas être partagé
> pour des raisons de confidentialité ou d'accord de collecte des données ;
> je vous remercie déjà pour le temps consacré à la lecture de ce message.
>
> Cordialement,
> [Nom de l'utilisateur]

---

## 4. Rappel

**Aucun de ces deux messages n'a été envoyé.** Aucune adresse e-mail n'a
été validée par un envoi de test. Si l'utilisateur approuve l'envoi, il
devra le faire lui-même (ou demander explicitement à ce qu'il soit envoyé
en son nom), après avoir personnalisé le nom/l'affiliation et vérifié
l'adresse exacte de Nir Nissim sur la page CRIS officielle.
