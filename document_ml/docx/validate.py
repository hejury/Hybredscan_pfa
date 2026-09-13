#!/usr/bin/env python3
"""validate.py — Validation structurelle DOCX (document_ml.docx).

DOCX est un conteneur ZIP (format OOXML). Ce module verifie qu'un fichier
declare ".docx" correspond reellement a cette structure, SANS jamais :
  - executer le document ;
  - ouvrir Microsoft Word ;
  - executer une macro VBA ;
  - suivre une relation externe (URL, template distant) ;
  - lancer PowerShell/cmd/wscript/cscript/Office.

Seules les METADONNEES du conteneur ZIP (table centrale : noms d'entrees,
tailles) et le texte brut de quelques fichiers XML internes (jamais
interprete comme du XML executable, jamais de resolution d'entite externe)
sont lus. Aucune extraction sur disque, aucune decompression au-dela de ce
qui est strictement necessaire pour lire un flux en memoire.

Un simple ZIP quelconque renomme .docx, ou un fichier texte renomme .docx,
ne doit PAS etre accepte comme un DOCX valide -- voir valider_docx() plus
bas, qui verifie explicitement la presence des parties OOXML attendues,
pas seulement la signature ZIP."""
import re
import zipfile

# Parties OOXML minimales attendues dans un document Word valide. Une
# archive ZIP quelconque (ex. un .zip renomme .docx) n'aura presque
# certainement ni l'une ni l'autre -- exiger LES DEUX (pas seulement la
# signature ZIP) est ce qui distingue un vrai DOCX d'un conteneur ZIP
# arbitraire.
PARTIE_CONTENT_TYPES = "[Content_Types].xml"
PARTIE_DOCUMENT = "word/document.xml"

# Sous-repertoires/parties dont la seule PRESENCE (jamais le contenu
# execute) est un indicateur de securite pertinent (cahier des charges §3).
PREFIXE_VBA = "word/vbaProject.bin"
PREFIXE_EMBEDDINGS = "word/embeddings/"
PREFIXE_ACTIVEX = "word/activeX/"
PREFIXE_CUSTOMXML = "customXml/"
PARTIE_RELS_DOCUMENT = "word/_rels/document.xml.rels"
PARTIE_RELS_RACINE = "_rels/.rels"
PARTIE_CORE_PROPS = "docProps/core.xml"
PARTIE_APP_PROPS = "docProps/app.xml"
PARTIE_CUSTOM_PROPS = "docProps/custom.xml"


def _entete_brute(path, n):
    """Lit uniquement les `n` premiers octets -- jamais le fichier entier,
    jamais une ouverture/execution."""
    try:
        with open(path, "rb") as fh:
            return fh.read(n)
    except Exception:
        return b""


def a_signature_zip(path):
    """Vrai si le fichier commence par une signature ZIP locale
    (PK\\x03\\x04) ou une archive ZIP vide (PK\\x05\\x06). Necessaire mais
    PAS suffisant pour etre un DOCX valide -- voir valider_docx()."""
    e = _entete_brute(path, 4)
    return e == b"PK\x03\x04" or e == b"PK\x05\x06"


class ResultatValidation:
    """Resultat de valider_docx().

    - `valide` : bool -- structure OOXML minimale confirmee.
    - `motif_invalide` : str|None -- raison si `valide` est False.
    - `entrees` : liste des noms d'entrees ZIP (table centrale uniquement,
      jamais le contenu decompresse), ou [] si le ZIP n'a pas pu etre ouvert.
    - `indicateurs` : dict de booleens/compteurs derives UNIQUEMENT des noms
      d'entrees (metadonnee d'archive) -- jamais du contenu."""
    __slots__ = ("valide", "motif_invalide", "entrees", "indicateurs")

    def __init__(self, valide, motif_invalide, entrees, indicateurs):
        self.valide = valide
        self.motif_invalide = motif_invalide
        self.entrees = entrees
        self.indicateurs = indicateurs


def valider_docx(path):
    """Validation structurelle complete d'un fichier declare .docx.

    Etapes, dans l'ordre :
      1. Signature ZIP presente en tete de fichier.
      2. Le fichier s'ouvre reellement comme une archive ZIP (rejette un
         ZIP tronque/corrompu).
      3. `[Content_Types].xml` present.
      4. `word/document.xml` present.

    Un fichier qui echoue a n'importe laquelle de ces etapes est INVALIDE
    -- jamais traite comme un DOCX authentique meme s'il porte l'extension.
    Ne leve jamais d'exception ; retourne toujours un ResultatValidation."""
    if not a_signature_zip(path):
        return ResultatValidation(False, "signature ZIP absente", [], {})

    try:
        with zipfile.ZipFile(path) as z:
            entrees = z.namelist()
    except (zipfile.BadZipFile, OSError, NotImplementedError) as e:
        return ResultatValidation(False, "archive ZIP illisible/corrompue : %s" % e, [], {})

    if PARTIE_CONTENT_TYPES not in entrees:
        return ResultatValidation(False, "'[Content_Types].xml' absent", entrees, {})
    if PARTIE_DOCUMENT not in entrees:
        return ResultatValidation(False, "'word/document.xml' absent", entrees, {})

    indicateurs = {
        "a_vba": PREFIXE_VBA in entrees,
        "a_embeddings": any(n.startswith(PREFIXE_EMBEDDINGS) for n in entrees),
        "a_activex": any(n.startswith(PREFIXE_ACTIVEX) for n in entrees),
        "a_customxml": any(n.startswith(PREFIXE_CUSTOMXML) for n in entrees),
        "a_rels_document": PARTIE_RELS_DOCUMENT in entrees,
        "a_rels_racine": PARTIE_RELS_RACINE in entrees,
        "a_core_properties": PARTIE_CORE_PROPS in entrees,
        "a_app_properties": PARTIE_APP_PROPS in entrees,
        "a_custom_properties": PARTIE_CUSTOM_PROPS in entrees,
    }
    return ResultatValidation(True, None, entrees, indicateurs)


def lire_partie_texte(path, nom_partie, limite_octets=1_000_000):
    """Lit UNE partie interne du conteneur ZIP comme texte brut (jamais
    parsee comme XML, jamais interpretee/executee) -- utilise par
    features.py pour l'analyse des fichiers .rels. Retourne "" si la
    partie est absente ou illisible (jamais une exception). `limite_octets`
    borne la lecture (defense en profondeur contre une entree ZIP
    anormalement volumineuse -- BF §3 : lecture seule, jamais de
    decompression non bornee)."""
    try:
        with zipfile.ZipFile(path) as z:
            info = z.getinfo(nom_partie)
            if info.file_size > limite_octets:
                return ""
            with z.open(nom_partie) as fh:
                return fh.read(limite_octets).decode("utf-8", errors="replace")
    except (KeyError, zipfile.BadZipFile, OSError):
        return ""
