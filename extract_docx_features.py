import os
import re
import math
import zipfile


SUSPICIOUS_EXTENSIONS = {
    ".exe", ".dll", ".scr", ".bat", ".cmd",
    ".ps1", ".vbs", ".js", ".hta", ".msi"
}


def entropy(data):
    if not data:
        return 0.0

    freq = [0] * 256

    for b in data:
        freq[b] += 1

    result = 0.0

    for count in freq:
        if count:
            p = count / len(data)
            result -= p * math.log2(p)

    return result


def extract_docx_features(path):
    features = {}

    # ---------------------------------------------------------
    # Basic file information
    # ---------------------------------------------------------

    features["file_size"] = os.path.getsize(path)

    with open(path, "rb") as f:
        raw = f.read()

    features["entropy"] = round(entropy(raw), 6)

    # ---------------------------------------------------------
    # Validate DOCX / ZIP
    # ---------------------------------------------------------

    if not zipfile.is_zipfile(path):
        raise ValueError("Not a valid DOCX/ZIP file")

    with zipfile.ZipFile(path, "r") as z:

        names = z.namelist()

        # -----------------------------------------------------
        # ZIP / OOXML structure
        # -----------------------------------------------------

        features["zip_file_count"] = len(names)

        features["has_content_types"] = int(
            "[Content_Types].xml" in names
        )

        features["has_document_xml"] = int(
            "word/document.xml" in names
        )

        features["has_settings_xml"] = int(
            "word/settings.xml" in names
        )

        features["has_styles_xml"] = int(
            "word/styles.xml" in names
        )

        # -----------------------------------------------------
        # Embedded objects
        # -----------------------------------------------------

        embedded = [
            n for n in names
            if n.lower().startswith("word/embeddings/")
        ]

        features["embedded_object_count"] = len(embedded)

        features["embedded_ole_count"] = sum(
            1
            for n in embedded
            if n.lower().endswith(".bin")
            or "oleobject" in n.lower()
        )

        # -----------------------------------------------------
        # Relationship files
        # -----------------------------------------------------

        relationship_files = [
            n for n in names
            if n.lower().endswith(".rels")
        ]

        features["relationship_file_count"] = len(
            relationship_files
        )

        external_relationships = 0
        external_templates = 0
        hyperlinks = 0
        suspicious_relationships = 0

        # -----------------------------------------------------
        # Analyze relationships
        # -----------------------------------------------------

        for name in relationship_files:

            try:
                data = z.read(name)
            except Exception:
                continue

            lower_data = data.lower()

            # External relationship
            external_relationships += lower_data.count(
                b'targetmode="external"'
            )

            # External template relationship
            external_templates += lower_data.count(
                b"attachedtemplate"
            )

            # Real hyperlink relationship
            hyperlinks += lower_data.count(
                b'type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"'
            )

            # Suspicious OLE relationship
            suspicious_relationships += lower_data.count(
                b"oleobject"
            )

        features["external_relationship_count"] = (
            external_relationships
        )

        features["external_template_count"] = (
            external_templates
        )

        features["hyperlink_count"] = hyperlinks

        features["suspicious_relationship_count"] = (
            suspicious_relationships
        )

        # -----------------------------------------------------
        # URLs
        # -----------------------------------------------------

        url_count = 0

        for name in relationship_files:

            try:
                data = z.read(name)
            except Exception:
                continue

            urls = re.findall(
                rb'https?://[^\s"<>]+',
                data,
                re.IGNORECASE
            )

            url_count += len(urls)

        features["url_count"] = url_count

        # -----------------------------------------------------
        # Suspicious embedded file extensions
        # -----------------------------------------------------

        suspicious_files = 0

        for name in names:

            lower = name.lower()

            _, ext = os.path.splitext(lower)

            if ext in SUSPICIOUS_EXTENSIONS:
                suspicious_files += 1

        features["suspicious_extension_count"] = (
            suspicious_files
        )

        # -----------------------------------------------------
        # XML / OOXML structure
        # -----------------------------------------------------

        xml_files = [
            n for n in names
            if n.lower().endswith(".xml")
        ]

        rels_files = [
            n for n in names
            if n.lower().endswith(".rels")
        ]

        features["xml_file_count"] = len(xml_files)

        features["rels_file_count"] = len(rels_files)

        features["total_xml_size"] = sum(
            z.getinfo(n).file_size
            for n in xml_files
        )

        # -----------------------------------------------------
        # Suspicious OOXML indicators
        # -----------------------------------------------------

        all_xml = b""

        for name in names:

            if not (
                name.lower().endswith(".xml")
                or name.lower().endswith(".rels")
            ):
                continue

            try:
                all_xml += z.read(name)
            except Exception:
                continue

        lower_xml = all_xml.lower()

        features["keyword_targetmode_external"] = (
            lower_xml.count(
                b'targetmode="external"'
            )
        )

        features["keyword_attachedtemplate"] = (
            lower_xml.count(
                b"attachedtemplate"
            )
        )

        features["keyword_oleobject"] = (
            lower_xml.count(
                b"oleobject"
            )
        )

        features["keyword_external"] = (
            lower_xml.count(
                b"external"
            )
        )

        features["keyword_cmd_exe"] = (
            lower_xml.count(
                b"cmd.exe"
            )
        )

        features["keyword_powershell"] = (
            lower_xml.count(
                b"powershell"
            )
        )

        features["keyword_ms_msdt"] = (
            lower_xml.count(
                b"ms-msdt:"
            )
        )

        features["keyword_file"] = (
            lower_xml.count(
                b"file://"
            )
        )

    return features


if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python extract_docx_features.py file.docx"
        )
        raise SystemExit(1)

    path = sys.argv[1]

    features = extract_docx_features(path)

    print("\nDOCX FEATURES")
    print("=" * 60)

    for key, value in features.items():
        print(f"{key:40s}: {value}")