import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional
import json

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure le logging de l'application
    
    Args:
        log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Fichier de log optionnel
        
    Returns:
        Logger configuré
    """
    # Créer le logger
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Éviter les doublons de handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optionnel)
    if log_file:
        # S'assurer que le répertoire existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_execution_time(func: Callable) -> Callable:
    """
    Décorateur pour mesurer et logger le temps d'exécution d'une fonction
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = datetime.now()
        logger = logging.getLogger(__name__)
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.info(f"Fonction {func.__name__} exécutée en {execution_time:.2f} secondes")
            return result
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.error(f"Fonction {func.__name__} échouée après {execution_time:.2f} secondes: {e}")
            raise
    
    return wrapper

def handle_api_errors(func: Callable) -> Callable:
    """
    Décorateur pour gérer les erreurs API de manière uniforme
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        logger = logging.getLogger(__name__)
        
        try:
            result = func(*args, **kwargs)
            return {
                "success": True,
                "data": result,
                "error": None
            }
        except ValueError as e:
            error_msg = str(e)
            logger.warning(f"Erreur de validation: {error_msg}")
            return {
                "success": False,
                "data": None,
                "error": error_msg,
                "error_type": "validation"
            }
        except Exception as e:
            error_msg = f"Erreur interne: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": "Une erreur interne est survenue. Veuillez réessayer.",
                "error_type": "internal"
            }
    
    return wrapper

def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les problèmes de sécurité
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier sécurisé
    """
    # Caractères dangereux à remplacer
    dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    safe_filename = filename
    
    for char in dangerous_chars:
        safe_filename = safe_filename.replace(char, '_')
    
    # Limiter la longueur
    if len(safe_filename) > 255:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:255-len(ext)] + ext
    
    return safe_filename

def format_file_size(size_bytes: int) -> str:
    """
    Formate la taille d'un fichier en lecture humaine
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        Taille formatée (KB, MB, etc.)
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_file_size(file_size: int, max_size: int = 16 * 1024 * 1024) -> bool:
    """
    Valide la taille d'un fichier
    
    Args:
        file_size: Taille du fichier en octets
        max_size: Taille maximale autorisée en octets
        
    Returns:
        True si la taille est valide, False sinon
    """
    return 0 < file_size <= max_size

def create_error_response(message: str, status_code: int = 400, details: Optional[Dict] = None) -> Dict:
    """
    Crée une réponse d'erreur standardisée
    
    Args:
        message: Message d'erreur
        status_code: Code HTTP de statut
        details: Détails supplémentaires optionnels
        
    Returns:
        Dictionnaire de réponse d'erreur
    """
    response = {
        "success": False,
        "error": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response

def create_success_response(data: Any, message: Optional[str] = None) -> Dict:
    """
    Crée une réponse de succès standardisée
    
    Args:
        data: Données à retourner
        message: Message optionnel
        
    Returns:
        Dictionnaire de réponse de succès
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    return response

class SessionManager:
    """Gestionnaire de session simple pour stocker l'état de l'application"""
    
    def __init__(self):
        self._data = {}
        self._logger = logging.getLogger(__name__)
    
    def set(self, key: str, value: Any) -> None:
        """Stocke une valeur dans la session"""
        self._data[key] = value
        self._logger.debug(f"Valeur stockée dans la session: {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur depuis la session"""
        value = self._data.get(key, default)
        self._logger.debug(f"Valeur récupérée depuis la session: {key} = {value}")
        return value
    
    def remove(self, key: str) -> bool:
        """Supprime une valeur de la session"""
        if key in self._data:
            del self._data[key]
            self._logger.debug(f"Valeur supprimée de la session: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Vide toute la session"""
        self._data.clear()
        self._logger.debug("Session vidée")
    
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe dans la session"""
        return key in self._data
    
    def get_all(self) -> Dict[str, Any]:
        """Récupère toutes les données de la session"""
        return self._data.copy()