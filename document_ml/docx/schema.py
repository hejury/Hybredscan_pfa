#!/usr/bin/env python3
"""schema.py — Schema des caracteristiques statiques DOCX (document_ml.docx).

Chaque caracteristique est extraite de maniere PUREMENT statique : metadonnee
d'archive ZIP (noms/tailles d'entrees), texte brut de parties XML/VBA lues
en memoire (jamais interpretees comme XML executable, jamais de resolution
d'entite externe), et extraction VBA via oletools (analyse statique publique,
jamais d'execution de macro). Voir features.py pour l'implementation et
validation/DOCX-FEATURES.md pour la justification individuelle complete de
chaque caracteristique (type, plage attendue, comportement en absence
d'information, comportement en cas d'echec d'extraction).

Ce module ne fait que DECRIRE le schema (noms, ordre, documentation) ; il
n'extrait ni n'entraine rien lui-meme. AUCUN model_docx.pkl n'existe a ce
stade (phase de fondation/recherche de dataset uniquement)."""

MODEL_FILENAME = "model_docx.pkl"

SCHEMA_VERSION = 2
# v1 -> v2 : ajout de "xml_text_entropy" (voir FEATURE_DOC ci-dessous et
# validation/DOCX-RESEARCH-MODEL-TRAINING.md) -- caracteristique
# reproduisant EXACTEMENT la methode de calcul d'"entropy" du notebook de
# reference officiel CIC-Trap4Phish (Doc_Feature_Extraction.ipynb, cas
# OOXML), sous un nom DISTINCT de "vba_source_entropy" car ce n'est PAS la
# meme grandeur (texte XML concatene entier, pas le seul source VBA) --
# voir validation/DOCX-CIC-FEATURE-DEFINITIONS.md section 3.1 point 3.

FEATURES = [
    # --- Structure generale (conteneur ZIP / parties OOXML) ---
    "file_size_bytes",
    "zip_entry_count",
    "xml_entry_count",
    "rels_entry_count",
    "has_core_properties",
    "has_app_properties",
    "has_custom_properties",
    "nb_content_types_overrides",
    "has_customxml",
    # --- Macros / VBA (oletools, jamais executees) ---
    "has_vba_macros",
    "nb_vba_modules",
    "vba_source_length",
    "nb_autoexec_keywords",
    "has_any_autoexec",
    # --- Relations OOXML (texte brut des .rels, jamais suivies) ---
    "nb_relationships_total",
    "nb_relationships_external",
    "nb_hyperlink_relationships",
    "has_attached_template",
    "nb_remote_targets_rels",
    "has_oleobject_relationship",
    # --- Contenu integre (metadonnee d'archive uniquement) ---
    "has_embeddings_dir",
    "embedded_entry_count",
    "has_activex",
    "nb_executable_like_embedded_names",
    # --- Chaines suspectes / DDE / obfuscation (texte VBA uniquement) ---
    "nb_suspicious_strings",
    "nb_url_like_strings",
    "has_dde",
    "nb_long_base64_tokens",
    "vba_source_entropy",
    # --- Ajoutee en v2 : reproduction prouvee d'une caracteristique CIC ---
    "xml_text_entropy",
]

