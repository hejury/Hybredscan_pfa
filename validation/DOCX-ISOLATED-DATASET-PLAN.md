# DOCX-ISOLATED-DATASET-PLAN.md — Pipeline de dataset de repli (conception uniquement)

**Statut : CONCEPTION UNIQUEMENT. Aucun malware n'a été téléchargé. Aucune
VM n'a été créée. Aucun script d'automatisation n'a été écrit ni exécuté
dans cette phase. Ce document décrit une architecture future, à valider et
approuver explicitement avant toute mise en œuvre.**

## 1. Pourquoi ce plan existe

Le dataset CIC-Trap4Phish 2025 est rejeté pour l'entraînement (statut
**C**, voir `validation/DOCX-CIC-INSPECTION.md`). Aucune source externe
publique ne fournit aujourd'hui de caractéristiques DOCX pré-extraites
sûres (voir `validation/DOCX-DATASET-PLAN.md`,
`validation/DOCX-DATASET-REQUEST.md`,
`validation/DOCX-CIC-CLARIFICATION-REQUEST.md`). Le support ML DOCX
reste **requis**. La seule voie restante, si aucune réponse favorable
n'arrive des demandes de clarification en cours, est de **construire notre
propre dataset** en appliquant NOTRE PROPRE extracteur
(`document_ml/docx/features.py`) à un corpus DOCX labellisé — garantissant
par construction une fidélité entraînement/runtime parfaite (le problème
central qui a fait échouer PDF `pdf_size` et la totalité du dataset CIC
Word ne peut pas se reproduire si l'extracteur d'entraînement EST
l'extracteur de production).

## 2. Architecture cible

```
[Hôte de développement Windows — CET ORDINATEUR]
        │
        │  (1) aucun fichier malveillant brut n'y transite jamais
        ▼
[VM jetable isolée — créée pour cet usage, détruite après]
        │
        │  (2) réception de DOCX bénins ET malveillants déjà labellisés
        │      (provenance documentée, voir §5)
        ▼
[Extraction statique — document_ml/docx/features.py, EXACTEMENT
 la même version que celle utilisée en production, jamais une variante]
        │
        │  (3) AUCUNE macro exécutée, AUCUN document ouvert dans Word/
        │      LibreOffice, AUCUN processus lancé au-delà de l'extraction
        │      statique elle-même (mêmes garanties que le runtime —
        │      voir validation/DOCX-FEATURES.md et les tests de
        │      tests/test_docx_security.py)
        ▼
[Export : UNIQUEMENT caractéristiques (schema.FEATURES) + label
 + un identifiant de groupe non réversible (voir §6) — CSV/Parquet]
        │
        │  (4) SEUL ce fichier de caractéristiques quitte la VM et
        │      revient vers l'hôte de développement — jamais un
        │      document brut, jamais un binaire, jamais une archive ZIP
        │      de documents
        ▼
[Hôte de développement — split train/val/test, entraînement, évaluation]
        │
        ▼
   model_docx.pkl
```

## 3. Garanties de conception (non négociables)

1. **La VM est jetable** : créée pour cette tâche, détruite après export
   des caractéristiques — jamais réutilisée comme environnement de travail
   général, jamais connectée à un stockage partagé avec l'hôte de
   développement au-delà du fichier de caractéristiques final.
2. **Aucun fichier `.doc`/`.docx`/etc. malveillant n'entre jamais sur
   l'hôte de développement Windows** utilisé pour ce projet — ni
   directement, ni via un dossier partagé, ni via un presse-papiers
   partagé VM/hôte.
3. **L'extracteur utilisé pour construire le dataset est identiquement
   celui utilisé en production** (`document_ml/docx/features.py`, même
   version de fichier — idéalement même hash Git/SHA-256 vérifié avant et
   après la campagne d'extraction). Ceci élimine par construction toute
   possibilité de dérive train/runtime — la classe de bug qui a
   nécessité de retirer `pdf_size` du pipeline PDF ne peut pas se
   reproduire si le même code produit les deux.
4. **Rien d'autre que le fichier de caractéristiques ne traverse la
   frontière VM → hôte.** Pas de log contenant des extraits de documents,
   pas de capture d'écran, pas de nom de fichier original.
5. **Aucune automatisation Office/PowerShell/cmd/wscript/cscript n'est
   utilisée pour la préparation des échantillons** — l'extraction reste
   strictement l'appel à `extraire_features_docx()` (ou son équivalent
   batch), jamais une ouverture de document dans une application.

## 4. Ce qui N'EST PAS fait dans cette phase

- Aucune VM n'a été provisionnée.
- Aucun échantillon (bénin ou malveillant) n'a été téléchargé.
- Aucun script d'extraction en lot n'a été écrit (au-delà de
  `document_ml/docx/features.py`, déjà existant et déjà testé —
  `tests/test_docx_features.py`).
- Aucune décision n'a été prise sur l'outil de virtualisation, l'isolation
  réseau exacte, ou la source d'acquisition des échantillons malveillants
  — ce sont des décisions qui nécessitent une approbation explicite et
  séparée avant mise en œuvre, notamment parce qu'elles impliquent de
  manipuler du malware réel (même en environnement isolé), ce qui dépasse
  le périmètre d'une tâche d'assistance de développement automatisée sans
  supervision humaine directe à chaque étape.

## 5. Exigences minimales pour un futur corpus brut

Un corpus de documents `.docx` bruts (bénins + malveillants) n'est
acceptable pour alimenter ce pipeline que s'il satisfait **tous** les
critères suivants :

1. **DOCX spécifiquement, jamais un mélange silencieux de formats Office.**
   Si le corpus contient plusieurs formats, chaque fichier doit être
   accompagné d'une preuve de format vérifiable indépendamment de son
   extension déclarée (ex. validation structurelle réelle via
   `document_ml/docx/validate.py`, qui rejette déjà tout fichier non
   authentiquement OOXML — voir §8.4).
2. **Étiquettes bénin/malveillant présentes et non ambiguës** pour chaque
   fichier, avec la méthode d'attribution du label documentée (scan
   antivirus, signature connue, etc.).
