import os, csv, math, pefile

DIRS = {os.path.expanduser("~/samples/malware"): 1,
        os.path.expanduser("~/samples/benign"): 0}
OUT = os.path.expanduser("~/pfe/dataset.csv")

SUSPECT_APIS = ["CreateRemoteThread","VirtualAllocEx","WriteProcessMemory","LoadLibraryA",
                "GetProcAddress","RegSetValueExA","InternetOpenA","URLDownloadToFileA",
                "CreateProcessA","ShellExecuteA","WinExec","IsDebuggerPresent",
                "CryptEncrypt","OpenProcess","SetWindowsHookExA","CreateMutexA"]

def entropy(data):
    if not data: return 0.0
    freq = [0]*256
    for b in data: freq[b] += 1
    e = 0.0
    for c in freq:
        if c:
            p = c/len(data)
            e -= p*math.log2(p)
    return e

def extract(path, label):
    pe = None
    try:
        pe = pefile.PE(path, fast_load=True)
        pe.parse_data_directories()
        f = {}
        f["file_size"] = os.path.getsize(path)
        f["entropy"] = round(entropy(open(path,"rb").read()), 4)
        f["nb_sections"] = len(pe.sections)
        f["size_code"] = pe.OPTIONAL_HEADER.SizeOfCode
        f["size_image"] = pe.OPTIONAL_HEADER.SizeOfImage
        f["entry_point"] = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        f["subsystem"] = pe.OPTIONAL_HEADER.Subsystem
        f["dll_char"] = pe.OPTIONAL_HEADER.DllCharacteristics
        f["machine"] = pe.FILE_HEADER.Machine
        # timestamp retire : fuite de donnees (voir exp_leakage.py)

        ents = [s.get_entropy() for s in pe.sections]
        f["sect_entropy_max"] = round(max(ents),4) if ents else 0
        f["sect_entropy_mean"] = round(sum(ents)/len(ents),4) if ents else 0

        imports = set()
        nb_dll = 0
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            nb_dll = len(pe.DIRECTORY_ENTRY_IMPORT)
            for d in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in d.imports:
                    if imp.name:
                        imports.add(imp.name.decode(errors="ignore"))
        f["nb_dll"] = nb_dll
        f["nb_imports"] = len(imports)
        for api in SUSPECT_APIS:
            f["api_"+api] = 1 if api in imports else 0
        f["label"] = label
        return f
    except Exception:
        return None
    finally:
        if pe:
            try: pe.close()
            except: pass

rows = []
for d, label in DIRS.items():
    if not os.path.isdir(d): continue
    files = os.listdir(d)
    ok = 0
    for name in files:
        r = extract(os.path.join(d, name), label)
        if r:
            rows.append(r); ok += 1
    print(d, ":", ok, "/", len(files), "fichiers PE valides")

if rows:
    keys = list(rows[0].keys())
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader(); w.writerows(rows)
    print("\ndataset.csv cree :", len(rows), "lignes,", len(keys), "colonnes")
    print("Chemin:", OUT)
else:
    print("Aucun fichier PE valide trouve")
