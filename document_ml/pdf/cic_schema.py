#!/usr/bin/env python3
"""cic_schema.py — Schema CIC-compatible (sous-ensemble defensible) pour
document_ml.pdf.

INDEPENDANT de schema.py (le schema PDF existant de HybridScan, phase 2) —
ce fichier ne le remplace pas et n'est importe par rien d'existant
(analyze.py, predict.py, train.py, evaluate.py restent inchanges). Voir
validation/CIC-PDF-FEATURE-COMPATIBILITY.md pour l'analyse complete de
compatibilite qui justifie chaque caracteristique retenue ici, et
validation/CIC-PDF-DATA-QUALITY.md pour l'analyse class-conditionnelle
(Benign vs Malicious) qui justifie l'exclusion de Header (§ ci-dessous).

VERSION 2 (mise a jour apres import du fichier reel) : le fichier reel
`datasets/pdf/PDFMalware2022.parquet` a ete obtenu et inspecte. Les 20
caracteristiques ci-dessous ont chacune une colonne reelle correspondante
(voir document_ml/pdf/cic_cleaning.py::COLONNE_REELLE pour le mapping EXACT,
verifie par inspection directe, y compris les corrections de capitalisation
"Javascript"/"Acroform" et la redirection de nb_page_approx vers "PageNo").
`header_present` (present en v1, base sur une hypothese non verifiee) a ete
RETIRE : voir cic_cleaning.EXCLU_HEADER_RAISON et
CIC-PDF-DATA-QUALITY.md pour la justification chiffree.

VERSION 3 (revue anti-fuite) : `is_encrypted` RETIRE. La colonne reelle
'isEncrypted' varie de 0 a 4 (pas un booleen propre comme suppose en v1/v2) ;
aucune documentation officielle CIC/PDFiD ne definit la semantique des
valeurs 2/3/4, et elle diverge de la colonne structurelle separee 'Encrypt'
sur ~0.86% des lignes comparables (voir validation/CIC-PDF-ANTI-LEAKAGE.md
§1). Cahier des charges : "If exact semantics cannot be proven: REMOVE...
Do not guess." — retire plutot que suppose booleen.

VERSION 4 (reparation de fidelite runtime) : `pdf_size` RETIRE. Decouvert
lors des tests d'integration reels (validation/PDF-MODEL-FINAL-EVALUATION.md
§9) : la colonne reelle 'PdfSize' varie de 0 a ~20-23k avec une mediane de
12-76, une echelle implausible pour un compte d'octets brut (un PDF valide
minimal fait deja plusieurs centaines d'octets) mais plausible en KILO-OCTETS.
Une reproduction TIERCE independante (Mathys-Rituper/PDF-feature-extractor,
src/extract.py ligne 126 : `round(os.path.getsize(path) / 1024, 2)`) implemente
exactement cette conversion, ce qui corrobore fortement l'hypothese KB —
mais ce depot n'est PAS la source CIC officielle (son propre README le
decrit comme un extracteur "ameliore", donc une reinterpretation, pas une
reproduction certifiee fidele de la methodologie originale). Cette preuve
tierce ne constitue donc pas une "documentation officielle prouvee" au sens
strict exige par le cahier des charges ("Do not guess a conversion from the
observed range alone" — une inference tierce, meme corroborante, reste une
inference, pas une specification). Retire plutot que transforme sur la base
d'une preuve non-officielle. Voir validation/PDF-RUNTIME-FIDELITY.md pour le
detail complet de cette decision.

Ce schema decrit la liste et l'ORDRE des caracteristiques d'entrainement
proposees ; le nettoyage des valeurs reelles (sentinelle -1, notation
composee PDFiD, texte fuite) est implemente separement dans
cic_cleaning.py, jamais ici."""

# Nom du fichier modele final en production, a cote de model.pkl (PE) et
# history.csv dans BASE (voir analyze.py/predict.py). Renomme depuis
# "model_pdf_cic.pkl" (phases 4-6) vers "model_pdf.pkl" au moment de
# l'entrainement final (phase 7) : c'est desormais LE modele PDF de
# production, le seul jamais charge par document_ml/pdf/predict.py.
MODEL_FILENAME = "model_pdf.pkl"

