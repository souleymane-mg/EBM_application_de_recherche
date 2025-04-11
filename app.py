from flask import Flask, request, jsonify, send_file, send_from_directory
from elasticsearch import Elasticsearch
from flask_cors import CORS
import datetime
import os
from werkzeug.utils import secure_filename
import base64
import mimetypes
import PyPDF2
import docx
import chardet
from pdf2image import convert_from_path
from PIL import Image
import io

app = Flask(__name__)
CORS(app)  # Activer CORS pour toutes les routes

# Configuration pour le téléchargement de fichiers
UPLOAD_FOLDER = os.path.abspath('uploads')
THUMBNAILS_FOLDER = os.path.abspath('thumbnails')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['THUMBNAILS_FOLDER'] = THUMBNAILS_FOLDER

# Créer les dossiers nécessaires s'ils n'existent pas
for folder in [UPLOAD_FOLDER, THUMBNAILS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Connexion à Elasticsearch
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "NJVjAXFHKle*gbElX48E")

try:
    print("Tentative de connexion à Elasticsearch...")
    es = Elasticsearch(
        "https://localhost:9200",
        basic_auth=("elastic", ELASTIC_PASSWORD),
        verify_certs=False
    )
    if es.ping():
        print("Connexion à Elasticsearch réussie!")
    else:
        print("Impossible de se connecter à Elasticsearch")
except Exception as e:
    print(f"Erreur lors de la connexion à Elasticsearch: {str(e)}")
    es = None

index_name = "documents"

# Vérifier si l'index existe, sinon le créer
try:
    if not es.indices.exists(index=index_name):
        print(f"Création de l'index {index_name}...")
        es.indices.create(index=index_name)
        print(f"Index {index_name} créé avec succès!")