3. **Provenance documentée** pour chaque sous-lot du corpus (d'où vient ce
   fichier, quand, comment) — pas seulement une provenance globale
   agrégée au niveau du dataset entier.
4. **Aucun fichier dupliqué ne doit traverser la frontière
   train/validation/test** — dédoublonnage par empreinte de contenu
   (hash) ET par empreinte de vecteur de caractéristiques (même règle que
   PDF, voir `validation/PDF-RUNTIME-FIDELITY.md`).
5. **Aucun raccourci de répertoire source ou de nom de fichier** ne doit
   être exploitable comme signal (ex. tous les malveillants dans un
   dossier nommé "malicious/", tous les bénins nommés "benign_NNNN") —
   ces informations ne doivent jamais être transformées en
   caractéristique, et idéalement les fichiers devraient être renommés/
   mélangés avant extraction pour qu'aucun script d'extraction ne puisse
   même accidentellement lire le nom comme indice.
6. **Échantillons suffisamment DIVERS, provenant de PLUSIEURS sources de
   collecte indépendantes** — la leçon centrale de cette phase CIC est
   qu'un corpus bénin d'une seule origine (crawl web) contre un corpus
   malveillant d'une seule autre origine (un seul dépôt de malware)
   produit un classifieur de provenance, pas un classifieur de
   malveillance. **Aucune source d'acquisition unique ne doit correspondre
   directement à une seule classe** — chaque classe doit elle-même
   mélanger plusieurs origines quand c'est possible (ex. bénins : documents
   d'entreprise réels + documents gouvernementaux + documents générés par
   des utilisateurs volontaires ; malveillants : plusieurs familles/
   campagnes/dépôts distincts).
