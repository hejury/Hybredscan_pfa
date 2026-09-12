#!/usr/bin/env python3
"""test_quarantine_manager.py — Tests du module centralise quarantine_manager.py
et de son integration dans analyze.py (QUARANTINE MVP).

Execution : python3 tests/test_quarantine_manager.py

Toutes les fixtures sont synthetiques et inoffensives (jamais de malware
reel). Chaque test opere dans un repertoire temporaire isole -- jamais le
quarantine/ reel du depot. Aucun contenu mis en quarantaine n'est jamais
ouvert/execute par ces tests."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import quarantine_manager as qm


def _fichier(tmp, nom, contenu=b"contenu synthetique inoffensif"):
    p = os.path.join(tmp, nom)
    with open(p, "wb") as fh:
        fh.write(contenu)
    return p


def _analyze_isole(tmp):
    os.environ.pop("VT_API_KEY", None)
    os.environ["HYBRIDSCAN_BASE_DIR"] = tmp
    for mod in list(sys.modules):
        if mod.startswith("document_ml") or mod in ("analyze",):
            del sys.modules[mod]
    import analyze
    return analyze


# --- 1/2/3/4/5/6/7 : quarantine_file() de base -------------------------

def test_local_path_moved_when_authorized(tmp):
    """1. Un fichier synthetique 'malveillant' est deplace en quarantaine
    quand un vrai chemin local est disponible et que la politique
    l'autorise."""
    p = _fichier(tmp, "malware.exe")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    assert meta["status"] == qm.STATUT_BLOQUE
    dest = os.path.join(tmp, "quarantine", meta["quarantine_storage_name"])
    assert os.path.isfile(dest)


def test_source_disappears_after_move(tmp):
    """2. Le fichier source n'existe plus a son chemin d'origine apres
    une mise en quarantaine reussie."""
    p = _fichier(tmp, "malware2.exe")
    qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                       source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    assert not os.path.exists(p)


def test_opaque_storage_name(tmp):
    """3. Le nom de stockage est opaque (UUID + '.quarantine'), jamais le
    nom original."""
    p = _fichier(tmp, "tres_dangereux_TROJAN.scr")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    nom_stockage = meta["quarantine_storage_name"]
    assert nom_stockage.endswith(".quarantine")
    assert "TROJAN" not in nom_stockage
    assert "dangereux" not in nom_stockage
    assert ".scr" not in nom_stockage


def test_metadata_json_created(tmp):
    """4. Un enregistrement JSON de metadonnees est cree."""
    p = _fichier(tmp, "x.exe")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    chemin_json = os.path.join(tmp, "quarantine", meta["id"] + ".json")
    assert os.path.isfile(chemin_json)
    with open(chemin_json, encoding="utf-8") as fh:
        relu = json.load(fh)
    assert relu["id"] == meta["id"]


def test_sha256_matches_payload(tmp):
    """5. Le SHA-256 dans les metadonnees correspond bien au contenu de la
    charge utile isolee."""
    import hashlib
    contenu = b"contenu unique pour verification sha256"
    p = _fichier(tmp, "y.exe", contenu)
    attendu = hashlib.sha256(contenu).hexdigest()
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    assert meta["sha256"] == attendu
    dest = os.path.join(tmp, "quarantine", meta["quarantine_storage_name"])
    with open(dest, "rb") as fh:
        assert hashlib.sha256(fh.read()).hexdigest() == attendu


def test_status_bloque(tmp):
    """6. status == 'bloque'."""
    p = _fichier(tmp, "z.exe")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    assert meta["status"] == "bloque"


def test_detection_source_reason_confidence_preserved(tmp):
    """7. Source de detection / raison / confiance preservees."""
    p = _fichier(tmp, "w.exe")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="2 (IA)",
                              confidence=0.87, source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    assert meta["detection_source"] == "2 (IA)"
    assert meta["confidence"] == 0.87
    assert meta["reason"] == "Le moteur IA PE a classé le fichier comme malveillant."


