import os
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# Importer nos modules personnalisés
from config import Config
from document_manager import DocumentManager
from utils import (
    setup_logging, log_execution_time, handle_api_errors, 
    sanitize_filename, format_file_size, validate_file_size,
    create_error_response, create_success_response, SessionManager
)

# --- Configuration de l'application Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = str(Config.UPLOAD_FOLDER)

# Configuration du logging
logger = setup_logging(log_level="INFO", log_file="logs/rag_app.log")

# Initialisation des gestionnaires
document_manager = DocumentManager()
session_manager = SessionManager()

# Variables globales
ALLOWED_EXTENSIONS = Config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    """Vérifie si le fichier a une extension autorisée"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Affiche la page d'accueil"""
    try:
        # Vérifier s'il y a des documents déjà chargés
        doc_count = document_manager.get_document_count()
        session_manager.set('doc_count', doc_count)
        
        logger.info("Page d'accueil chargée")
        return render_template('index.html', doc_count=doc_count)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page d'accueil: {e}")
        return render_template('index.html', doc_count=0, error="Erreur lors du chargement de la page")

@app.route('/upload', methods=['POST'])
@log_execution_time
@handle_api_errors
def upload_files():
    """Gère le téléversement et le traitement des fichiers PDF"""
    # Vérifier si des fichiers sont présents
    if 'files[]' not in request.files:
        return create_error_response("Aucun fichier sélectionné", 400)
    
    files = request.files.getlist('files[]')
    if not files or all(f.filename == '' for f in files):
        return create_error_response("Aucun fichier sélectionné", 400)
    
    # Traiter chaque fichier
    file_paths = []
    processed_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Valider la taille du fichier
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if not validate_file_size(file_size):
                return create_error_response(
                    f"Le fichier {file.filename} est trop volumineux. Taille maximale: {format_file_size(Config.MAX_CONTENT_LENGTH)}",
                    400
                )
            
            # Générer un nom de fichier unique et sécurisé
            original_filename = secure_filename(file.filename)
            unique_filename = Config.generate_unique_filename(original_filename)
            filename = sanitize_filename(unique_filename)
            
            # Sauvegarder le fichier
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            file_paths.append(filepath)
            processed_files.append(original_filename)
            
            logger.info(f"Fichier téléversé: {original_filename} -> {filename}")
        else:
            logger.warning(f"Fichier non autorisé: {file.filename}")
    
    if not file_paths:
        return create_error_response("Aucun fichier PDF valide n'a été trouvé", 400)
    
    # Traiter les documents
    try:
        chunks_count, processed_files = document_manager.process_documents(file_paths)
        
        # Mettre à jour la session
        doc_count = document_manager.get_document_count()
        session_manager.set('doc_count', doc_count)
        session_manager.set('last_upload', datetime.now().isoformat())
        
        logger.info(f"{len(processed_files)} fichier(s) traité(s) avec succès. {chunks_count} morceaux créés.")
        
        return create_success_response({
            "files_processed": len(processed_files),
            "chunks_created": chunks_count,
            "file_names": processed_files,
            "doc_count": doc_count
        }, f"{len(processed_files)} fichier(s) traité(s) avec succès. {chunks_count} morceaux créés.")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement des documents: {e}")
        return create_error_response(f"Erreur lors du traitement des documents: {str(e)}", 500)

