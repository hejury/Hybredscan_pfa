"""document_ml — pipelines ML statiques par famille de document.

Chaque sous-package (ex. `pdf`) est technique­ment independant : son propre
schema de caracteristiques, son propre extracteur, son propre modele. Aucun
pipeline document ne reutilise les 29 caracteristiques PE de `extract_features.py`
/ `model.pkl`, et aucun ne les modifie.

Portee actuelle : seul `document_ml.pdf` existe. Un futur pipeline Office
(DOC/DOCX) suivrait la meme structure sous `document_ml/office/` mais n'a pas
ete commence — voir validation/DOCUMENT-DATASET-PLAN.md.
"""