except Exception as e:
    print(f"Erreur lors de la vérification/création de l'index: {str(e)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def extract_text_from_file(file_path):
    """Extraire le texte d'un fichier selon son type"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
        elif file_ext == '.docx':
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
            
        elif file_ext == '.txt':
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
                
        else:
            return ""
            
    except Exception as e:
        print(f"Erreur lors de l'extraction du texte: {str(e)}")
        return ""

def generate_thumbnail(file_path, doc_id):
    """Générer une miniature pour un document"""
    thumbnail_path = os.path.join(app.config['THUMBNAILS_FOLDER'], f"{doc_id}.jpg")
    
    if os.path.exists(thumbnail_path):
        return thumbnail_path
        
    try:
        if file_path.lower().endswith('.pdf'):
            # Convertir la première page du PDF en image
            images = convert_from_path(file_path, first_page=1, last_page=1)
            if images:
                image = images[0]
                # Redimensionner l'image pour la miniature
                image.thumbnail((180, 180), Image.Resampling.LANCZOS)
                image.save(thumbnail_path, "JPEG", quality=95)
                return thumbnail_path
                
    except Exception as e:
        print(f"Erreur lors de la génération de la miniature: {str(e)}")
        return None

# Route pour récupérer tous les documents
@app.route('/documents')
def get_documents():
    try:
        query = {"query": {"match_all": {}}}
        res = es.search(index=index_name, body=query, size=100)
        documents = []

        for doc in res['hits']['hits']:
            documents.append({
                "doc_id": doc["_id"],
                "doc_name": doc["_source"]["doc_name"],
                "doc_type": doc["_source"]["doc_type"],
                "doc_format": doc["_source"]["doc_format"],
                "doc_content": doc["_source"].get("doc_content", ""),
                "doc_content_b64": doc["_source"].get("doc_content_b64", ""),
                "doc_insert_date": doc["_source"].get("doc_insert_date", ""),
                "doc_updated_date": doc["_source"].get("doc_updated_date", ""),
                "doc_file_full_path": doc["_source"].get("doc_file_full_path", ""),
                "original_filename": doc["_source"].get("original_filename", "")
            })

        return jsonify(documents)
    except Exception as e:
        print(f"Erreur lors de la récupération des documents: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route pour ajouter un document
@app.route('/documents', methods=['POST'])
def add_document():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Pas de fichier"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Pas de fichier sélectionné"}), 400

        # Récupération des champs obligatoires
        doc_id = request.form.get("doc_id")
        doc_name = request.form.get("doc_name")
        doc_type = request.form.get("doc_type")
        
        # Vérification des champs obligatoires
        if not all([doc_name, doc_type]):
            return jsonify({"error": "Champs obligatoires manquants"}), 400
        
        if file and allowed_file(file.filename):
            # Si doc_id n'est pas fourni, on en génère un
            if not doc_id:
                doc_id = str(datetime.datetime.now().timestamp()).replace(".", "")
            
            # On utilise le doc_id dans le nom du fichier
            file_ext = os.path.splitext(file.filename)[1]
            filename = f"{doc_id}{file_ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_path = os.path.abspath(file_path)
            file.save(file_path)
            
            # Génération de la miniature pour les PDF
            if file_ext.lower() == '.pdf':
                generate_thumbnail(file_path, doc_id)
            
            # Extraction du texte et du format
            doc_format = os.path.splitext(file.filename)[1][1:].upper()
            if doc_format not in ['PDF', 'DOCX']:
                return jsonify({"error": "Format de fichier non autorisé. Seuls PDF et DOCX sont acceptés"}), 400
            
            extracted_text = extract_text_from_file(file_path)
            current_time = datetime.datetime.utcnow()

            document = {
                "doc_id": doc_id,
                "doc_name": doc_name,
                "doc_type": doc_type,
                "doc_content": extracted_text,
                "doc_format": doc_format,
                "doc_insert_date": current_time,
                "doc_updated_date": current_time,
                "doc_file_full_path": file_path
            }

            # Indexation avec l'ID spécifié
            result = es.index(index=index_name, id=doc_id, body=document)
            return jsonify({
                "message": "Document ajouté avec succès",
                "doc_id": doc_id,
                "doc_name": doc_name,
                "doc_type": doc_type,
                "doc_format": doc_format
            }), 201
            
        return jsonify({"error": "Type de fichier non autorisé"}), 400
        
    except Exception as e:
        print(f"Erreur lors de l'ajout du document: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route pour supprimer un document
@app.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        es.delete(index=index_name, id=doc_id)
        return jsonify({"message": "Document supprimé avec succès"}), 200
    except Exception as e:
        print(f"Erreur lors de la suppression du document: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route pour télécharger un document
@app.route('/documents/<doc_id>/download')
def download_document(doc_id):
    try:
        doc = es.get(index=index_name, id=doc_id)
        file_path = doc["_source"]["doc_file_full_path"]
        original_filename = doc["_source"].get("original_filename", os.path.basename(file_path))
        
        if not os.path.exists(file_path):
            print(f"Fichier non trouvé: {file_path}")
            return jsonify({"error": "Fichier non trouvé"}), 404
        
        mime_type = get_mime_type(file_path)
        
        response = send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False  # Pour permettre l'affichage dans le navigateur
        )
        
        # Ajout des en-têtes CORS
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        return response
    except Exception as e:
        print(f"Erreur lors du téléchargement: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route pour la recherche
@app.route('/search', methods=['GET'])
def search_documents():
    try:
        query_text = request.args.get("query", "")
        doc_type = request.args.get("doc_type", "")
        
        if not query_text:
            return jsonify({"documents": [], "total": 0}), 200

        search_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": ["doc_name^3", "doc_content^2", "doc_type"],
                                "type": "best_fields",
                                "operator": "or",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            }
        }

        if doc_type:
            search_query["query"]["bool"]["filter"] = [{"term": {"doc_type": doc_type}}]

        res = es.search(index=index_name, body=search_query, size=100)
        documents = []
        
        for hit in res['hits']['hits']:
            doc_data = {
                "doc_id": hit["_id"],
                "title": hit["_source"]["doc_name"],
                "doc_type": hit["_source"]["doc_type"],
                "doc_format": hit["_source"]["doc_format"],
                "content": hit["_source"].get("doc_content", "")[:150] + "..."
            }
            documents.append(doc_data)

        return jsonify({"documents": documents, "total": len(documents)}), 200

    except Exception as e:
        print(f"Erreur lors de la recherche: {str(e)}")
        return jsonify({"error": str(e), "documents": [], "total": 0}), 500

# Route pour récupérer la miniature d'un document
@app.route('/documents/<doc_id>/thumbnail')
def get_thumbnail(doc_id):
    try:
        doc = es.get(index=index_name, id=doc_id)
        file_path = doc["_source"]["doc_file_full_path"]
        
        if not os.path.exists(file_path):
            return jsonify({"error": "Fichier non trouvé"}), 404
            
        thumbnail_path = generate_thumbnail(file_path, doc_id)
        
        if thumbnail_path and os.path.exists(thumbnail_path):
            return send_file(
                thumbnail_path,
                mimetype='image/jpeg',
                as_attachment=False
            )
        else:
            return jsonify({"error": "Impossible de générer la miniature"}), 500
            
    except Exception as e:
        print(f"Erreur lors de la récupération de la miniature: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    try:
        es_status = "OK" if es and es.ping() else "NON CONNECTÉ"
        return jsonify({
            "status": "UP",
            "elasticsearch": es_status,
            "upload_folder": os.path.exists(UPLOAD_FOLDER),
            "thumbnails_folder": os.path.exists(THUMBNAILS_FOLDER)
        })
    except Exception as e:
        return jsonify({
            "status": "DOWN",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