@app.route('/query', methods=['POST'])
@log_execution_time
def query():
    """Gère les questions de l'utilisateur et génère des réponses"""
    # Vérifier si des documents sont chargés
    if not document_manager.retriever:
        return jsonify(create_error_response("Veuillez d'abord téléverser des documents.", 400))
    
    # Récupérer la question
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify(create_error_response("La question est requise", 400))
    
    question = data['question'].strip()
    model_id = data.get('model', Config.DEFAULT_LLM)
    
    # Valider la question
    if not Config.validate_question(question):
        return jsonify(create_error_response(
            "Question invalide. La question doit contenir entre 3 et 1000 caractères.",
            400
        ))
    
    try:
        # Effectuer la requête RAG
        answer = document_manager.query(question, model_id=model_id)
        
        # Stocker la requête dans l'historique de session
        history = session_manager.get('query_history', [])
        history.append({
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        })
        
        # Garder seulement les 10 dernières requêtes
        if len(history) > 10:
            history = history[-10:]
        
        session_manager.set('query_history', history)
        
        logger.info(f"Réponse générée pour la question: {question[:50]}...")
        
        # Retourner la réponse directement sans décorateur
        return jsonify({
            'success': True,
            'data': {
                'answer': answer,
                'question': question,
                'doc_count': document_manager.get_document_count()
            },
            'error': None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la requête RAG: {e}")
        return jsonify(create_error_response("Erreur lors de la génération de la réponse. Veuillez réessayer.", 500))

@app.route('/status', methods=['GET'])
def get_status():
    """Récupère l'état actuel du système"""
    try:
        status = {
            'doc_count': document_manager.get_document_count(),
            'has_retriever': document_manager.retriever is not None,
            'last_upload': session_manager.get('last_upload'),
            'session_data': session_manager.get_all()
        }
        
        return create_success_response(status)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {e}")
        return create_error_response("Erreur lors de la récupération du statut", 500)

@app.route('/clear', methods=['POST'])
@handle_api_errors
def clear_data():
    """Supprime toutes les données et réinitialise le système"""
    try:
        # Supprimer les fichiers uploadés
        upload_folder = Config.UPLOAD_FOLDER
        if upload_folder.exists():
            import shutil
            for item in upload_folder.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        
        # Réinitialiser le document manager
        document_manager.clear_data()
        
        # Vider la session
        session_manager.clear()
        
        logger.info("Système réinitialisé avec succès")
        
        return create_success_response({
            'message': 'Système réinitialisé avec succès',
            'doc_count': 0
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation: {e}")
        return create_error_response("Erreur lors de la réinitialisation", 500)

@app.route('/history', methods=['GET'])
def get_history():
    """Récupère l'historique des requêtes"""
    try:
        history = session_manager.get('query_history', [])
        return create_success_response(history)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        return create_error_response("Erreur lors de la récupération de l'historique", 500)

@app.route('/health', methods=['GET'])
def health_check():
    """Vérifie la santé de l'application"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'components': {
                'document_manager': 'ok' if document_manager else 'error',
                'vector_store': 'ok' if document_manager.vectorstore else 'not_loaded',
                'retriever': 'ok' if document_manager.retriever else 'not_loaded'
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Gère les erreurs de fichier trop volumineux"""
    return create_error_response(
        f"Fichier trop volumineux. Taille maximale: {format_file_size(Config.MAX_CONTENT_LENGTH)}",
        413
    )

@app.errorhandler(404)
def not_found(e):
    """Gère les erreurs 404"""
    return create_error_response("Ressource non trouvée", 404)

@app.errorhandler(500)
def internal_error(e):
    """Gère les erreurs internes"""
    logger.error(f"Erreur interne du serveur: {e}")
    return create_error_response("Erreur interne du serveur", 500)

# --- Initialisation au démarrage ---
def initialize_app():
    """Initialise l'application au premier démarrage"""
    try:
        # Essayer de charger un vector store existant
        if document_manager.load_existing_vectorstore():
            doc_count = document_manager.get_document_count()
            session_manager.set('doc_count', doc_count)
            logger.info(f"Vector store existant chargé avec {doc_count} documents")
        else:
            logger.info("Aucun vector store existant trouvé. Nouvelle session démarrée.")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")

# Initialiser l'application au démarrage
initialize_app()

if __name__ == '__main__':
    # S'assurer que le répertoire des logs existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Démarrer l'application
    logger.info("Démarrage de l'application RAG...")
    app.run(
        host='0.0.0.0', 
        port=5001, 
        debug=True,
        threaded=True
    )