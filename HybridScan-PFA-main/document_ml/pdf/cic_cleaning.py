#!/usr/bin/env python3
"""cic_cleaning.py — Couche de nettoyage DETERMINISTE pour les donnees
reelles PDFMalware2022 (datasets/pdf/PDFMalware2022.parquet).

Portee : ce module nettoie les colonnes reelles du fichier Parquet
importe vers les caracteristiques `document_ml.pdf.cic_schema.CIC_FEATURES`.
Il n'est PAS cable dans analyze.py/app.py/predict.py/train.py — ce module
prepare des DONNEES D'ENTRAINEMENT hors-ligne, jamais l'inference en
production. Voir validation/CIC-PDF-FEATURE-COMPATIBILITY.md §8 pour
l'analyse complete qui a produit les regles ci-dessous, et
validation/CIC-PDF-DATA-QUALITY.md pour les chiffres class-conditionnels
qu'il permet de calculer.

Regles de nettoyage (cahier des charges §3) :
  A. sentinelle "-1"                -> manquant (jamais traite comme un
                                        compte reel de 0 occurrence).
  B. notation PDFiD "N(M)"          -> N (Count) retenu comme valeur
                                        d'entrainement, exactement la
                                        semantique que cic_features.py
                                        calcule au runtime (comptage total,
                                        obfuscation incluse — voir le
                                        commentaire de
                                        nettoyer_valeur_texte_comptage) ;
                                        M (HexcodeCount) conserve pour
                                        diagnostic uniquement, jamais
                                        utilise comme caracteristique.
  C. texte fuite (ex. "pdfid.py",
     "bytes[endHeader]", fragments
     de nom de fichier, ">", "list") -> invalide, jamais convertie en 0.
  D. valeurs numeriques genuines     -> conservees telles quelles.

Aucune valeur textuelle arbitraire n'est jamais convertie en zero — une
valeur non reconnue devient toujours "manquant" (None), jamais 0."""
import re

# --- Correspondance caracteristique CIC -> colonne REELLE du Parquet -------
# Corrigee suite a l'inspection directe du fichier reel (voir
# CIC-PDF-FEATURE-COMPATIBILITY.md §8.5) :
#   - "Javascript" / "Acroform" (PAS "JavaScript" / "AcroForm")
#   - nb_page_approx -> "PageNo" (PAS "Pages", qui est une colonne
#     "generale" distincte, non couverte par ce sous-ensemble)
# "header_present" est volontairement ABSENT : voir EXCLU_HEADER_RAISON.
# "is_encrypted" egalement ABSENT depuis le schema v3 : voir
# EXCLU_IS_ENCRYPTED_RAISON ci-dessous. "pdf_size" egalement ABSENT depuis
# le schema v4 : voir EXCLU_PDF_SIZE_RAISON ci-dessous.
COLONNE_REELLE = {
    "nb_stream_kw": "Stream",
    "nb_endstream_kw": "Endstream",
    "nb_objstm_kw": "ObjStm",
    "nb_trailer_kw": "Trailer",
    "nb_xref_kw": "Xref",
    "nb_startxref_kw": "StartXref",
    "nb_obj_kw": "Obj",
    "nb_page_approx": "PageNo",
    "nb_embeddedfile_kw": "EmbeddedFile",
    "nb_js_kw": "JS",
    "nb_javascript_kw": "Javascript",
    "nb_aa_kw": "AA",
    "nb_openaction_kw": "OpenAction",
    "nb_launch_kw": "Launch",
    "nb_acroform_kw": "Acroform",
    "nb_xfa_kw": "XFA",
    "nb_jbig2decode_kw": "JBIG2Decode",
    "nb_richmedia_kw": "RichMedia",
}

# Colonnes reelles stockees en float32 natif par PyArrow : verifie par
# inspection directe (CIC-PDF-FEATURE-COMPATIBILITY.md §8.4) que leur SEULE
# anomalie est la sentinelle -1 — jamais de notation composee ni de texte
# fuite, ce sont deja des nombres, pas des chaines.
COLONNES_FLOAT_PUR = frozenset({"nb_stream_kw",
                                 "nb_objstm_kw", "nb_trailer_kw"})

# Colonnes reelles stockees en texte/categorie : peuvent contenir un entier
# simple, une notation composee "N(M)", ou du texte fuite.
COLONNES_TEXTE_COMPTAGE = frozenset(COLONNE_REELLE) - COLONNES_FLOAT_PUR

SENTINELLE_MANQUANT = -1

_RE_ENTIER_SIMPLE = re.compile(r"^(-?\d+)$")
_RE_COMPOSE = re.compile(r"^(\d+)\((\d+)\)$")
_RE_HEADER_BIEN_FORME = re.compile(r"^\t?%PDF-\d\.\d$")

