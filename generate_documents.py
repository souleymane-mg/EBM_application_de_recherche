import random
import datetime
from elasticsearch import Elasticsearch
import os

# Connexion sécurisée à Elasticsearch
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "+*Vmd=yXTQlNvZUXJnAb")  
CERT_PATH = r"C:\Users\Abissa\Documents\elasticsearch\config\certs\http_ca.crt"

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", ELASTIC_PASSWORD),
    verify_certs=True,
    ca_certs=CERT_PATH
)

index_name = "documents"

# Liste fictive de noms et types de documents
doc_names = ["Rapport", "CV", "Fiche de poste", "Évaluation annuelle", "Contrat"]
doc_types = ["Rapport", "CV", "Fiche de poste", "Évaluation annuelle"]
doc_formats = ["pdf", "docx"]

# Contenu fictif
doc_contents = [
    "Ce document traite de la stratégie d'entreprise et des objectifs de l'année.",
    "Résumé des compétences et expériences professionnelles.",
    "Description du poste et des responsabilités associées.",
    "Évaluation annuelle des performances et axes d'amélioration.",
    "Contrat signé entre l'entreprise et le client."
]

# Génération de 100 documents
for i in range(1, 101):
    doc_id = str(i)
    doc_name = random.choice(doc_names) + f" {i}"
    doc_type = random.choice(doc_types)
    doc_format = random.choice(doc_formats)
    doc_content = random.choice(doc_contents)
    doc_insert_date = datetime.datetime.utcnow().isoformat()
    doc_updated_date = doc_insert_date
    doc_file_full_path = f"/path/to/document_{i}.{doc_format}"

    document = {
        "doc_id": doc_id,
        "doc_name": doc_name,
        "doc_type": doc_type,
        "doc_format": doc_format,
        "doc_content": doc_content,
        "doc_insert_date": doc_insert_date,
        "doc_updated_date": doc_updated_date,
        "doc_file_full_path": doc_file_full_path
    }

    es.index(index=index_name, id=doc_id, body=document)

print("✅ 100 documents fictifs ont été ajoutés avec succès !")
