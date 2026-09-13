"""document_ml.pdf — pipeline ML statique dedie aux fichiers PDF.

Independant du pipeline PE (`analyze.py`/`extract_features.py`/`model.pkl`) :
schema de caracteristiques propre (`schema.py`), extracteur propre
(`features.py`), inference propre (`predict.py`), entrainement/evaluation
propres (`train.py`/`evaluate.py`). Le fichier modele produit est
`model_pdf.pkl`, jamais `model.pkl`.
"""