# A incrementer si CIC_FEATURES change. v2 : retrait de "header_present".
# v3 : retrait de "is_encrypted" (semantique reelle non prouvee, voir
# CIC-PDF-ANTI-LEAKAGE.md §1). v4 : retrait de "pdf_size" (unite reelle non
# prouvee -- probable kilo-octets vs octets bruts au runtime, voir
# PDF-RUNTIME-FIDELITY.md).
CIC_SCHEMA_VERSION = 4

# --- Classe A : exactement reproductible (comptage d'octets bruts, sans
# ambiguite de methode — voir §4/§5 du document de compatibilite) ---------
_FEATURES_CLASSE_A = [
    "nb_stream_kw",
    "nb_endstream_kw",
    "nb_objstm_kw",
    "nb_trailer_kw",
    "nb_xref_kw",
    "nb_startxref_kw",
]

# --- Classe B : reproductible avec transformation documentee (le plus
# souvent : comptage au lieu d'un booleen de presence, meme jeton exact que
# la liste de mots-cles canonique de PDFiD) --------------------------------
_FEATURES_CLASSE_B = [
    "nb_obj_kw",
    "nb_page_approx",
    "nb_embeddedfile_kw",
    "nb_js_kw",
    "nb_javascript_kw",
    "nb_aa_kw",
    "nb_openaction_kw",
    "nb_launch_kw",
    "nb_acroform_kw",
    "nb_xfa_kw",
    "nb_jbig2decode_kw",
    "nb_richmedia_kw",
]

CIC_FEATURES = _FEATURES_CLASSE_A + _FEATURES_CLASSE_B