# Pourquoi "header_present" n'est pas dans COLONNE_REELLE (cahier des
# charges §2 : "If Header semantics cannot be reproduced reliably at
# runtime, exclude Header ... rather than inventing a transformation").
EXCLU_HEADER_RAISON = (
    "Header exclu du sous-ensemble d'entrainement final : (1) semantique non "
    "reproductible de maniere fiable au runtime -- la colonne reelle est une "
    "chaine de version brute avec un caractere tabulation en tete, alors que "
    "cic_features.py ne produit qu'un booleen de presence d'en-tete via une "
    "regex independante, jamais verifiee equivalente a la logique qui a "
    "genere cette colonne ; (2) une fraction substantielle des valeurs "
    "reelles est manifestement corrompue (ex. '\\ta', '\\tyour', "
    "'\\t%PDF-11113') sans qu'aucune regle deterministe documentee ne "
    "permette de les distinguer de maniere fiable d'un en-tete legitime "
    "mais atypique -- voir CIC-PDF-DATA-QUALITY.md pour les chiffres "
    "exacts (class-conditionnels) qui justifient cette decision."
)

# Pourquoi "is_encrypted" n'est pas (plus, depuis le schema v3) dans
# COLONNE_REELLE (cahier des charges de la revue anti-fuite §1 : "If exact
# semantics cannot be proven: REMOVE ... Do not guess").
EXCLU_IS_ENCRYPTED_RAISON = (
    "is_encrypted exclu du sous-ensemble d'entrainement (v3) : la colonne "
    "reelle 'isEncrypted' varie de 0 a 4 (9640 lignes a 0, 75 a 1, seulement "
    "6 lignes au total a 2/3/4) alors que l'extracteur runtime produit un "
    "booleen 0/1 base sur la simple presence du jeton '/Encrypt'. Aucune "
    "documentation officielle CIC/PDFiD ne definit la semantique des valeurs "
    "2/3/4. De plus, 'isEncrypted' diverge de la colonne structurelle "
    "separee 'Encrypt' (comptage du mot-cle PDFiD '/Encrypt') sur environ "
    "0.86% des lignes ou les deux sont valides -- ce ne sont pas deux vues "
    "redondantes du meme fait. Sans preuve de semantique exacte, la "
    "caracteristique est retiree plutot que supposee booleen -- voir "
    "validation/CIC-PDF-ANTI-LEAKAGE.md §1."
)

# Pourquoi "pdf_size" n'est pas (plus, depuis le schema v4) dans
# COLONNE_REELLE -- decouvert lors des tests d'integration reels (cahier
# des charges de la reparation de fidelite runtime §1).
EXCLU_PDF_SIZE_RAISON = (
    "pdf_size exclu du sous-ensemble d'entrainement (v4) : la colonne reelle "
    "'PdfSize' varie de 0 a ~20 510-23 816 avec une mediane de 12 (Malicious) "
    "/ 76 (Benign) -- une echelle implausible pour un compte d'octets bruts "
    "(un PDF valide minimal fait deja plusieurs centaines d'octets) mais "
    "plausible en kilo-octets. L'extracteur runtime (cic_features.py) "
    "calculait pdf_size = len(octets_bruts), c'est-a-dire des octets VRAIS -- "
    "un ecart d'echelle confirme empiriquement (des PDF benins realistes de "
    "quelques dizaines de Ko a plusieurs Mo produisaient des valeurs 100 a "
    "1000x hors de la plage d'entrainement, et ont ete classes 'malveillant' "
    "lors de tests d'integration manuels). Une reproduction TIERCE "
    "independante (Mathys-Rituper/PDF-feature-extractor, src/extract.py "
    "ligne 126) implemente exactement round(getsize/1024, 2), corroborant "
    "l'hypothese kilo-octets -- mais ce depot n'est pas la source CIC "
    "officielle (son propre README le decrit comme 'ameliore', donc "
    "reinterprete, pas certifie fidele). Cette preuve tierce corroborante "
    "ne constitue pas une documentation officielle prouvee. Retire plutot "
    "que transforme sur la base d'une inference, meme corroboree -- voir "
    "validation/PDF-RUNTIME-FIDELITY.md."
)


