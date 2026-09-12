#!/usr/bin/env python3
"""features.py — Extraction statique de caracteristiques DOCX (document_ml.docx).

Extraction PUREMENT statique et defensive :
  - metadonnee d'archive ZIP (noms/tailles d'entrees) via validate.py ;
  - texte brut de parties '*.rels' et '[Content_Types].xml', jamais parse
    comme XML executable (recherche par expression reguliere sur le texte,
    la meme discipline que document_ml/pdf/features.py) ;
  - macros VBA via oletools.olevba.VBA_Parser -- une bibliotheque d'analyse
    STATIQUE (decompilation de p-code/tokenisation), jamais un interpreteur
    VBA : aucune macro n'est executee a aucun moment ;
  - liens DDE via oletools.msodde -- egalement statique.

Aucune relation externe n'est resolue/suivie. Aucun objet integre n'est
extrait sur disque ni ouvert. Aucun processus n'est lance (jamais de
PowerShell/cmd/wscript/cscript/Office).

Toute erreur d'extraction (fichier illisible, VBA_Parser en echec sur un
conteneur pourtant valide, etc.) retourne {"_erreur": "..."} -- JAMAIS une
valeur fabriquee (0 = sain, 1 = malveillant). Voir validation/DOCX-FEATURES.md."""
import math
import re

from .schema import FEATURES
from .validate import valider_docx, lire_partie_texte, PREFIXE_EMBEDDINGS, PREFIXE_ACTIVEX

_EXTENSIONS_EXECUTABLE_LIKE = (".exe", ".scr", ".bat", ".cmd", ".vbs", ".js", ".jar", ".ps1", ".dll")

_MOTS_CLES_AUTOEXEC = ("autoopen", "document_open", "document_close", "autoclose")
_MOTS_CLES_SUSPECTS = ("powershell", "cmd.exe", "wscript", "cscript", "mshta", "rundll32",
                        "regsvr32", "certutil", "bitsadmin", "shell", "createobject")

_RE_RELATIONSHIP = re.compile(rb"<Relationship\b")
_RE_TARGET_EXTERNAL = re.compile(rb'TargetMode\s*=\s*"External"', re.IGNORECASE)
_RE_TYPE_HYPERLINK = re.compile(rb'Type\s*=\s*"[^"]*hyperlink[^"]*"', re.IGNORECASE)
_RE_TYPE_ATTACHED_TEMPLATE = re.compile(rb'Type\s*=\s*"[^"]*attachedTemplate[^"]*"', re.IGNORECASE)
_RE_TYPE_OLEOBJECT = re.compile(rb'Type\s*=\s*"[^"]*oleObject[^"]*"', re.IGNORECASE)
_RE_TARGET_URL = re.compile(rb'Target\s*=\s*"(https?://[^"]*)"', re.IGNORECASE)
_RE_OVERRIDE = re.compile(rb"<Override\b")
_RE_BASE64_LONG = re.compile(r"[A-Za-z0-9+/]{40,}")


def _entropie(texte):
    """Entropie de Shannon (bits) sur une chaine ; 0.0 pour une chaine
    vide -- une valeur reelle, pas une valeur fabriquee en absence de
    macro (voir schema.FEATURE_DOC['vba_source_entropy'])."""
    if not texte:
        return 0.0
    data = texte.encode("utf-8", errors="replace")
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    n = len(data)
    e = 0.0
    for c in freq.values():
        p = c / n
        e -= p * math.log2(p)
    return e


def _entropie_caracteres(texte):
    """Entropie de Shannon (bits/CARACTERE, pas bits/octet) sur une chaine
    Python -- reproduction prouvee, fidele au caractere pres, de
    calculate_entropy() dans le notebook officiel CIC-Trap4Phish
    (Counter(text) sur une chaine str, jamais sur des octets encodes).
    Utilisee UNIQUEMENT par xml_text_entropy -- ne pas reutiliser pour
    vba_source_entropy, qui reste sciemment une entropie sur octets
    (_entropie ci-dessus, inchangee)."""
    if not texte:
        return 0.0
    freq = {}
    for c in texte:
        freq[c] = freq.get(c, 0) + 1
    n = len(texte)
    e = 0.0
    for compte in freq.values():
        p = compte / n
        e -= p * math.log2(p)
    return e


def _extraire_vba(path):
    """Extraction STATIQUE du source VBA (jamais execute) via oletools.
    Retourne (a_macros: bool, nb_modules: int, source_concatene: str,
    erreur: str|None). N'echoue jamais par exception -- une erreur
    oletools sur un conteneur pourtant valide est rapportee, pas masquee
    en '0 macro'."""
    try:
        from oletools.olevba import VBA_Parser
    except Exception as e:
        return False, 0, "", "oletools indisponible : %s" % e

    try:
        vba = VBA_Parser(path)
    except Exception as e:
        return False, 0, "", "VBA_Parser a echoue a l'ouverture : %s" % e

    try:
        a_macros = bool(vba.detect_vba_macros())
        modules = []
        if a_macros:
            try:
                for (_fichier, _flux, _nom_vba, code) in vba.extract_macros():
                    if code:
                        modules.append(code)
            except Exception as e:
                # Detection positive mais extraction du source impossible :
                # on le signale plutot que de fabriquer un source vide.
                return True, 0, "", "extraction du source VBA a echoue : %s" % e
        return a_macros, len(modules), "\n".join(modules), None
    finally:
        try:
            vba.close()
        except Exception:
            pass


