#!/bin/bash
ZIP_DIR=~/samples/malware_zip
OUT_DIR=~/samples/malware
mkdir -p "$OUT_DIR"
ok=0; err=0
for z in "$ZIP_DIR"/*.zip; do
    # -p infected = mot de passe ; -y = oui à tout ; -o = dossier de sortie
    if 7z x -p"infected" -y -o"$OUT_DIR" "$z" > /dev/null 2>&1; then
        ok=$((ok+1))
    else
        err=$((err+1))
    fi
done
# Retirer le droit d'exécution sur tous les échantillons (sécurité)
chmod -x "$OUT_DIR"/* 2>/dev/null
echo "OK: $ok | Erreurs: $err"
echo "Total malware PE:"; ls "$OUT_DIR" | wc -l