# Documentation individuelle — classe, jeton PDFiD/CIC correspondant,
# justification. Voir validation/CIC-PDF-FEATURE-COMPATIBILITY.md pour le
# tableau complet incluant les caracteristiques EXCLUES (classes C et D).
CIC_FEATURE_DOC = {
    "nb_stream_kw": {
        "classe": "A",
        "cic_feature": "No. of keywords \"streams\"",
        "definition": "Nombre d'occurrences du jeton 'stream' — identique a schema.FEATURES['nb_stream'] et "
                       "au comptage du mot-cle 'stream' de PDFiD.",
    },
    "nb_endstream_kw": {
        "classe": "A",
        "cic_feature": "No. of keywords \"endstreams\"",
        "definition": "Nombre d'occurrences du jeton 'endstream' — identique a schema.FEATURES['nb_endstream'].",
    },
    "nb_objstm_kw": {
        "classe": "A",
        "cic_feature": "No. of stream objects (ObjStm)",
        "definition": "Nombre d'occurrences du jeton '/ObjStm' (mot-cle de base PDFiD).",
    },
    "nb_trailer_kw": {
        "classe": "A",
        "cic_feature": "/Trailer",
        "definition": "Nombre d'occurrences du jeton 'trailer' (mot-cle de base PDFiD) — distinct de la "
                       "'No. of Xref entries' (classe D, exclue : necessite un vrai parseur de table xref).",
    },
    "nb_xref_kw": {
        "classe": "A",
        "cic_feature": "/Xref",
        "definition": "Nombre d'occurrences du jeton 'xref' (mot-cle de base PDFiD) — comptage du jeton "
                       "lui-meme, PAS le nombre d'entrees de la table (voir ci-dessus).",
    },
    "nb_startxref_kw": {
        "classe": "A",
        "cic_feature": "/Startxref",
        "definition": "Nombre d'occurrences du jeton 'startxref' (mot-cle de base PDFiD).",
    },
    "nb_obj_kw": {
        "classe": "B",
        "cic_feature": "Object number",
        "definition": "Nombre d'occurrences du motif '<n> <g> obj' — tres proche de schema.FEATURES['nb_obj'] "
                       "et du comptage du mot-cle 'obj' de PDFiD ; divergence possible sur fichiers malformes.",
    },
    "nb_page_approx": {
        "classe": "B",
        "cic_feature": "PageNo (structural /Page keyword count)",
        "definition": "APPROXIMATION : nombre d'occurrences du motif '/Type /Page' — identique a "
                       "schema.FEATURES['nb_page']. CORRIGE apres inspection du fichier reel (v1 mappait a tort "
                       "vers la colonne generale 'Pages', un vrai compte de pages presumement issu de PyMuPDF) : "
                       "la colonne reelle correspondante est 'PageNo' (structurelle, comptage du mot-cle "
                       "'/Page' de PDFiD), distincte de 'Pages' qui reste hors de ce sous-ensemble (non "
                       "reproductible sans un vrai parseur — voir CIC-PDF-FEATURE-COMPATIBILITY.md §8.5).",
    },
    "nb_embeddedfile_kw": {
        "classe": "B",
        "cic_feature": "Number of embedded files",
        "definition": "Nombre d'occurrences du jeton '/EmbeddedFile' (mot-cle de base PDFiD) — schema.FEATURES "
                       "expose ceci comme un booleen ('has_embeddedfile') ; ici transforme en comptage pour "
                       "correspondre a la semantique CIC.",
    },
    "nb_js_kw": {
        "classe": "B",
        "cic_feature": "/JS",
        "definition": "Nombre d'occurrences du jeton '/JS' (mot-cle de base PDFiD) — transformation "
                       "comptage-au-lieu-de-booleen depuis schema.FEATURES['has_js'].",
    },
    "nb_javascript_kw": {
        "classe": "B",
        "cic_feature": "/JavaScript",
        "definition": "Nombre d'occurrences du jeton '/JavaScript' (mot-cle de base PDFiD) — transformation "
                       "depuis schema.FEATURES['has_javascript']. Jamais execute. Colonne reelle : 'Javascript' "
                       "(capitalisation corrigee apres inspection du fichier reel, pas 'JavaScript').",
    },
    "nb_aa_kw": {
        "classe": "B",
        "cic_feature": "/AA",
        "definition": "Nombre d'occurrences du jeton '/AA' (mot-cle de base PDFiD) — transformation depuis "
                       "schema.FEATURES['has_aa'].",
    },
    "nb_openaction_kw": {
        "classe": "B",
        "cic_feature": "/OpenAction",
        "definition": "Nombre d'occurrences du jeton '/OpenAction' (mot-cle de base PDFiD) — transformation "
                       "depuis schema.FEATURES['has_openaction'].",
    },
    "nb_launch_kw": {
        "classe": "B",
        "cic_feature": "/launch",
        "definition": "Nombre d'occurrences du jeton '/Launch' (mot-cle de base PDFiD) — transformation depuis "
                       "schema.FEATURES['has_launch']. Jamais suivi/execute.",
    },
    "nb_acroform_kw": {
        "classe": "B",
        "cic_feature": "/Acroform",
        "definition": "Nombre d'occurrences du jeton '/AcroForm' (mot-cle de base PDFiD) — transformation "
                       "depuis schema.FEATURES['has_acroform']. Colonne reelle : 'Acroform' (capitalisation "
                       "corrigee apres inspection du fichier reel, pas 'AcroForm').",
    },
    "nb_xfa_kw": {
        "classe": "B",
        "cic_feature": "/XFA",
        "definition": "Nombre d'occurrences du jeton '/XFA' (mot-cle de base PDFiD) — transformation depuis "
                       "schema.FEATURES['has_xfa'].",
    },
    "nb_jbig2decode_kw": {
        "classe": "B",
        "cic_feature": "/JBig2Decode",
        "definition": "Nombre d'occurrences du jeton '/JBIG2Decode' (mot-cle de base PDFiD) — nouvelle "
                       "caracteristique, absente de schema.FEATURES, ajoutee ici avec la meme technique.",
    },
    "nb_richmedia_kw": {
        "classe": "B",
        "cic_feature": "/RichMedia",
        "definition": "Nombre d'occurrences du jeton '/RichMedia' (mot-cle de base PDFiD) — nouvelle "
                       "caracteristique, absente de schema.FEATURES, ajoutee ici avec la meme technique.",
    },
}

assert set(CIC_FEATURE_DOC) == set(CIC_FEATURES), (
    "cic_schema.py : CIC_FEATURE_DOC et CIC_FEATURES doivent lister exactement les "
    "memes noms de caracteristiques."
)

