from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from elasticsearch import Elasticsearch
import datetime
import os
from werkzeug.utils import secure_filename
import base64
import mimetypes
import PyPDF2
import docx
import chardet

app = Flask(__name__)

# Configuration pour le téléchargement de fichiers
UPLOAD_FOLDER = os.path.abspath('uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Créer le dossier uploads s'il n'existe pas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Connexion à Elasticsearch
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "NJVjAXFHKle*gbElX48E")

es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", ELASTIC_PASSWORD),
    verify_certs=False
)

index_name = "documents"

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
            # Détecter l'encodage du fichier
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            # Lire le fichier avec l'encodage détecté
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
                
        else:
            return ""
            
    except Exception as e:
        print(f"Erreur lors de l'extraction du texte: {str(e)}")
        return ""

# Route pour afficher les documents
@app.route('/')
def index():
    query = {"query": {"match_all": {}}}
    res = es.search(index=index_name, body=query, size=100)
    documents = []

    for doc in res['hits']['hits']:
        documents.append({
            "doc_id": doc["_id"],
            "doc_name": doc["_source"]["doc_name"],
            "doc_type": doc["_source"]["doc_type"],
            "doc_format": doc["_source"]["doc_format"],
            "doc_file_full_path": doc["_source"]["doc_file_full_path"]
        })

    return render_template('index.html', documents=documents)

# Route pour afficher la page d'ajout de document
@app.route('/create')
def create():
    return render_template('create.html')

# Route pour afficher la page d'édition d'un document
@app.route('/edit/<doc_id>')
def edit(doc_id):
    doc = es.get(index=index_name, id=doc_id)
    return render_template('edit.html', document=doc["_source"])

# Route pour ajouter un document
@app.route('/add_document', methods=['POST'])
def add_document():
    doc_id = request.form.get("doc_id")
    doc_name = request.form.get("doc_name")
    doc_type = request.form.get("doc_type")
    doc_format = request.form.get("doc_format")
    
    if 'file' not in request.files:
        return jsonify({"error": "Pas de fichier"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Pas de fichier sélectionné"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_path = os.path.abspath(file_path)  # Convertir en chemin absolu
        file.save(file_path)
        
        try:
            # Extraire le texte du document
            extracted_text = extract_text_from_file(file_path)
            
            # Lire le contenu binaire pour le stockage
            with open(file_path, 'rb') as f:
                file_content = f.read()
                file_content_b64 = base64.b64encode(file_content).decode('utf-8')

            document = {
                "doc_id": doc_id,
                "doc_name": doc_name,
                "doc_type": doc_type,
                "doc_format": doc_format,
                "doc_content": extracted_text,  # Utiliser le texte extrait
                "doc_content_b64": file_content_b64,  # Garder le contenu binaire pour le téléchargement
                "doc_insert_date": datetime.datetime.utcnow(),
                "doc_updated_date": datetime.datetime.utcnow(),
                "doc_file_full_path": file_path,
                "original_filename": filename
            }

            es.index(index=index_name, id=doc_id, body=document)
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Erreur lors de l'ajout du document: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Type de fichier non autorisé"}), 400

@app.route('/download_document/<doc_id>')
def download_document(doc_id):
    try:
        # Récupérer le document
        doc = es.get(index=index_name, id=doc_id)
        file_path = doc["_source"]["doc_file_full_path"]
        original_filename = doc["_source"].get("original_filename", os.path.basename(file_path))
        
        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            print(f"Fichier non trouvé: {file_path}")
            return jsonify({"error": "Fichier non trouvé"}), 404
        
        # Déterminer le type MIME
        mime_type = get_mime_type(file_path)
        
        try:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=original_filename,
                mimetype=mime_type
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi du fichier: {str(e)}")
            return jsonify({"error": f"Erreur lors de l'envoi du fichier: {str(e)}"}), 500
            
    except Exception as e:
        print(f"Erreur lors de la récupération du document: {str(e)}")
        return jsonify({"error": str(e)}), 404

@app.route('/update_document', methods=['POST'])
def update_document():
    doc_id = request.form.get("doc_id")
    doc_name = request.form.get("doc_name")
    doc_type = request.form.get("doc_type")
    doc_format = request.form.get("doc_format")
    doc_file_full_path = request.form.get("doc_file_full_path")

    document = {
        "doc_name": doc_name,
        "doc_type": doc_type,
        "doc_format": doc_format,
        "doc_updated_date": datetime.datetime.utcnow(),
        "doc_file_full_path": doc_file_full_path
    }

    es.update(index=index_name, id=doc_id, body={"doc": document})
    return redirect(url_for('index'))  # Rediriger après modification


# Route pour supprimer un document
@app.route('/delete_document/<doc_id>', methods=['POST'])
def delete_document(doc_id):
    es.delete(index=index_name, id=doc_id)
    return jsonify({"message": "Document supprimé avec succès"}), 200

@app.route('/search', methods=['GET'])
def search_documents():
    try:
        query_text = request.args.get("query", "")
        doc_type = request.args.get("doc_type", "")
        
        print("=== DÉBUT DE LA RECHERCHE ===")
        print(f"Paramètres reçus - Query: '{query_text}', Type: '{doc_type}'")

        if not query_text:
            print("Erreur: Aucun terme de recherche fourni")
            return jsonify({
                "status": "error",
                "message": "Veuillez entrer un terme de recherche",
                "documents": []
            }), 400

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

        print(f"Requête Elasticsearch: {search_query}")
        
        # Vérifier la connexion à Elasticsearch
        if not es.ping():
            print("Erreur: Impossible de se connecter à Elasticsearch")
            raise Exception("La connexion à Elasticsearch a échoué")

        # Vérifier que l'index existe
        if not es.indices.exists(index=index_name):
            print(f"Erreur: L'index '{index_name}' n'existe pas")
            raise Exception(f"L'index '{index_name}' n'existe pas")

        print("Exécution de la recherche...")
        res = es.search(index=index_name, body=search_query, size=100)
        print(f"Résultats bruts: {res}")
        
        documents = []
        
        for hit in res['hits']['hits']:
            doc_data = {
                "doc_id": hit["_id"],
                "doc_name": hit["_source"]["doc_name"],
                "doc_type": hit["_source"]["doc_type"],
                "doc_format": hit["_source"]["doc_format"],
                "doc_file_full_path": hit["_source"].get("doc_file_full_path", ""),
                "score": hit["_score"]
            }
            
            if "highlight" in hit:
                doc_data["content_preview"] = hit["highlight"].get("doc_content", [""])[0]
            else:
                content = hit["_source"].get("doc_content", "")
                doc_data["content_preview"] = content[:150] + "..." if content else ""

            documents.append(doc_data)
            print(f"Document ajouté aux résultats: {doc_data}")

        response_data = {
            "status": "success",
            "message": f"{len(documents)} document(s) trouvé(s)",
            "documents": documents,
            "total": len(documents)
        }
        
        print(f"Réponse finale: {response_data}")
        print("=== FIN DE LA RECHERCHE ===")

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Erreur lors de la recherche: {str(e)}")
        print(f"Type d'erreur: {type(e)}")
        import traceback
        print(f"Traceback complet: {traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "message": "Une erreur est survenue lors de la recherche",
            "error_details": str(e),
            "documents": [],
            "total": 0
        }), 500

@app.route('/recherche')
def search_page():
    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)
