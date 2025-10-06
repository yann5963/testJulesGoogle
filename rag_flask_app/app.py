import os
from flask import Flask, request, jsonify, render_template
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
# Import des classes de LLM
#from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
# Gestion des variables d'environnement
from dotenv import load_dotenv
import pathlib

# --- Configuration de l'application Flask ---
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Configuration des modèles ---

# 1. Modèle d'embedding local avec Ollama
# J'utilise nomic-embed-text, un modèle spécialisé pour la création d'embeddings.
# Assurez-vous que le modèle est disponible dans Ollama : `ollama pull nomic-embed-text`
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 2. Modèle de chat via OpenRouter
# OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# Définir le chemin vers le fichier .env à la racine du projet
current_dir = pathlib.Path(__file__).parent.absolute()
env_path = current_dir / '.env'
print(f"Chemin du fichier .env : {env_path}")

# Charger les variables d'environnement depuis le fichier .env
load_dotenv(dotenv_path=env_path)

# Récupérer la clé
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
print(f"Clé OPENROUTER_API_KEY chargée : {'Oui' if OPENROUTER_API_KEY else 'Non'}")

if not OPENROUTER_API_KEY:
     print("AVERTISSEMENT: La variable d'environnement OPENROUTER_API_KEY n'est pas définie ou est vide. Veuillez définir cette variable dans le fichier .env pour utiliser OpenRouter.")
     # Optionnel : vous pouvez choisir de stopper l'application ou d'utiliser le modèle local par défaut
     # Ici, nous continuons avec une clé vide, ce qui provoquera une erreur si l'utilisateur essaie de l'utiliser.
     exit(1)

llm = ChatOpenAI(
    model="openai/gpt-oss-20b:free",
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1"
)

# --- Variables globales pour le stockage des données ---
vectorstore = None
retriever = None

# --- Routes de l'application ---
@app.route('/')
def index():
    """Affiche la page d'accueil."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Gère le téléversement et le traitement des fichiers PDF."""
    global vectorstore, retriever

    if 'files[]' not in request.files:
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    files = request.files.getlist('files[]')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    all_chunks = []
    for file in files:
        if file and file.filename.endswith('.pdf'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            loader = UnstructuredFileLoader(filepath)
            docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(docs)
            all_chunks.extend(chunks)

    if not all_chunks:
        return jsonify({"error": "Impossible d'extraire le texte des fichiers PDF fournis."}), 400

    vectorstore = Chroma.from_documents(documents=all_chunks, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    return jsonify({"message": f"{len(files)} fichier(s) traité(s) avec succès. {len(all_chunks)} morceaux créés."})

@app.route('/query', methods=['POST'])
def query():
    """Gère les questions de l'utilisateur et génère des réponses."""
    global retriever

    if not retriever:
        return jsonify({"error": "Veuillez d'abord téléverser des documents."}), 400

    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({"error": "La question ne peut pas être vide."}), 400

    template = """
    Vous êtes un assistant IA. Utilisez les morceaux de contexte suivants pour répondre à la question.
    Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse.
    Utilisez au maximum trois phrases et soyez concis.

    Contexte : {context}
    Question : {question}
    Réponse utile :
    """
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    try:
        answer = rag_chain.invoke(question)
        return jsonify({"answer": answer})
    except Exception as e:
        # Capturer les erreurs d'API (par exemple, clé API incorrecte)
        return jsonify({"error": f"Erreur lors de l'appel au LLM : {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)