def _detecter_dde(path):
    """Detection STATIQUE de liens DDE/DDEAUTO via oletools.msodde. Ne
    suit jamais le lien -- se contente de signaler sa presence textuelle
    dans le document. Retourne (a_dde: bool, erreur: str|None)."""
    try:
        from oletools import msodde
    except Exception as e:
        return False, "msodde indisponible : %s" % e
    try:
        resultat = msodde.process_file(path)
        return bool(resultat and str(resultat).strip()), None
    except Exception as e:
        return False, "msodde a echoue : %s" % e


def extraire_features_docx(path):
    """Extraction statique complete, SANS rendu ni execution du DOCX.
    Retourne un dict conforme a schema.FEATURES, ou {"_erreur": "..."} si
    le fichier n'est pas un DOCX structurellement valide ou si
    l'extraction echoue -- jamais d'exception qui remonte a l'appelant."""
    resultat = valider_docx(path)
    if not resultat.valide:
        return {"_erreur": resultat.motif_invalide}

    entrees = resultat.entrees
    ind = resultat.indicateurs

    f = {}

    # --- Structure generale ---------------------------------------------
    try:
        import os
        f["file_size_bytes"] = os.path.getsize(path)
    except Exception as e:
        return {"_erreur": "taille de fichier illisible : %s" % e}
    f["zip_entry_count"] = len(entrees)
    f["xml_entry_count"] = sum(1 for n in entrees if n.endswith(".xml"))
    f["rels_entry_count"] = sum(1 for n in entrees if n.endswith(".rels"))
    f["has_core_properties"] = 1 if ind["a_core_properties"] else 0
    f["has_app_properties"] = 1 if ind["a_app_properties"] else 0
    f["has_custom_properties"] = 1 if ind["a_custom_properties"] else 0
    content_types_texte = lire_partie_texte(path, "[Content_Types].xml").encode("utf-8", errors="replace")
    f["nb_content_types_overrides"] = len(_RE_OVERRIDE.findall(content_types_texte))
    f["has_customxml"] = 1 if ind["a_customxml"] else 0

    # --- Macros / VBA (jamais executees) --------------------------------
    a_macros, nb_modules, source_vba, err_vba = _extraire_vba(path)
    if err_vba:
        return {"_erreur": err_vba}
    f["has_vba_macros"] = 1 if a_macros else 0
    f["nb_vba_modules"] = nb_modules
    f["vba_source_length"] = len(source_vba)
    source_vba_min = source_vba.lower()
    nb_autoexec = sum(1 for kw in _MOTS_CLES_AUTOEXEC if kw in source_vba_min)
    f["nb_autoexec_keywords"] = nb_autoexec
    f["has_any_autoexec"] = 1 if nb_autoexec > 0 else 0

    # --- Relations OOXML (texte brut, jamais suivies) -------------------
    rels_texte = b""
    for nom in entrees:
        if nom.endswith(".rels"):
            rels_texte += lire_partie_texte(path, nom).encode("utf-8", errors="replace") + b"\n"
    f["nb_relationships_total"] = len(_RE_RELATIONSHIP.findall(rels_texte))
    f["nb_relationships_external"] = len(_RE_TARGET_EXTERNAL.findall(rels_texte))
    f["nb_hyperlink_relationships"] = len(_RE_TYPE_HYPERLINK.findall(rels_texte))
    f["has_attached_template"] = 1 if _RE_TYPE_ATTACHED_TEMPLATE.search(rels_texte) else 0
    f["nb_remote_targets_rels"] = len(_RE_TARGET_URL.findall(rels_texte))
    f["has_oleobject_relationship"] = 1 if _RE_TYPE_OLEOBJECT.search(rels_texte) else 0

    # --- Contenu integre (metadonnee d'archive uniquement) --------------
    f["has_embeddings_dir"] = 1 if ind["a_embeddings"] else 0
    f["embedded_entry_count"] = sum(1 for n in entrees if n.startswith(PREFIXE_EMBEDDINGS))
    f["has_activex"] = 1 if ind["a_activex"] else 0
    f["nb_executable_like_embedded_names"] = sum(
        1 for n in entrees
        if (n.startswith(PREFIXE_EMBEDDINGS) or n.startswith(PREFIXE_ACTIVEX))
        and n.lower().endswith(_EXTENSIONS_EXECUTABLE_LIKE)
    )

    # --- Chaines suspectes / DDE / obfuscation (source VBA uniquement) --
    f["nb_suspicious_strings"] = sum(source_vba_min.count(kw) for kw in _MOTS_CLES_SUSPECTS)
    f["nb_url_like_strings"] = source_vba_min.count("http://") + source_vba_min.count("https://")
    a_dde, err_dde = _detecter_dde(path)
    if err_dde:
        return {"_erreur": err_dde}
    f["has_dde"] = 1 if a_dde else 0
    f["nb_long_base64_tokens"] = len(_RE_BASE64_LONG.findall(source_vba))
    f["vba_source_entropy"] = round(_entropie(source_vba), 4)

    # --- xml_text_entropy (v2) -- reproduction prouvee du notebook CIC ---
    xml_texte_concat = "".join(
        lire_partie_texte(path, nom) for nom in entrees if nom.endswith(".xml")
    )
    f["xml_text_entropy"] = round(_entropie_caracteres(xml_texte_concat), 4)

    assert set(f) == set(FEATURES), "features.py/schema.py desynchronises"
    return {k: f[k] for k in FEATURES}
