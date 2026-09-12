import os, requests, time

# ⚠️ بدل هاد المفتاح بواحد جديد من https://auth.abuse.ch/ حيت القديم تكشف
API_KEY = "e8a971c2170e817d03f381f340ccca8524b2a19ac8c77a9e"
OUT_DIR = os.path.expanduser("~/samples/malware_zip")
URL = "https://mb-api.abuse.ch/api/v1/"
HEADERS = {"Auth-Key": API_KEY}
CSV_URL = f"https://mb-api.abuse.ch/v2/files/exports/{API_KEY}/recent.csv"
LIMITE = 500

os.makedirs(OUT_DIR, exist_ok=True)

def get_hashes():
    for a in range(3):
        try:
            r = requests.get(CSV_URL, timeout=120)
            if r.status_code != 200:
                print("Erreur CSV, code:", r.status_code); time.sleep(15); continue
            lignes = [l for l in r.text.splitlines() if l and not l.startswith("#")]
            hashes = [l.split(",")[1].strip().strip('"') for l in lignes
                      if ("exe" in l.lower() or "dll" in l.lower())]
            return [h for h in hashes if len(h) == 64][:LIMITE]
        except Exception as e:
            print("Erreur:", e); time.sleep(15)
    return []

def download(h):
    p = os.path.join(OUT_DIR, h + ".zip")
    if os.path.exists(p): return "skip"
    try:
        r = requests.post(URL, data={"query": "get_file", "sha256_hash": h},
                          headers=HEADERS, timeout=120)
        if r.status_code != 200 or len(r.content) < 100: return "fail"
        open(p, "wb").write(r.content); return "ok"
    except Exception:
        return "erreur"

hs = get_hashes()
print("Telechargement de", len(hs), "fichiers")
for i, h in enumerate(hs, 1):
    print(i, h[:16], download(h)); time.sleep(1)
n = len(os.listdir(OUT_DIR))
print("Total dans le dossier:", n)