7. **La source de collecte doit être auditable** — conservée comme
   métadonnée de traçabilité (jamais comme caractéristique
   d'entraînement, voir §6) pour permettre un audit de fuite par
   sous-groupe, exactement le contrôle qui a manqué pour CIC-Trap4Phish
   (voir `validation/DOCX-CIC-SEMANTIC-REPAIR.md` §4).
8. **Les échecs d'extraction ne doivent jamais devenir une caractéristique
   prédictive**, ni explicitement (colonne "extraction_failed") ni
   implicitement (une valeur sentinelle comme `file_size=0` combinée à
   `entropy=0.0` conservée sans exclusion — le défaut précis découvert
   dans le CSV CIC, voir `validation/DOCX-CIC-INSPECTION.md` §5.4).

**La diversité prime sur le volume.** Ce projet ne prétend PAS qu'un
volume de 20 000 échantillons (comme CIC-Trap4Phish) est nécessaire ou
même souhaitable — un corpus plus petit (quelques centaines à quelques
milliers d'échantillons) mais réellement diversifié en sources, et
propre au sens des 8 critères ci-dessus, est préférable et plus
défendable qu'un grand corpus mono-source comme celui rejeté cette phase.

## 6. Contrat de caractéristiques pour un futur entraînement

Le futur `model_docx.pkl` ne doit être entraîné que sur des
caractéristiques produites par `document_ml/docx/features.py` (ou une
version strictement versionnée avec une sémantique runtime identique,
vérifiée par les mêmes tests que `tests/test_docx_features.py`). **Aucune
caractéristique disponible uniquement au moment de l'entraînement n'est
autorisée** — si une information n'est pas calculable par
`extraire_features_docx()` sur un DOCX arbitraire au moment de
l'inférence, elle ne doit jamais entrer dans l'entraînement.

Interdits explicitement, sans exception :

- nom de fichier ;
- chemin complet ;
- hash (SHA-256 ou autre) ;
- source de l'échantillon (dépôt, campagne, lot) ;
- dossier/répertoire de collecte ;
- identifiant de dataset ;
- indicateur `extraction_failed` ;
- indicateur de valeur manquante (missingness indicator) — un échec
  d'extraction doit conduire à l'EXCLUSION de la ligne, jamais à une
  caractéristique binaire "cette valeur était-elle manquante".

L'identifiant de groupe mentionné en §2 (étape 4, "identifiant de groupe
non réversible") sert **uniquement** à garantir qu'aucun doublon ne
traverse les splits train/validation/test (voir §7) — ce n'est jamais une
colonne d'entraînement, et il doit être conçu pour ne permettre aucune
reconstruction du fichier ou de la source d'origine (ex. un hash du
VECTEUR DE CARACTÉRISTIQUES lui-même, pas un hash du fichier).

## 7. Split futur (conception, non exécuté)

Même méthode que PDF (`validation/PDF-DATASET-PLAN.md`) et le contrat déjà
posé dans `validation/DOCX-DATASET-ACCEPTANCE.md` :

- Split conscient des groupes (`group-aware`) : deux lignes au vecteur de
  caractéristiques identique ne doivent jamais se retrouver de part et
  d'autre d'un split.
- Cible approximative : 70 % train / 15 % validation / 15 % test.
- `random_state = 42`.
- Seuil de décision choisi UNIQUEMENT sur la validation, jamais sur le
  test (même règle que PE et PDF).
- Test tenu à l'écart, touché une seule fois.

## 8. Rappels de sécurité (repris du cahier des charges d'origine, toujours en vigueur)

1. Jamais d'ouverture de document dans Microsoft Word ou LibreOffice.
2. Jamais d'exécution de macro.
3. Jamais de suivi de relation externe.
4. Jamais de lancement de PowerShell/cmd/wscript/cscript/Office depuis ce
   projet.
5. Jamais de téléchargement de malware brut sur l'hôte de développement
   Windows utilisé pour ce projet — la VM isolée, si elle est un jour
   provisionnée, est un environnement **séparé et non décrit plus avant
   ici** (décision hors périmètre de cette phase de conception).
6. Jamais de désactivation d'antivirus.

## 9. Prochaine étape (nécessite une approbation explicite, pas entreprise ici)

1. Décision utilisateur : provisionner ou non une VM isolée pour ce
   projet, et avec quels outils/isolation réseau exacts.
2. Identification d'une ou plusieurs sources de corpus DOCX satisfaisant
   §5 (multi-source, DOCX vérifié structurellement, provenance
   documentée).
3. Script d'extraction en lot (nouveau fichier, ex.
   `document_ml/docx/build_dataset.py`) appelant
   `extraire_features_docx()` sur chaque fichier du corpus, produisant
   uniquement le CSV/Parquet de caractéristiques + label + identifiant de
   groupe — à écrire et faire approuver séparément, pas dans cette phase.
4. Application du contrat de vérification déjà écrit dans
   `validation/DOCX-DATASET-ACCEPTANCE.md` (qualité de données,
   anti-fuite, tableau de compatibilité — désormais trivialement
   satisfait pour la compatibilité de schéma puisque l'extracteur EST
   `schema.py`/`features.py`, mais toujours requis pour la qualité et
   l'anti-fuite du nouveau corpus lui-même).