# Caracteristiques CIC officielles delibrement EXCLUES de ce schema (classes
# C et D — voir validation/CIC-PDF-FEATURE-COMPATIBILITY.md §4 pour le
# detail de chacune). Liste conservee ici, pas seulement dans le document
# markdown, pour qu'un futur contributeur voie immediatement, depuis le
# code, que leur absence est une decision documentee et non un oubli.
CIC_FEATURES_EXCLUES_CLASSE_C = [
    "Title characters", "Font objects", "Average stream size",
    "No. of name obfuscations", "/URI", "/Action", "/submitForm",
]
CIC_FEATURES_EXCLUES_CLASSE_D = [
    "Metadata size", "Image number", "Text",
    "Average size of all the embedded media", "No. of Xref entries",
    "Total number of filters used", "No. of objects with nested filters",
    "Colors",
]

# Retire en v2, APRES avoir ete inclus en v1 : contrairement aux listes
# ci-dessus (jamais retenues, car non reproductibles au runtime au sens
# strict), "Header" AVAIT ete inclus en v1 (classe A, "header_present") sur
# la base d'une hypothese non verifiee. L'import du fichier reel a montre :
# (1) semantique non fiable au runtime (voir cic_cleaning.EXCLU_HEADER_RAISON),
# (2) l'ecart de validite Malicious/Benign le plus eleve de tout le schema
# (20.03 points, contre 5-13 pour les autres — voir
# validation/CIC-PDF-DATA-QUALITY.md §2). Retire plutot que force a rester
# pour la seule compatibilite ascendante avec la v1 (cahier des charges §6 :
# "Do not keep ... merely for backward compatibility if it is scientifically
# incompatible").
CIC_FEATURES_EXCLUES_DONNEES_REELLES = [
    "Header (header_present, retire en v2)",
    "Encryption (is_encrypted, retire en v3 : colonne reelle 'isEncrypted' "
    "variant de 0 a 4 sans semantique documentee pour 2/3/4, en desaccord "
    "avec la colonne 'Encrypt' separee sur ~0.86% des lignes comparables — "
    "voir validation/CIC-PDF-ANTI-LEAKAGE.md §1)",
    "PDF size (pdf_size, retire en v4 : colonne reelle 'PdfSize' (mediane "
    "12-76, max ~20-23k) implausible en octets bruts, plausible en "
    "kilo-octets ; une reproduction tierce independante implemente "
    "exactement round(getsize/1024,2) mais n'est pas la source CIC "
    "officielle — preuve corroborante, pas une specification prouvee — "
    "voir validation/PDF-RUNTIME-FIDELITY.md)",
]


def valider_contrat_schema(colonnes, label_col=None):
    """Contrat de schema reutilisable par un futur train.py/predict.py
    CIC-compatible (BF §7 — pas encore cable dans train.py/predict.py
    existants par cette tache, voir rapport final).

    - Leve ValueError si une colonne de CIC_FEATURES est absente de
      `colonnes` (echec sur — jamais un remplissage silencieux par une
      valeur par defaut, qui fausserait l'inference).
    - Leve ValueError si `label_col` est lui-meme un nom de caracteristique
      (la colonne d'etiquette ne doit jamais fuiter dans le vecteur de
      caracteristiques).
    - Retourne la liste des colonnes presentes dans `colonnes` mais ni dans
      CIC_FEATURES ni egales a `label_col` — des colonnes EXTRA, explicitement
      ignorees par l'appelant (jamais silencieusement inclues dans
      l'entrainement), pas rejetees en erreur : un CSV source peut
      legitimement contenir des colonnes de metadonnees (ex. "filename")
      non pertinentes pour l'entrainement."""
    colonnes = list(colonnes)
    if label_col is not None and label_col in CIC_FEATURES:
        raise ValueError("valider_contrat_schema : la colonne d'etiquette '%s' ne peut pas "
                          "etre aussi un nom de caracteristique" % label_col)
    manquantes = [c for c in CIC_FEATURES if c not in colonnes]
    if manquantes:
        raise ValueError("valider_contrat_schema : colonnes de caracteristiques CIC manquantes : %s"
                          % manquantes)
    extra = [c for c in colonnes if c not in CIC_FEATURES and c != label_col]
    return extra
