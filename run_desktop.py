#!/usr/bin/env python3
"""run_desktop.py — Point d'entrée unique de l'application desktop HybridScan.

    python run_desktop.py

démarre l'API FastAPI locale (127.0.0.1:8000) et le frontend Next.js
(port 3000), attend qu'ils répondent, puis ouvre une fenêtre PyWebView
native affichant l'interface HybridScan -- aucun terminal ni navigateur à
lancer manuellement. Fermer la fenêtre arrête proprement les deux
processus.

La logique vit dans desktop/launcher.py ; ce fichier n'est qu'un point
d'entrée mince (voir `python run_desktop.py --help` pour les options,
notamment --dev pour se rattacher à des serveurs déjà lancés à la main).
"""
from desktop.launcher import main

if __name__ == "__main__":
    raise SystemExit(main())
