import os, requests

API = "https://mb-api.abuse.ch/api/v1/"
OUT_DIR = os.path.expanduser("~/samples/malware_zip")
os.makedirs(OUT_DIR, exist_ok=True)

# Clé API abuse.ch (mettre la vôtre, ou via variable d'environnement)
AUTH_KEY = os.environ.get("MB_API_KEY", "VOTRE_CLE_ICI")
HEADERS = {"Auth-Key": AUTH_KEY}

# Étape 1 : lister les derniers échantillons de type exe
def get_batch(file_type="exe", limit=1000):
    data = {"query": "get_file_type", "file_type": file_type, "limit": str(limit)}
    r = requests.post(API, data=data, headers=HEADERS, timeout=60)
    r.raise_for_status()
    js = r.json()
    if js.get("query_status") != "ok":
        print("Erreur API:", js.get("query_status"))
        return []
    return js.get("data", [])

# Étape 2 : télécharger un échantillon par son hash (ZIP chiffré)
def download(sha256):
    dest = os.path.join(OUT_DIR, sha256 + ".zip")
    if os.path.exists(dest):
        return "skip"
    data = {"query": "get_file", "sha256_hash": sha256}
    r = requests.post(API, data=data, headers=HEADERS, timeout=120)
    if r.status_code == 200 and r.content[:2] == b"PK":  # signature ZIP
        open(dest, "wb").write(r.content)
        return "ok"
    return "fail"

samples = get_batch(file_type="exe", limit=1000)
print(f"{len(samples)} échantillons trouvés")

ok = skip = fail = 0
for i, s in enumerate(samples, 1):
    res = download(s["sha256_hash"])
    if res == "ok": ok += 1
    elif res == "skip": skip += 1
    else: fail += 1
    if i % 50 == 0:
        print(f"  {i}/{len(samples)} — ok:{ok} skip:{skip} fail:{fail}")

print(f"Terminé — ok:{ok} | skip:{skip} | fail:{fail}")
print("ZIP en attente de décompression:")
os.system(f"ls {OUT_DIR}/*.zip 2>/dev/null | wc -l")
