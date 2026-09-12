import sys, hashlib, requests, time, os

def _charger_cle_vt():
    """Charge la cle VirusTotal depuis l'environnement, puis depuis
    .streamlit/secrets.toml. Ne leve jamais d'exception ni n'affiche
    la valeur."""
    cle = os.environ.get("VT_API_KEY")
    if cle:
        return cle
    try:
        import streamlit as st
        return st.secrets.get("VT_API_KEY")
    except Exception:
        return None

VT_KEY = _charger_cle_vt()
URL = "https://www.virustotal.com/api/v3/files/"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def check(path):
    """Etape 1 : detection par signature via VirusTotal"""
    d = sha256(path)
    if not VT_KEY:
        return {"statut": "erreur_cle_absente", "sha256": d}
    try:
        r = requests.get(URL + d, headers={"x-apikey": VT_KEY}, timeout=30)
    except requests.exceptions.RequestException as e:
        return {"statut": "erreur_reseau", "detail": str(e), "sha256": d}

    if r.status_code == 404:
        return {"statut": "inconnu", "sha256": d}   # -> passer a l'etape 2 (IA)
    if r.status_code == 401:
        return {"statut": "cle_invalide", "sha256": d}
    if r.status_code == 429:
        return {"statut": "quota_depasse", "sha256": d}
    if r.status_code != 200:
        return {"statut": "erreur_api", "code": r.status_code, "sha256": d}

    stats = r.json()["data"]["attributes"]["last_analysis_stats"]
    mal = stats.get("malicious", 0)
    total = sum(stats.values())
    return {
        "statut": "malveillant" if mal > 0 else "sain",
        "detections": mal,
        "total_moteurs": total,
        "sha256": d,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 vt_check.py <fichier>"); sys.exit(1)
    p = sys.argv[1]
    if not os.path.exists(p):
        print("Fichier introuvable:", p); sys.exit(1)
    res = check(p)
    print("SHA-256 :", res["sha256"])
    print("Statut  :", res["statut"])
    if "detections" in res:
        print("Detections :", res["detections"], "/", res["total_moteurs"])
