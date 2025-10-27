import os
import logging
from pathlib import Path
from typing import List, Optional
from functools import lru_cache
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
try:
    # Version moderne de langchain-ollama
    from langchain_ollama import OllamaEmbeddings
except ImportError:
    # Fallback pour la version dépréciée
    from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from config import Config
from utils import SessionManager

logger = logging.getLogger(__name__)

class DocumentManager:
    """Gestionnaire de documents pour le système RAG"""
    
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=Config.EMBEDDING_MODEL)
        self.vectorstore = None
        self.retriever = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"DocumentManager initialisé avec le modèle: {Config.EMBEDDING_MODEL}")
    
    @lru_cache(maxsize=1000)
    def _get_embedding(self, text: str) -> List[float]:
        """Mise en cache des embeddings pour éviter les recalculs"""
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'embedding: {e}")
            raise
    
    def process_documents(self, file_paths: List[str]) -> tuple[int, List[str]]:
        """
        Traite les documents PDF et crée le vector store
        
        Args:
            file_paths: Liste des chemins vers les fichiers PDF
            
        Returns:
            tuple: (nombre de chunks créés, liste des noms de fichiers traités)
        """
        all_chunks = []
        processed_files = []
        
        for file_path in file_paths:
            try:
                if not os.path.exists(file_path):
                    logger.warning(f"Fichier non trouvé: {file_path}")
                    continue
                
                filename = os.path.basename(file_path)
                logger.info(f"Traitement du fichier: {filename}")
                
                # Charger le document
                loader = UnstructuredFileLoader(file_path)
                docs = loader.load()
                
                if not docs:
                    logger.warning(f"Aucun contenu extrait du fichier: {filename}")
                    continue
                
                # Diviser en chunks
                chunks = self.text_splitter.split_documents(docs)
                all_chunks.extend(chunks)
                processed_files.append(filename)
                
                logger.info(f"Fichier {filename} traité: {len(chunks)} chunks créés")
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du fichier {file_path}: {e}")
                continue
        
        if not all_chunks:
            raise ValueError("Aucun document n'a pu être traité avec succès")
        
        # Créer le vector store
        try:
            self.vectorstore = Chroma.from_documents(
                documents=all_chunks,
                embedding=self.embeddings,
                persist_directory=str(Config.PERSIST_DIRECTORY)
            )
            
            # Configurer le retriever
            self.retriever = self.vectorstore.as_retriever(
                search_type="mmr",  # Maximal Marginal Relevance
                search_kwargs={
                    "k": Config.RETRIEVE_K,
                    "fetch_k": Config.RETRIEVE_FETCH_K,
                    "lambda_mult": Config.RETRIEVE_LAMBDA_MULT
                }
            )
            
            logger.info(f"Vector store créé avec {len(all_chunks)} chunks")
            return len(all_chunks), processed_files
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du vector store: {e}")
            raise
    
    def load_existing_vectorstore(self) -> bool:
        """Charge un vector store existant si disponible"""
        try:
            if Config.PERSIST_DIRECTORY.exists():
                self.vectorstore = Chroma(
                    persist_directory=str(Config.PERSIST_DIRECTORY),
                    embedding_function=self.embeddings
                )
                
                if self.vectorstore:
                    self.retriever = self.vectorstore.as_retriever(
                        search_type="mmr",
                        search_kwargs={
                            "k": Config.RETRIEVE_K,
                            "fetch_k": Config.RETRIEVE_FETCH_K,
                            "lambda_mult": Config.RETRIEVE_LAMBDA_MULT
                        }
                    )
                    logger.info("Vector store existant chargé avec succès")
                    return True
        except Exception as e:
            logger.error(f"Erreur lors du chargement du vector store existant: {e}")
        
        return False
    
    def query(self, question: str, model_id: str = Config.DEFAULT_LLM) -> str:
        """Effectue une requête RAG"""
        if not self.retriever:
            raise ValueError("Aucun document n'a été chargé. Veuillez d'abord téléverser des documents.")
        
        if not Config.validate_question(question):
            raise ValueError("Question invalide")
        
        try:
            # Template amélioré
            template = """
            Vous êtes un assistant IA expert. Utilisez exclusivement les morceaux de contexte fournis 
            pour répondre à la question de manière précise et concise.
            
            Règles importantes:
            1. Répondez uniquement en utilisant l'information du contexte fourni
            2. Si vous ne trouvez pas la réponse dans le contexte, dites simplement "Je ne trouve pas cette information dans les documents fournis"
            3. Soyez concis (maximum 3 phrases)
            4. Citez les sources pertinentes si possible
            
            Contexte : {context}
            Question : {question}
            Réponse :
            """
            
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.runnables import RunnablePassthrough
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_template(template)
            
            def format_docs(docs):
                return "\n\n".join([f"Document {i+1}: {doc.page_content}" for i, doc in enumerate(docs)])
            
            llm = self._get_llm(model_id)
            if not llm:
                raise ValueError(f"Modèle LLM non valide: {model_id}")

            rag_chain = (
                {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            answer = rag_chain.invoke(question)
            return answer
            
        except Exception as e:
            logger.error(f"Erreur lors de la requête RAG: {e}")
            raise
    
    def _get_llm(self, model_id: str):
        """Récupère le LLM configuré"""
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        import pathlib
        
        model_config = Config.LLM_MODELS.get(model_id)
        if not model_config:
            logger.error(f"Configuration non trouvée pour le modèle: {model_id}")
            return None

        # Charger les variables d'environnement
        current_dir = pathlib.Path(__file__).parent.absolute()
        env_path = current_dir / '.env'
        load_dotenv(dotenv_path=env_path)
        
        api_key = "ollama" # Pas de clé pour un ollama local
        if model_id == "openrouter":
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError("La clé API OpenRouter n'est pas configurée")
        
        return ChatOpenAI(
            model=model_config["name"],
            openai_api_key=api_key,
            openai_api_base=model_config["api_base"],
            temperature=0.2,
            max_tokens=500
        )
    
    def get_document_count(self) -> Optional[int]:
        """Récupère le nombre de documents dans le vector store"""
        if self.vectorstore:
            try:
                return self.vectorstore._collection.count()
            except:
                return None
        return None
    
    def clear_data(self):
        """Supprime toutes les données du vector store"""
        try:
            if self.vectorstore:
                self.vectorstore.delete_collection()
                self.vectorstore = None
                self.retriever = None
                
                # Supprimer le répertoire persistant
                if Config.PERSIST_DIRECTORY.exists():
                    import shutil
                    shutil.rmtree(Config.PERSIST_DIRECTORY)
                
                logger.info("Données du vector store supprimées avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des données: {e}")
            raise
    
    def reset_vectorstore(self):
        """Réinitialise uniquement le vector store mais conserve les fichiers uploadés"""
        try:
            # Supprimer le vector store existant
            if self.vectorstore:
                self.vectorstore.delete_collection()
                self.vectorstore = None
                self.retriever = None
            
            # Supprimer le répertoire persistant
            if Config.PERSIST_DIRECTORY.exists():
                import shutil
                shutil.rmtree(Config.PERSIST_DIRECTORY)
            
            # Vider l'historique de session
            session_manager = SessionManager()
            session_manager.remove('query_history')
            session_manager.remove('last_upload')
            
            logger.info("Vector store réinitialisé avec succès (fichiers conservés)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation du vector store: {e}")
            return False