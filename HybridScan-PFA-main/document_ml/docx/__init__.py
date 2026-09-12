"""document_ml.docx — pipeline ML statique dedie aux fichiers DOCX (OOXML).

INDEPENDANT des pipelines PE (analyze.py/extract_features.py/model.pkl) et
PDF (document_ml/pdf/*) : schema de caracteristiques propre (schema.py),
validation de conteneur propre (validate.py), extraction propre
(features.py), entrainement/evaluation propres (train.py/evaluate.py). Le
fichier modele produit serait model_docx.pkl -- INEXISTANT a ce stade
(phase de fondation/recherche uniquement, voir validation/DOCX-DATASET-PLAN.md).

Portee de cette phase : DOCX uniquement. Le format DOC legacy (OLE/CFB)
n'est PAS couvert ici et reste au comportement VirusTotal-seul existant
dans analyze.py -- aucun module DOC n'a ete cree.

Ce package n'est PAS importe par analyze.py/app.py : DOCX continue de
suivre EXACTEMENT le chemin existant (VirusTotal -> si non concluant ->
indetermine) tant qu'aucun modele DOCX valide n'existe et n'a ete approuve
pour integration (voir cahier des charges §18)."""