class ValeurNettoyee:
    """Resultat du nettoyage d'UNE valeur brute pour UNE caracteristique.

    - `valeur` : float retenu pour l'entrainement, ou None si la ligne est
      manquante/invalide pour cette caracteristique (jamais une valeur
      fabriquee comme 0).
    - `statut` : une des 5 categories exigees par le cahier des charges §5 :
      "valide", "manquant_sentinelle", "compose_malforme", "texte_fuite",
      "autre_invalide".
    - `hexcode_count` : le second composant (M) de la notation "N(M)" quand
      present, sinon None -- conserve pour tracabilite/diagnostic (§3B :
      "do not silently discard information without documenting it") mais
      JAMAIS utilise comme caracteristique d'entrainement (aucune colonne
      *_hexcode n'existe dans cic_schema.CIC_FEATURES)."""
    __slots__ = ("valeur", "statut", "hexcode_count")

    def __init__(self, valeur, statut, hexcode_count=None):
        self.valeur = valeur
        self.statut = statut
        self.hexcode_count = hexcode_count


def nettoyer_valeur_float_pure(x):
    """Colonnes float32 natives (PdfSize, isEncrypted, Stream, ObjStm,
    Trailer). `x` est deja un nombre (jamais une chaine) : la seule
    transformation necessaire est la sentinelle -1 -> manquant."""
    if x is None:
        return ValeurNettoyee(None, "autre_invalide")
    try:
        v = float(x)
    except (TypeError, ValueError):
        return ValeurNettoyee(None, "autre_invalide")
    if v != v:  # NaN
        return ValeurNettoyee(None, "autre_invalide")
    if v == SENTINELLE_MANQUANT:
        return ValeurNettoyee(None, "manquant_sentinelle")
    if v < 0:
        # Aucune valeur negative autre que -1 n'a ete observee lors de
        # l'inspection (CIC-PDF-FEATURE-COMPATIBILITY.md §8.4) ; une telle
        # valeur serait une anomalie non documentee -- jamais silencieusement
        # acceptee comme un compte valide.
        return ValeurNettoyee(None, "autre_invalide")
    return ValeurNettoyee(v, "valide")


def nettoyer_valeur_texte_comptage(x):
    """Colonnes texte/categorie representant un comptage de mot-cle (Obj,
    Endobj, Endstream, Xref, StartXref, PageNo, JS, Javascript, AA,
    OpenAction, Launch, Acroform, XFA, JBIG2Decode, RichMedia,
    EmbeddedFile). Gere explicitement les 3 formes documentees dans
    CIC-PDF-FEATURE-COMPATIBILITY.md §8.4 :

      1. Entier simple "N" (ou "-1") -> valeur numerique directe, ou
         manquant si N == -1.
      2. Notation composee "N(M)" (Count(HexcodeCount), style PDFiD -- voir
         la sortie XML de pdfid.py citee dans ce meme document, ou
         Count inclut deja les occurrences obfusquees, HexcodeCount en
         etant le sous-ensemble) : N est retenu comme valeur d'entrainement
         car il correspond exactement a ce que cic_features.py calcule au
         runtime (un comptage total par sous-chaine, qui compte deja les
         occurrences obfusquees comme n'importe quelle autre occurrence
         litterale du jeton) ; M est conserve dans `hexcode_count` pour
         diagnostic uniquement.
      3. Tout le reste (texte fuite type "pdfid.py", "bytes[endHeader]",
         fragments de nom de fichier, ">", "list", etc.) : invalide, JAMAIS
         convertie en 0 ni en toute autre valeur numerique."""
    if x is None:
        return ValeurNettoyee(None, "autre_invalide")
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return ValeurNettoyee(None, "autre_invalide")

    m_simple = _RE_ENTIER_SIMPLE.match(s)
    if m_simple:
        n = int(m_simple.group(1))
        if n == SENTINELLE_MANQUANT:
            return ValeurNettoyee(None, "manquant_sentinelle")
        if n < 0:
            return ValeurNettoyee(None, "autre_invalide")
        return ValeurNettoyee(float(n), "valide")

    m_compose = _RE_COMPOSE.match(s)
    if m_compose:
        n, hexn = int(m_compose.group(1)), int(m_compose.group(2))
        return ValeurNettoyee(float(n), "compose_malforme", hexcode_count=float(hexn))

    return ValeurNettoyee(None, "texte_fuite")


def nettoyer_valeur_header(x):
    """Nettoyeur DEDIE a la colonne 'Header' -- NON utilise pour produire le
    sous-ensemble d'entrainement final (voir EXCLU_HEADER_RAISON), conserve
    uniquement pour alimenter l'analyse de qualite class-conditionnelle qui
    JUSTIFIE l'exclusion avec des chiffres plutot que de l'affirmer sans
    preuve (cahier des charges §5)."""
    if x is None:
        return ValeurNettoyee(None, "autre_invalide")
    s = str(x)
    if s.strip() == str(SENTINELLE_MANQUANT):
        return ValeurNettoyee(None, "manquant_sentinelle")
    if _RE_HEADER_BIEN_FORME.match(s):
        return ValeurNettoyee(1.0, "valide")
    if s.strip() in ("0", "1"):
        # Ni une chaine d'en-tete, ni la sentinelle -1 : une valeur
        # numerique isolee dans un champ cense contenir du texte de
        # version -- traitee comme anomalie distincte du texte fuite.
        return ValeurNettoyee(None, "autre_invalide")
    return ValeurNettoyee(None, "texte_fuite")


