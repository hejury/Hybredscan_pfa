# DOCX-CIC-CLARIFICATION-REQUEST.md — Demande préparée, NON envoyée

**Statut : brouillon. Aucun e-mail n'a été envoyé automatiquement.**

## 1. Contexte

Ce document prépare une demande de clarification aux auteurs du dataset
**CIC-Trap4Phish 2025** (Canadian Institute for Cybersecurity, University
of New Brunswick — portail officiel
<https://www.unb.ca/cic/datasets/trap4phish2025.html>, papier associé
*"CIC-Trap4Phish: A Unified Multi-Format Dataset for Phishing and Quishing
Attachment Detection"*, arXiv:2602.09015), suite à l'inspection du dataset
livré (`datasets/docx/Word_All_features.csv`,
`Word_Top10_Features.csv`) et de son code de référence officiel
(`datasets/docx/cic_reference/Doc_Feature_Extraction.ipynb`,
`Readme.txt`).

Cette inspection a abouti au statut **C. DOCX CIC DATASET UNSAFE FOR
DEFENSIBLE TRAINING** (voir `validation/DOCX-CIC-INSPECTION.md`,
`DOCX-CIC-SEMANTIC-REPAIR.md`, `DOCX-CIC-SAFE-SUBSET.md`), pour des
raisons précises et vérifiables que la demande ci-dessous cite
directement — jamais de reproche vague, uniquement des faits observés et
reproductibles de notre côté.

## 2. Contact identifié

Pas d'auteur individuel identifié spécifiquement pour ce dataset 2025
(contrairement à Koutsokostas/Patsakis pour le dataset Zenodo — voir
`DOCX-DATASET-REQUEST.md`). Le portail officiel CIC UNB est le point de
contact institutionnel :
<https://www.unb.ca/cic/datasets/trap4phish2025.html> (formulaire/contact
CIC habituellement listé sur <https://www.unb.ca/cic/contact.html> — à
vérifier au moment de l'envoi, non vérifié indépendamment ici). Si les
auteurs individuels du papier arXiv:2602.09015 (dont Fatemeh Nejati,
identifiée lors de la recherche précédente) sont joignables via leur
page institutionnelle, ils constituent une alternative à identifier avant
l'envoi — non fait ici pour rester dans le périmètre "préparation
uniquement" de cette phase.

## 3. Message proposé (à adapter et envoyer manuellement si approuvé)

> Objet : Question technique sur le dataset Word/DOCX — CIC-Trap4Phish 2025 (Word_All_features.csv)
>
> Bonjour,
>
> Je travaille sur un projet académique de détection de malware
> (HybridScan, projet de fin d'études) et j'utilise
> `Word_All_features.csv` / `Word_Top10_Features.csv`, ainsi que le
> notebook de référence `Doc_Feature_Extraction.ipynb`, tous deux
> téléchargés depuis le portail officiel CIC-Trap4Phish 2025.
>
> Lors de mon analyse, j'ai rencontré plusieurs points que je n'arrive pas
> à résoudre à partir de la documentation publique, et je me permets de
> vous les soumettre :
>
> **1. Portée du format Word.** Le fichier `Readme.txt` fourni indique que
> `Doc_Feature_Extraction.ipynb` "extracts features from Microsoft Word
> documents (.doc, .docx, .docm, .dotm)", et le notebook lui-même précise
> "Supports: .docx .docm .dotx .dotm .doc .dot" dans son en-tête. Le CSV
> livré ne contient cependant aucune colonne de format/extension. Les
> lignes de `Word_All_features.csv` correspondent-elles exclusivement à
> des `.docx`, ou à un mélange de tous ces formats ?
>
> **2. Indicateur de format par ligne.** Si le dataset mélange plusieurs
> formats, existe-t-il une table non publiée (ou une colonne que j'aurais
> manquée) permettant d'identifier le format exact de chaque ligne ?
>
> **3. Fidélité du notebook public.** `Doc_Feature_Extraction.ipynb`
> est-il exactement le code ayant servi à générer
> `Word_All_features.csv`, ou une version nettoyée/simplifiée a
> posteriori ? Je pose cette question car mon analyse suggère une
> incohérence (point 4 ci-dessous).
>
> **4. Génération de `dde_present`.** Dans le notebook fourni, la valeur
> de `dde_present` n'est calculée que dans une branche de code atteinte
> uniquement lorsque `macro_present` est déjà à 1 (la détection DDE se
> fait par recherche des sous-chaînes "DDE"/"DDEAUTO" dans le texte source
> VBA déjà extrait, donc seulement si des macros ont été détectées au
> préalable). Or, dans `Word_All_features.csv`, **9 994 lignes sur 20 000
> (49,97 %)** ont simultanément `macro_present = 0` et `dde_present = 1`
> — une combinaison qui semble impossible avec la logique du notebook tel
> que publié. Pourriez-vous éclairer comment `dde_present` a réellement
> été calculé pour le dataset livré ?
>
> **5. Table Word/DOCX corrigée.** Si les points 1 et 4 révèlent une
> version différente (plus ancienne ou corrigée) du pipeline
> d'extraction, une table strictement `.docx`, avec un mécanisme de
> `dde_present` cohérent avec les données livrées, serait-elle
> disponible ?
>
> **6. Source de collecte par échantillon.** Le README/papier indique que
> les échantillons bénins ont été collectés par exploration de sites
> "fiables" (Google, Wikipedia) et les échantillons malveillants
> principalement depuis MalwareBazaar. Une information de source de
> collecte par ligne (même agrégée, ex. "google_crawl" vs
> "malwarebazaar_2025_batch3") serait-elle partageable ? Ceci me
> permettrait d'auditer si une partie du signal observé (plusieurs
> caractéristiques atteignent un AUC descriptif supérieur à 0,99 dans mon
> analyse, y compris `file_size` de façon inattendue) reflète l'origine de
> collecte plutôt qu'une propriété de malveillance intrinsèque.
>
> Je vous remercie par avance pour votre temps, et reste à votre
> disposition pour partager mon analyse détaillée si cela peut être utile
> de votre côté (retour d'expérience sur le dataset).
>
> Cordialement,
> [Nom de l'utilisateur]

## 4. Rappel

**Ce message n'a pas été envoyé.** Comme pour les demandes précédentes
(`DOCX-DATASET-REQUEST.md`), l'envoi reste à la discrétion de
l'utilisateur, après identification d'un contact e-mail précis (le
portail CIC ou les auteurs individuels du papier) et personnalisation du
nom/affiliation.