# --- 8/9 : liste et details ---------------------------------------------

def test_list_quarantine_items_returns_item(tmp):
    """8. list_quarantine_items retourne l'element."""
    p = _fichier(tmp, "a.exe")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    statut, items, _ = qm.list_quarantine_items(tmp)
    assert statut == "ok"
    ids = [i["id"] for i in items]
    assert meta["id"] in ids


def test_get_quarantine_details_metadata_only(tmp):
    """9. get_quarantine_details retourne uniquement des metadonnees (pas
    le contenu de la charge utile)."""
    p = _fichier(tmp, "b.exe")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    details = qm.get_quarantine_details(meta["id"], tmp)
    assert details is not None
    assert details["nom_affiche"] == "b.exe"
    assert "payload" not in details and "contenu" not in details


# --- 10/11 : doublons / robustesse --------------------------------------

def test_duplicate_filename_does_not_overwrite(tmp):
    """10. Un nom de fichier dupliqué ne remplace pas un enregistrement
    de quarantaine existant (deux fichiers 'malware.exe' distincts a des
    moments differents doivent produire deux entrees independantes)."""
    p1 = _fichier(tmp, "malware.exe", b"premiere version")
    meta1 = qm.quarantine_file(p1, verdict="malveillant", detection_source="1 (signature)",
                               source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    p2 = _fichier(tmp, "malware.exe", b"seconde version, contenu different")
    meta2 = qm.quarantine_file(p2, verdict="malveillant", detection_source="1 (signature)",
                               source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    assert meta1["id"] != meta2["id"]
    assert meta1["quarantine_storage_name"] != meta2["quarantine_storage_name"]
    d1 = os.path.join(tmp, "quarantine", meta1["quarantine_storage_name"])
    d2 = os.path.join(tmp, "quarantine", meta2["quarantine_storage_name"])
    assert os.path.isfile(d1) and os.path.isfile(d2)
    with open(d1, "rb") as fh:
        assert fh.read() == b"premiere version"


def test_repeated_quarantine_attempt_does_not_corrupt_storage(tmp):
    """11. Des tentatives repetees de mise en quarantaine (meme contenu,
    sha256 identique) ne corrompent pas le stockage -- chaque appel reussi
    produit un enregistrement valide et independant."""
    for i in range(5):
        p = _fichier(tmp, "repete_%d.exe" % i, b"contenu identique")
        qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                           source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp)
    statut, items, _ = qm.list_quarantine_items(tmp)
    assert statut == "ok"
    assert len(items) == 5
    for it in items:
        assert it["statut"] == qm.STATUT_ENREGISTREMENT_OK


def test_non_utf8_legacy_metadata_does_not_crash_listing(tmp):
    """11b. Regression sur un cas reel : un enregistrement legacy dont le
    JSON a ete ecrit dans un encodage non-UTF-8 (observe dans le
    repertoire quarantine/ reel du depot) ne doit jamais faire planter
    list_quarantine_items() -- degrade en 'metadonnees_illisibles'."""
    qdir = os.path.join(tmp, "quarantine")
    os.makedirs(qdir, exist_ok=True)
    with open(os.path.join(qdir, "legacy_latin1.pdf"), "wb") as fh:
        fh.write(b"payload")
    # Ecrit volontairement en latin-1 avec un caractere accentue --
    # invalide en UTF-8 strict (reproduit l'erreur reelle rencontree).
    with open(os.path.join(qdir, "legacy_latin1.pdf.json"), "wb") as fh:
        fh.write('{"details": "signalé"}'.encode("latin-1"))

    statut, items, avertissements = qm.list_quarantine_items(tmp)
    assert statut == "ok"
    assert len(items) == 1
    assert items[0]["statut"] == qm.STATUT_ENREGISTREMENT_META_ILLISIBLE
    assert avertissements


def test_path_traversal_filename_is_safe(tmp):
    """12. Un nom de fichier contenant des sequences de traversee de
    chemin n'affecte jamais le nom de STOCKAGE (toujours un UUID opaque) --
    la traversee ne peut donc jamais atteindre un chemin hors quarantine/."""
    p = os.path.join(tmp, "evil_traversal_name.exe")
    with open(p, "wb") as fh:
        fh.write(b"x")
    # os.path.basename() neutralise deja toute sequence "../" presente
    # dans le CHEMIN d'entree ; on verifie ici que meme un nom de fichier
    # de base contenant des sequences suspectes reste confine aux
    # metadonnees, jamais utilise pour construire un chemin.
    import shutil
    nom_suspect = "..%2F..%2F..%2Fetc%2Fpasswd"
    p2 = os.path.join(tmp, "fichier_a_renommer.exe")
    with open(p2, "wb") as fh:
        fh.write(b"y")
    avant = set(os.listdir(tmp))
    meta = qm.quarantine_file(p2, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_FOLDER_SCAN, base_dir=tmp,
                              original_path_hint=nom_suspect)
    assert meta["quarantine_storage_name"].endswith(".quarantine")
    assert "/" not in meta["quarantine_storage_name"]
    assert "\\" not in meta["quarantine_storage_name"]
    # Aucun fichier nouveau n'est apparu ailleurs que dans quarantine/.
    apres = set(n for n in os.listdir(tmp) if n != "quarantine")
    assert apres <= avant


def test_malformed_legacy_metadata_does_not_crash_listing(tmp):
    """13. Des metadonnees legacy malformees n'empechent jamais
    list_quarantine_items() de retourner les autres enregistrements."""
    qdir = os.path.join(tmp, "quarantine")
    os.makedirs(qdir, exist_ok=True)
    # Entree legacy valide.
    with open(os.path.join(qdir, "20260101_010101_bon.exe"), "wb") as fh:
        fh.write(b"payload")
    with open(os.path.join(qdir, "20260101_010101_bon.exe.json"), "w", encoding="utf-8") as fh:
        json.dump({"nom_origine": "bon.exe", "chemin_origine": "/tmp/bon.exe",
                   "date_isolation": "2026-01-01T01:01:01", "detecte_par": "1 (signature)",
                   "details": "test"}, fh)
    # JSON corrompu (payload present mais metadonnees illisibles).
    with open(os.path.join(qdir, "20260101_020202_corrompu.exe"), "wb") as fh:
        fh.write(b"payload")
    with open(os.path.join(qdir, "20260101_020202_corrompu.exe.json"), "w", encoding="utf-8") as fh:
        fh.write("{ceci n'est pas du JSON valide")

    statut, items, avertissements = qm.list_quarantine_items(tmp)
    assert statut == "ok"
    assert len(items) == 2
    par_id = {i["id"]: i for i in items}
    assert par_id["20260101_010101_bon.exe"]["statut"] == qm.STATUT_ENREGISTREMENT_OK
    assert par_id["20260101_020202_corrompu.exe"]["statut"] == qm.STATUT_ENREGISTREMENT_META_ILLISIBLE
    assert avertissements  # au moins un avertissement signale l'incoherence


def test_upload_temp_never_falsely_reports_original_removed(tmp):
    """14. Le comportement 'copie temporaire de televersement' ne rapporte
    jamais faussement original_removed=True."""
    p = _fichier(tmp, "upload_copy.exe")
    meta = qm.quarantine_file(p, verdict="malveillant", detection_source="1 (signature)",
                              source_context=qm.SOURCE_UPLOAD, base_dir=tmp)
    assert meta["source_context"] == qm.SOURCE_UPLOAD
    assert meta["original_removed"] is False


def test_benign_verdict_does_not_quarantine(tmp):
    """15. Un verdict sain n'entraine jamais de mise en quarantaine (via
    le pipeline complet analyze.analyser())."""
    analyze = _analyze_isole(tmp)
    analyze.etape1_virustotal = lambda digest: {"statut": "sain", "detections": 0, "total_moteurs": 60}
    p = _fichier(tmp, "sain.exe", b"MZ" + b"\x00" * 100)
    r = analyze.analyser(p, isoler=True)
    assert r["verdict"] == "sain"
    assert r["action"] == "aucune"
    statut, items, _ = qm.list_quarantine_items(tmp)
    assert statut == "absent" or len(items) == 0


def test_indeterminate_verdict_does_not_quarantine(tmp):
    """16. Un verdict indetermine n'entraine jamais de mise en
    quarantaine."""
    analyze = _analyze_isole(tmp)
    analyze.etape1_virustotal = lambda digest: {"statut": "erreur_cle_absente"}
    p = _fichier(tmp, "indetermine.pdf", b"not a real pdf")
    r = analyze.analyser(p, isoler=True)
    assert r["verdict"] == "indetermine"
    assert r["action"] == "aucune"


def test_pe_routing_regression(tmp):
    """17. Non-regression : le routage PE (identifier_fichier) reste
    inchange."""
    analyze = _analyze_isole(tmp)
    p = _fichier(tmp, "x.exe", b"MZ" + b"\x90" * 62 + b"\x00" * 100)
    info = analyze.identifier_fichier(p)
    assert info["famille"] == "pe"


def test_pdf_routing_regression(tmp):
    """18. Non-regression : le routage PDF reste inchange."""
    analyze = _analyze_isole(tmp)
    p = _fichier(tmp, "x.pdf", b"%PDF-1.4\n%%EOF")
    info = analyze.identifier_fichier(p)
    assert info["famille"] == "pdf"
    assert info["valide"] is True


def test_docx_routing_regression(tmp):
    """19. Non-regression : le routage DOCX (validation structurelle
    reelle) reste inchange."""
    analyze = _analyze_isole(tmp)
    p = _fichier(tmp, "x.docx", b"not a real docx")
    info = analyze.identifier_fichier(p)
    assert info["famille"] == "docx"
    assert info["valide"] is False


def test_model_artifact_hash_regression():
    """20. Les artefacts modele PE/PDF/DOCX ne sont pas modifies par cette
    phase (aucun entrainement, cahier des charges §DO NOT MODIFY)."""
    import hashlib
    racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    attendus = {
        "model.pkl": "4c0f8b73382febd1ef17deb3d81e3c8fda48a36fd1e6f561080b8619fb30622f",
        "model_pdf.pkl": "be1ade69e5acdc130478dac6dbe904fa557eb53a93bdfa9140fc9097a9b3a8bc",
        "model_docx.pkl": "7ef9f2702af4e7fa28bbf61eb9a88cb08f698ab3e64d7bb6e95c6a3a50f9dde9",
    }
    for nom, attendu in attendus.items():
        chemin = os.path.join(racine, nom)
        h = hashlib.sha256()
        with open(chemin, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        assert h.hexdigest() == attendu, "%s modifie !" % nom


def run_all():
    import inspect
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = []
    ancien_base_dir = os.environ.get("HYBRIDSCAN_BASE_DIR")
    try:
        for t in tests:
            args = inspect.signature(t).parameters
            if args:
                with tempfile.TemporaryDirectory(prefix="hybridscan_quarantine_test_") as tmp:
                    try:
                        t(tmp)
                        print("PASS  %s" % t.__name__)
                    except Exception as e:
                        print("FAIL  %s : %s" % (t.__name__, e))
                        failures.append(t.__name__)
            else:
                try:
                    t()
                    print("PASS  %s" % t.__name__)
                except Exception as e:
                    print("FAIL  %s : %s" % (t.__name__, e))
                    failures.append(t.__name__)
    finally:
        if ancien_base_dir is None:
            os.environ.pop("HYBRIDSCAN_BASE_DIR", None)
        else:
            os.environ["HYBRIDSCAN_BASE_DIR"] = ancien_base_dir
        for mod in list(sys.modules):
            if mod.startswith("document_ml") or mod == "analyze":
                del sys.modules[mod]

    print("\n%d/%d tests passed" % (len(tests) - len(failures), len(tests)))
    return len(failures) == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
