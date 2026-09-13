#!/usr/bin/env python3
"""docx_fixtures.py — Fixtures DOCX synthetiques partagees par les tests.

Toutes les fixtures sont construites localement avec `zipfile`, a partir de
constantes XML minimales ecrites dans ce fichier. AUCUN fichier n'est
telecharge, AUCUN echantillon de malware reel n'est utilise. Voir
validation/DOCX-FEATURES.md §6 pour la limite connue de cette approche
(un flux vbaProject.bin reellement decompilable par oletools n'est pas
reproduit ici — cf. MS-OVBA, hors perimetre)."""
import zipfile

CONTENT_TYPES_MIN = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

DOCUMENT_MIN = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:r><w:t>Hello world</w:t></w:r></w:p></w:body>
</w:document>"""

ROOT_RELS_MIN = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOC_RELS_EXTERNAL = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/attachedTemplate" Target="http://example-remote-host.test/normal.dotm" TargetMode="External"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.test/page" TargetMode="External"/>
</Relationships>"""


def build_minimal_docx(path, extra_entries=None, doc_rels=ROOT_RELS_MIN,
                        content_types=CONTENT_TYPES_MIN, document_xml=DOCUMENT_MIN,
                        include_core_app_props=True):
    """Construit un DOCX minimal structurellement valide. `extra_entries`
    (dict nom -> bytes) permet d'ajouter des parties supplementaires (VBA,
    embeddings, activeX, etc.) sans dupliquer la logique de base."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", ROOT_RELS_MIN)
        z.writestr("word/document.xml", document_xml)
        if include_core_app_props:
            z.writestr("docProps/core.xml", b"<coreProperties/>")
            z.writestr("docProps/app.xml", b"<Properties/>")
        if doc_rels is not None:
            z.writestr("word/_rels/document.xml.rels", doc_rels)
        if extra_entries:
            for name, data in extra_entries.items():
                z.writestr(name, data)
    return path


def build_plain_zip(path, entries=None):
    """ZIP valide mais sans aucune partie OOXML attendue — simule un .zip
    quelconque renomme .docx."""
    with zipfile.ZipFile(path, "w") as z:
        for name, data in (entries or {"readme.txt": b"just a zip file"}).items():
            z.writestr(name, data)
    return path


def build_plain_text(path, content=b"This is plain text, not a zip file at all."):
    with open(path, "wb") as fh:
        fh.write(content)
    return path


def build_truncated_zip(path):
    """En-tete ZIP valide mais donnees corrompues/tronquees ensuite."""
    with open(path, "wb") as fh:
        fh.write(b"PK\x03\x04" + b"\x00" * 10)
    return path


def build_fake_pe(path):
    """Un veritable en-tete PE (MZ) renomme .docx — doit etre rejete par
    validate.py (signature ZIP absente), pas par une detection PE."""
    with open(path, "wb") as fh:
        fh.write(b"MZ" + b"\x90" * 62 + b"\x00" * 100)
    return path
