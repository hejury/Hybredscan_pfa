#!/usr/bin/env python3
"""features.py — Extraction statique de caracteristiques PDF (document_ml.pdf).

Extraction PUREMENT statique : lecture des octets bruts du fichier et
comptage par expression reguliere. Choix delibere de ne PAS invoquer de
bibliotheque de parsing/rendu PDF (ex. pypdf, PyMuPDF) sur une entree
potentiellement hostile — un parseur PDF complet est lui-meme une surface
d'attaque (CVE historiques dans plusieurs bibliotheques PDF). Le comptage
par motif s'applique au contenu brut, y compris a l'interieur des flux
compresses NON decompresses : cela sous-estime legerement certains
comptages (un jeton '/JavaScript' a l'interieur d'un flux Deflate compresse
n'est pas retrouve par une simple recherche texte), mais ne necessite jamais
de decompresser (donc jamais d'executer un decompresseur sur une entree
hostile) ni de parser la structure d'objets PDF.

Aucun rendu. Aucune execution de JavaScript. Aucun lien suivi. Aucun fichier
integre extrait ou ouvert.
"""
import math
import re

from .schema import FEATURES

_RE_VERSION = re.compile(rb"%PDF-(\d\.\d)")
_RE_OBJ = re.compile(rb"\d+\s+\d+\s+obj\b")
_RE_PAGE = re.compile(rb"/Type\s*/Page\b")
_RE_JS = re.compile(rb"/JS\b")
_RE_AA = re.compile(rb"/AA\b")
_RE_URI = re.compile(rb"/URI\b")
_RE_OBFUSCATED_NAME = re.compile(rb"/[A-Za-z0-9]*#[0-9A-Fa-f]{2}")


def _entropie(data):
    """Entropie de Shannon (en bits) sur une sequence d'octets."""
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    n = len(data)
    e = 0.0
    for c in freq:
        if c:
            p = c / n
            e -= p * math.log2(p)
    return e


def extraire_features_pdf(path):
    """Extraction statique, SANS rendu ni execution du PDF.

    Retourne un dict conforme a `schema.FEATURES`, ou {"_erreur": "..."} si
    le fichier est illisible ou vide — jamais d'exception qui remonte a
    l'appelant (meme convention defensive que analyze.extraire_features
    pour les PE)."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except Exception as e:
        return {"_erreur": str(e)}
    if not data:
        return {"_erreur": "fichier vide"}

    f = {}
    f["file_size"] = len(data)
    f["entropy"] = round(_entropie(data), 4)

    m = _RE_VERSION.search(data[:2048])
    f["pdf_version"] = float(m.group(1)) if m else 0.0

    f["nb_obj"] = len(_RE_OBJ.findall(data))
    f["nb_endobj"] = data.count(b"endobj")
    f["nb_stream"] = data.count(b"stream")
    f["nb_endstream"] = data.count(b"endstream")
    f["obj_stream_ratio"] = round(f["nb_stream"] / max(f["nb_obj"], 1), 4)
    f["nb_page"] = len(_RE_PAGE.findall(data))

    f["has_javascript"] = 1 if b"/JavaScript" in data else 0
    f["has_js"] = 1 if _RE_JS.search(data) else 0
    f["has_openaction"] = 1 if b"/OpenAction" in data else 0
    f["has_aa"] = 1 if _RE_AA.search(data) else 0
    f["has_launch"] = 1 if b"/Launch" in data else 0
    f["nb_uri"] = len(_RE_URI.findall(data))
    f["has_embeddedfile"] = 1 if b"/EmbeddedFile" in data else 0
    f["has_acroform"] = 1 if b"/AcroForm" in data else 0
    f["has_xfa"] = 1 if b"/XFA" in data else 0
    f["nb_suspicious_actions"] = (f["has_openaction"] + f["has_aa"] + f["has_launch"]
                                   + f["has_javascript"] + f["has_js"])
    f["has_encryption"] = 1 if b"/Encrypt" in data else 0
    f["nb_obfuscated_names"] = len(_RE_OBFUSCATED_NAME.findall(data))

    assert set(f) == set(FEATURES), "features.py/schema.py desynchronises"
    return f