def nettoyer_colonne(nom_caracteristique, valeurs):
    """Applique le nettoyeur approprie (float pur ou texte-comptage) a une
    sequence de valeurs brutes pour UNE caracteristique cic_schema. Retourne
    la liste de ValeurNettoyee correspondante, dans le meme ordre. Leve
    KeyError si `nom_caracteristique` n'est pas dans COLONNE_REELLE (jamais
    un nettoyage silencieux d'une caracteristique inconnue ou exclue)."""
    if nom_caracteristique not in COLONNE_REELLE:
        raise KeyError("nettoyer_colonne : caracteristique inconnue ou exclue : %s" % nom_caracteristique)
    fn = (nettoyer_valeur_float_pure if nom_caracteristique in COLONNES_FLOAT_PUR
          else nettoyer_valeur_texte_comptage)
    return [fn(v) for v in valeurs]


def nettoyer_dataframe(df):
    """Nettoie TOUTES les caracteristiques de COLONNE_REELLE a partir du
    DataFrame brut (colonnes reelles du Parquet importe). Retourne
    (df_valeurs, df_statuts, df_hexcode) -- trois DataFrame pandas alignes
    sur le meme index que `df`, une colonne par caracteristique cic_schema
    (jamais Header, qui n'est pas dans COLONNE_REELLE -- voir
    nettoyer_colonne_header_seule ci-dessous pour l'analyse dediee)."""
    import pandas as pd
    valeurs, statuts, hexcodes = {}, {}, {}
    for feat, col in COLONNE_REELLE.items():
        resultats = nettoyer_colonne(feat, df[col].tolist())
        valeurs[feat] = [r.valeur for r in resultats]
        statuts[feat] = [r.statut for r in resultats]
        hexcodes[feat] = [r.hexcode_count for r in resultats]
    return (pd.DataFrame(valeurs, index=df.index),
            pd.DataFrame(statuts, index=df.index),
            pd.DataFrame(hexcodes, index=df.index))


def nettoyer_colonne_header_seule(df):
    """Variante dediee pour 'Header' seul (colonne exclue du sous-ensemble
    d'entrainement, voir EXCLU_HEADER_RAISON) -- utilisee uniquement par
    l'analyse de qualite des donnees, jamais par nettoyer_dataframe()."""
    import pandas as pd
    resultats = [nettoyer_valeur_header(v) for v in df["Header"].tolist()]
    return (pd.Series([r.valeur for r in resultats], index=df.index, name="header_present"),
            pd.Series([r.statut for r in resultats], index=df.index, name="header_present"))


def calculer_diagnostics(df_statuts):
    """Caracteristiques de diagnostic AGREGEES (nombre de champs
    manquants/invalides par ligne) -- reservees a l'analyse de qualite des
    donnees (cahier des charges §4). ATTENTION : ces colonnes NE DOIVENT
    JAMAIS etre ajoutees au vecteur d'entrainement Random Forest. La
    corruption/l'absence d'extraction est fortement correlee a l'etiquette
    Malicious (voir CIC-PDF-DATA-QUALITY.md) : les inclure creerait une
    fuite de cible / un raccourci d'apprentissage (le modele apprendrait a
    detecter "l'extraction a echoue" plutot qu'un signal structurel reel du
    PDF), pas une caracteristique legitime.

    Important : le statut "compose_malforme" N'EST PAS compte comme
    manquant/invalide ici -- une cellule "N(M)" produit une valeur N
    reellement utilisee pour l'entrainement (voir
    nettoyer_valeur_texte_comptage), ce n'est pas un echec d'extraction,
    seulement un format texte inhabituel. `invalid_field_count` ne compte
    que les cellules dont la valeur finale est reellement absente
    ("texte_fuite", "autre_invalide")."""
    import pandas as pd
    est_manquant = df_statuts.eq("manquant_sentinelle")
    est_invalide = df_statuts.isin(["texte_fuite", "autre_invalide"])
    missing_field_count = est_manquant.sum(axis=1)
    invalid_field_count = est_invalide.sum(axis=1)
    return pd.DataFrame({
        "missing_field_count": missing_field_count,
        "invalid_field_count": invalid_field_count,
        "extraction_failed": ((missing_field_count + invalid_field_count) > 0).astype(int),
    }, index=df_statuts.index)
