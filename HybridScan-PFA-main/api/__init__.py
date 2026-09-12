"""api — Pont HTTP/JSON FastAPI pour le moteur HybridScan existant.

Ce package n'implemente AUCUNE logique de detection de malware. Chaque
service sous api/services/ delegue au code Python deja teste
(analyze.py, quarantine_manager.py, watcher.py, auth.py, backend_shared.py)
et se contente de convertir ses entrees/sorties en JSON. Voir
validation/NEXTJS-FASTAPI-INTEGRATION.md pour le contrat complet."""
