import os
from flask import Flask, request, jsonify, render_template
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama

# --- Configuration de l'application Flask ---
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Configuration des modèles ---

# 1. Modèle d'embedding local avec Ollama
# Assurez-vous que le modèle gemma:2b est disponible dans Ollama : `ollama pull gemma:2b`
embeddings = OllamaEmbeddings(model="gemma:2b")

# 2. Modèle de chat (LLM) pour la génération de réponses
# Par défaut, nous utilisons un modèle local via Ollama pour un fonctionnement immédiat.
# Assurez-vous qu'Ollama est en cours d'exécution.
llm = ChatOllama(model="gemma:2b")

# --- (Optionnel) Configuration pour OpenRouter ---
# Pour utiliser un modèle plus puissant via OpenRouter, commentez la ligne `llm` ci-dessus
# et décommentez les lignes ci-dessous. N'oubliez pas de définir votre clé API.
#
# OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# if not OPENROUTER_API_KEY:
#     print("AVERTISSEMENT: La variable d'environnement OPENROUTER_API_KEY n'est pas définie.")
#
# llm = ChatOllama(
#     model="meta-llama/llama-3-8b-instruct",
#     base_url="https://openrouter.ai/api/v1",
#     api_key=OPENROUTER_API_KEY
# )

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

    answer = rag_chain.invoke(question)

    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)