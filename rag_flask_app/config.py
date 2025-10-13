import os
import secrets
from pathlib import Path

class Config:
    """Configuration centralisée de l'application RAG"""
    
    # Configuration de base
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Configuration des dossiers
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    PERSIST_DIRECTORY = BASE_DIR / 'chroma_db'
    
    # S'assurer que les dossiers existent
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    PERSIST_DIRECTORY.mkdir(exist_ok=True)
    
    # Configuration des modèles
    EMBEDDING_MODEL = "nomic-embed-text"
    LLM_MODEL = "openai/gpt-oss-20b:free"
    
    # Configuration du traitement de texte
    CHUNK_SIZE = 1500
    CHUNK_OVERLAP = 100
    
    # Configuration de la recherche
    RETRIEVE_K = 5
    RETRIEVE_FETCH_K = 10
    RETRIEVE_LAMBDA_MULT = 0.5
    
    # Configuration de l'API
    OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """Génère un nom de fichier unique pour éviter les conflits"""
        if '.' in original_filename:
            name, ext = original_filename.rsplit('.', 1)
            ext = ext.lower()
        else:
            name = original_filename
            ext = ''
        
        unique_id = secrets.token_hex(8)
        if ext:
            return f"{unique_id}.{ext}"
        return unique_id
    
    @staticmethod
    def is_allowed_file(filename):
        """Vérifie si le fichier a une extension autorisée"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_question(question):
        """Valide la question de l'utilisateur"""
        if not question or not isinstance(question, str):
            return False
        if len(question.strip()) < 3:
            return False
        if len(question) > 1000:  # Limite de longueur
            return False
        return True