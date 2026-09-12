#!/usr/bin/env python3
"""schema.py — Schema des caracteristiques statiques PDF (document_ml.pdf).

Chaque caracteristique est extraite par lecture d'octets et comptage par
expression reguliere sur le contenu BRUT du fichier (voir features.py) —
jamais par rendu du PDF, jamais par execution de JavaScript, jamais par
suivi de lien. Ce module ne fait que DECRIRE le schema (noms, ordre,
documentation) ; il n'extrait ni n'entraine rien lui-meme.

Le nom et l'ordre des colonnes dans FEATURES doivent rester stables : ils
sont serialises dans le bundle model_pdf.pkl (cle "features") et relus tels
quels a l'inference par predict.py — un changement d'ordre ou de nom sans
reentrainement invaliderait silencieusement le modele.
"""

MODEL_FILENAME = "model_pdf.pkl"

# Version du schema : a incrementer si FEATURES change (ajout, suppression,
# renommage, ou changement de semantique d'une colonne). Stockee dans les
# metadonnees du modele entraine (voir train.py) pour detecter un decalage
# entre un model_pdf.pkl existant et une version plus recente de ce fichier.
SCHEMA_VERSION = 1

FEATURES = [
    "file_size",
    "entropy",
    "pdf_version",
    "nb_obj",
    "nb_endobj",
    "nb_stream",
    "nb_endstream",
    "obj_stream_ratio",
    "nb_page",
    "has_javascript",
    "has_js",
    "has_openaction",
    "has_aa",
    "has_launch",
    "nb_uri",
    "has_embeddedfile",
    "has_acroform",
    "has_xfa",
    "nb_suspicious_actions",
    "has_encryption",
    "nb_obfuscated_names",
]

# Documentation individuelle de chaque caracteristique (BF §3 du cahier des
# charges document-ML : "Every feature must be documented"). Toutes sont
# extraites de maniere purement statique — comptage d'octets/jetons sur le
# contenu brut du fichier, y compris a l'interieur de flux compresses NON
# decompresses (voir features.py pour la justification de ce choix).
FEATURE_DOC = {
    "file_size":
        "Taille du fichier en octets.",
    "entropy":
        "Entropie de Shannon calculee sur l'ensemble des octets du fichier "
        "(0 a 8). Un PDF fortement compresse/obfusque presente typiquement "
        "une entropie plus elevee qu'un PDF texte simple.",
    "pdf_version":
        "Version PDF declaree dans l'en-tete '%PDF-x.y' (ex. 1.4), 0.0 si "
        "illisible ou absente dans les 2048 premiers octets.",
    "nb_obj":
        "Nombre d'occurrences du motif '<n> <g> obj' (debut d'objet indirect "
        "PDF, ex. '12 0 obj').",
    "nb_endobj":
        "Nombre d'occurrences du jeton 'endobj'.",
    "nb_stream":
        "Nombre d'occurrences du jeton 'stream' (debut de flux de donnees, "
        "souvent compresse — contenu de page, police, JavaScript, etc.).",
    "nb_endstream":
        "Nombre d'occurrences du jeton 'endstream'.",
    "obj_stream_ratio":
        "Ratio nb_stream / max(nb_obj, 1) — un ratio eleve peut indiquer un "
        "fichier majoritairement compose de flux de donnees plutot que "
        "d'objets structurels classiques.",
    "nb_page":
        "Nombre d'occurrences du motif '/Type /Page' ou '/Type/Page' "
        "(approximation du nombre de pages ; un PDF valide en a au moins 1).",
    "has_javascript":
        "1 si le jeton '/JavaScript' est present dans le fichier, 0 sinon. "
        "Le JavaScript declare n'est JAMAIS execute par cet extracteur.",
    "has_js":
        "1 si le jeton '/JS' (cle alternative referencant du code "
        "JavaScript) est present, 0 sinon. Jamais execute.",
    "has_openaction":
        "1 si le jeton '/OpenAction' est present (action declenchee "
        "automatiquement a l'ouverture du document), 0 sinon.",
    "has_aa":
        "1 si le jeton '/AA' (Additional Actions — actions declenchees par "
        "des evenements du lecteur), 0 sinon.",
    "has_launch":
        "1 si le jeton '/Launch' (lancement d'une application ou d'un "
        "fichier externe) est present, 0 sinon. Jamais suivi/execute.",
    "nb_uri":
        "Nombre d'occurrences du jeton '/URI' (liens/URL externes declares "
        "dans le document). Jamais resolus ni ouverts par cet extracteur.",
    "has_embeddedfile":
        "1 si le jeton '/EmbeddedFile' est present (fichier integre au "
        "PDF), 0 sinon. Le fichier integre n'est jamais extrait sur disque "
        "ni ouvert par cet extracteur.",
    "has_acroform":
        "1 si le jeton '/AcroForm' est present (formulaire interactif), "
        "0 sinon.",
    "has_xfa":
        "1 si le jeton '/XFA' est present (formulaire XFA — technologie "
        "historiquement associee a plusieurs vulnerabilites connues des "
        "lecteurs PDF), 0 sinon.",
    "nb_suspicious_actions":
        "Somme des indicateurs d'action potentiellement dangereuse : "
        "has_openaction + has_aa + has_launch + has_javascript + has_js.",
    "has_encryption":
        "1 si le jeton '/Encrypt' est present (dictionnaire de chiffrement "
        "PDF standard), 0 sinon — un PDF chiffre peut viser a dissimuler son "
        "contenu a une analyse statique naive.",
    "nb_obfuscated_names":
        "Nombre de noms PDF utilisant l'echappement hexadecimal '#xx' "
        "(ex. '/Ja#76aScript' pour masquer '/JavaScript') — technique "
        "d'obfuscation documentee des PDF malveillants pour echapper a une "
        "detection par simple recherche de motif en clair.",
}

assert set(FEATURE_DOC) == set(FEATURES), (
    "schema.py : FEATURE_DOC et FEATURES doivent lister exactement les "
    "memes noms de caracteristiques (chaque caracteristique doit etre "
    "documentee, et aucune entree de documentation ne doit etre orpheline)."
)
