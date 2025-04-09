from elasticsearch import Elasticsearch
import os

# Récupération des variables d'environnement
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "NJVjAXFHKle*gbElX48E")

print("Connexion à Elasticsearch...")
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", ELASTIC_PASSWORD),
    verify_certs=False
)

# Vérifier la connexion
if not es.ping():
    raise Exception("La connexion à Elasticsearch a échoué!")
else:
    print("Connexion à Elasticsearch réussie!")

index_name = "documents"

# Définition du mapping
mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "french_analyzer": {
                    "type": "french"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "doc_name": {"type": "text", "analyzer": "french_analyzer"},
            "doc_type": {"type": "keyword"},
            "doc_content": {"type": "text", "analyzer": "french_analyzer"},
            "doc_content_b64": {"type": "binary"},  # Pour stocker le contenu binaire
            "doc_format": {"type": "keyword"},
            "doc_insert_date": {"type": "date"},
            "doc_updated_date": {"type": "date"},
            "doc_file_full_path": {"type": "keyword"},
            "original_filename": {"type": "keyword"}
        }
    }
}

print(f"Vérification de l'existence de l'index '{index_name}'...")

# Supprimer l'index s'il existe
if es.indices.exists(index=index_name):
    print(f"Suppression de l'ancien index '{index_name}'...")
    es.indices.delete(index=index_name)
    print("Index supprimé avec succès.")

# Créer l'index avec le nouveau mapping
print(f"Création de l'index '{index_name}' avec le mapping...")
es.indices.create(index=index_name, body=mapping)
print("Index créé avec succès!")

# Vérifier que l'index a été créé
if es.indices.exists(index=index_name):
    print(f"Vérification réussie : l'index '{index_name}' existe!")
    # Afficher les détails de l'index
    index_details = es.indices.get(index=index_name)
    print("\nDétails de l'index :")
    print(f"Nombre de shards : {index_details[index_name]['settings']['index']['number_of_shards']}")
    print(f"Nombre de réplicas : {index_details[index_name]['settings']['index']['number_of_replicas']}")
else:
    print("ERREUR : L'index n'a pas été créé correctement!")