# Documentation individuelle complete : voir validation/DOCX-FEATURES.md
# (cahier des charges §7 : nom, type, methode d'extraction exacte,
# justification securite, plage attendue, comportement en absence
# d'information, comportement en cas d'echec du parseur, dependance
# oletools, garantie d'identite entrainement/runtime). Resume court ici
# uniquement pour un usage programmatique (ex. generation de documentation,
# validation croisee avec ce fichier) ; le document markdown fait foi.
FEATURE_DOC = {
    "file_size_bytes": "Taille du fichier en octets (os.path.getsize). ATTENTION -- voir "
                        "DOCX-FEATURES.md : cette caracteristique est fournie mais NE DOIT PAS "
                        "etre entrainee sans avoir explicitement confirme l'unite exacte du "
                        "dataset choisi (voir la lecon de document_ml/pdf/cic_schema.py v4 : "
                        "pdf_size retire pour exactement cette raison).",
    "zip_entry_count": "Nombre total d'entrees dans la table centrale du conteneur ZIP.",
    "xml_entry_count": "Nombre d'entrees dont le nom se termine par '.xml'.",
    "rels_entry_count": "Nombre d'entrees dont le nom se termine par '.rels'.",
    "has_core_properties": "1 si 'docProps/core.xml' est present, 0 sinon.",
    "has_app_properties": "1 si 'docProps/app.xml' est present, 0 sinon.",
    "has_custom_properties": "1 si 'docProps/custom.xml' est present, 0 sinon.",
    "nb_content_types_overrides": "Nombre d'occurrences du jeton '<Override' dans "
                                   "'[Content_Types].xml' -- proxy du nombre de parties internes "
                                   "declarees.",
    "has_customxml": "1 si une entree commence par 'customXml/', 0 sinon.",
    "has_vba_macros": "1 si oletools.olevba.VBA_Parser.detect_vba_macros() est vrai, 0 sinon.",
    "nb_vba_modules": "Nombre de modules VBA retournes par VBA_Parser.extract_macros().",
    "vba_source_length": "Longueur totale (caracteres) du code source VBA extrait (statique, "
                          "jamais execute) ; 0 si aucune macro.",
    "nb_autoexec_keywords": "Somme des indicateurs d'auto-execution presents dans le source VBA : "
                             "AutoOpen + Document_Open + Document_Close + AutoClose (0-4, "
                             "recherche insensible a la casse).",
    "has_any_autoexec": "1 si nb_autoexec_keywords > 0, 0 sinon.",
    "nb_relationships_total": "Nombre d'occurrences du jeton '<Relationship' dans l'ensemble des "
                               "parties '*.rels' du conteneur.",
    "nb_relationships_external": "Nombre d'occurrences de 'TargetMode=\"External\"' dans les "
                                  "parties '*.rels'.",
    "nb_hyperlink_relationships": "Nombre de relations dont l'attribut Type contient "
                                   "'hyperlink' (insensible a la casse).",
    "has_attached_template": "1 si une relation de Type contenant 'attachedTemplate' est presente "
                              "(technique connue d'injection de modele distant), 0 sinon.",
    "nb_remote_targets_rels": "Nombre de valeurs Target commencant par 'http://' ou 'https://' "
                               "dans les parties '*.rels'. Jamais resolues/suivies.",
    "has_oleobject_relationship": "1 si une relation de Type contenant 'oleObject' est presente, "
                                   "0 sinon.",
    "has_embeddings_dir": "1 si une entree commence par 'word/embeddings/', 0 sinon.",
    "embedded_entry_count": "Nombre d'entrees sous 'word/embeddings/'.",
    "has_activex": "1 si une entree commence par 'word/activeX/', 0 sinon.",
    "nb_executable_like_embedded_names": "Nombre d'entrees sous 'word/embeddings/' ou "
                                          "'word/activeX/' dont le nom se termine par une "
                                          "extension executable-like (.exe/.scr/.bat/.cmd/.vbs/"
                                          ".js/.jar/.ps1/.dll) -- nom de fichier uniquement, "
                                          "jamais le contenu ouvert.",
    "nb_suspicious_strings": "Nombre d'occurrences (insensible a la casse) des jetons "
                              "powershell/cmd.exe/wscript/cscript/mshta/rundll32/regsvr32/"
                              "certutil/bitsadmin/shell/createobject dans le SOURCE VBA extrait "
                              "uniquement. La presence seule n'implique pas la malveillance.",
    "nb_url_like_strings": "Nombre d'occurrences de 'http://'/'https://' dans le source VBA "
                            "extrait uniquement (distinct de nb_remote_targets_rels, qui "
                            "provient des relations OOXML, un canal different).",
    "has_dde": "1 si oletools.msodde detecte un lien DDE/DDEAUTO, 0 sinon.",
    "nb_long_base64_tokens": "Nombre de sous-chaines contigues d'au moins 40 caracteres "
                              "appartenant a l'alphabet base64 ([A-Za-z0-9+/]) dans le source "
                              "VBA extrait -- heuristique simple de contenu encode/obfusque.",
    "vba_source_entropy": "Entropie de Shannon (bits) du source VBA extrait ; 0.0 si aucune "
                           "macro (valeur reelle d'une chaine vide, pas une valeur fabriquee).",
    "xml_text_entropy": "Entropie de Shannon (bits/caractere, PAS bits/octet) calculee sur la "
                         "concatenation du texte decode de TOUTES les parties '.xml' du "
                         "conteneur -- reproduction prouvee, caractere par caractere sur une "
                         "chaine Python (pas les octets bruts), de la methode 'entropy' du "
                         "notebook officiel CIC-Trap4Phish (cas OOXML uniquement -- ce projet ne "
                         "traite jamais de .doc legacy, donc l'ambiguite de definition du "
                         "notebook selon le format ne s'applique pas ici, voir "
                         "DOCX-CIC-FEATURE-DEFINITIONS.md section 3). DISTINCTE de "
                         "'vba_source_entropy' (source VBA seul) -- portee volontairement plus "
                         "large (tout le XML du document). 0.0 si aucune partie .xml lisible "
                         "(cas structurellement impossible pour un DOCX valide, deja rejete par "
                         "validate.py avant d'atteindre ce calcul).",
}

assert set(FEATURE_DOC) == set(FEATURES), (
    "schema.py : FEATURE_DOC et FEATURES doivent lister exactement les "
    "memes noms de caracteristiques."
)
