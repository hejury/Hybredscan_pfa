#!/usr/bin/env python3
"""cic_features.py — Extracteur CIC-compatible (sous-ensemble defensible).

Meme discipline de securite que document_ml/pdf/features.py (le module
existant, NON modifie par cette tache) : lecture d'octets bruts, comptage
par expression reguliere/sous-chaine, JAMAIS de rendu, JAMAIS d'execution
de JavaScript, JAMAIS de suivi de lien, JAMAIS de decompression de flux
(voir validation/CIC-PDF-FEATURE-COMPATIBILITY.md §3 : le code source de
pdfid.py, l'outil que CIC declare avoir utilise pour ses caracteristiques
structurelles, confirme qu'il ne decompresse jamais non plus — cet
extracteur suit deliberement la meme methode pour rester comparable).

Ce module est INDEPENDANT de features.py. Il n'est importe par rien
d'existant (analyze.py, predict.py, train.py, evaluate.py restent
inchanges par cette tache)."""
import math
import re

from .cic_schema import CIC_FEATURES

# --- Jetons de base PDFiD (lus directement dans le code source de l'outil,
# voir CIC-PDF-FEATURE-COMPATIBILITY.md §3) — comptage par sous-chaine
# litterale, exactement comme pdfid.py, jamais une regex plus permissive
# qui divergerait de sa semantique. ------------------------------------
_MOTS_CLES_SIMPLES = {
    "nb_stream_kw": b"stream",
    "nb_endstream_kw": b"endstream",
    "nb_objstm_kw": b"/ObjStm",
    "nb_trailer_kw": b"trailer",
    "nb_xref_kw": b"xref",
    "nb_startxref_kw": b"startxref",
    "nb_embeddedfile_kw": b"/EmbeddedFile",
    "nb_js_kw": b"/JS",
    "nb_javascript_kw": b"/JavaScript",
    "nb_aa_kw": b"/AA",
    "nb_openaction_kw": b"/OpenAction",
    "nb_launch_kw": b"/Launch",
    "nb_acroform_kw": b"/AcroForm",
    "nb_xfa_kw": b"/XFA",
    "nb_jbig2decode_kw": b"/JBIG2Decode",
    "nb_richmedia_kw": b"/RichMedia",
}

_RE_OBJ = re.compile(rb"\d+\s+\d+\s+obj\b")
# /Page keyword count, style PDFiD (voir cic_schema.CIC_FEATURE_DOC pour
# nb_page_approx) : PDFiD tokenise sur les delimiteurs PDF et compte les
# occurrences du NOM '/Page' lui-meme, pas uniquement celles precedees de
# '/Type' — \b apres "Page" exclut correctement '/Pages' (le tiret bas
# n'existe pas ici, mais 's' est un caractere de mot, donc pas de frontiere
# entre 'e' et 's' : '/Pages' ne matche jamais ce motif).
_RE_PAGE_KW = re.compile(rb"/Page\b")


def extraire_caracteristiques_cic(path):
    """Extraction statique, SANS rendu ni execution du PDF — sous-ensemble
    de 18 caracteristiques CIC-Evasive-PDFMal2022 classees A/B (voir
    CIC-PDF-FEATURE-COMPATIBILITY.md, CIC-PDF-DATA-QUALITY.md et
    CIC-PDF-ANTI-LEAKAGE.md ; "Header" retire en v2, "is_encrypted" retire
    en v3, "pdf_size" retire en v4 (ecart d'echelle octets/kilo-octets
    decouvert lors des tests d'integration reels, voir
    PDF-RUNTIME-FIDELITY.md) — voir cic_schema.CIC_FEATURES_EXCLUES_DONNEES_REELLES).
    Retourne un dict conforme a cic_schema.CIC_FEATURES, ou
    {"_erreur": "..."} si le fichier est illisible/vide — jamais
    d'exception qui remonte a l'appelant (meme convention defensive que
    document_ml.pdf.features.extraire_features_pdf et
    analyze.extraire_features pour les PE)."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except Exception as e:
        return {"_erreur": str(e)}
    if not data:
        return {"_erreur": "fichier vide"}

    f = {}
    f["nb_stream_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_stream_kw"])
    f["nb_endstream_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_endstream_kw"])
    f["nb_objstm_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_objstm_kw"])
    f["nb_trailer_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_trailer_kw"])
    f["nb_xref_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_xref_kw"])
    f["nb_startxref_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_startxref_kw"])
    f["nb_obj_kw"] = len(_RE_OBJ.findall(data))
    f["nb_page_approx"] = len(_RE_PAGE_KW.findall(data))
    f["nb_embeddedfile_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_embeddedfile_kw"])
    f["nb_js_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_js_kw"])
    f["nb_javascript_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_javascript_kw"])
    f["nb_aa_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_aa_kw"])
    f["nb_openaction_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_openaction_kw"])
    f["nb_launch_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_launch_kw"])
    f["nb_acroform_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_acroform_kw"])
    f["nb_xfa_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_xfa_kw"])
    f["nb_jbig2decode_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_jbig2decode_kw"])
    f["nb_richmedia_kw"] = data.count(_MOTS_CLES_SIMPLES["nb_richmedia_kw"])

    assert list(f.keys()) == list(CIC_FEATURES), "cic_features.py/cic_schema.py: ordre desynchronise"
    return f
