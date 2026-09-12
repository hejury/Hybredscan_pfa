import os, zipfile

ZIP_DIR = os.path.expanduser("~/samples/malware_zip")
OUT_DIR = os.path.expanduser("~/samples/malware")
PWD = b"infected"

os.makedirs(OUT_DIR, exist_ok=True)
ok, skip, err = 0, 0, 0

for name in os.listdir(ZIP_DIR):
    if not name.endswith(".zip"):
        continue
    try:
        with zipfile.ZipFile(os.path.join(ZIP_DIR, name)) as z:
            for member in z.namelist():
                dest = os.path.join(OUT_DIR, os.path.basename(member))
                if os.path.exists(dest):
                    skip += 1
                    continue
                z.extract(member, OUT_DIR, pwd=PWD)
                # Retirer le droit d'exécution (sécurité)
                extracted = os.path.join(OUT_DIR, member)
                if os.path.exists(extracted):
                    os.chmod(extracted, 0o600)
                ok += 1
    except Exception as e:
        err += 1
        print(f"Erreur sur {name}: {e}")

print(f"Extraits: {ok} | Ignorés (déjà présents): {skip} | Erreurs: {err}")
