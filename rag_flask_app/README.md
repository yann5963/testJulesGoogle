# Application RAG simple avec Flask, Ollama et ChromaDB

Cette application web permet de téléverser des documents PDF, de poser des questions sur leur contenu et d'obtenir des réponses générées par un grand modèle de langage (LLM). Elle utilise une approche RAG (Retrieval-Augmented Generation).

## Fonctionnalités

- **Interface Web Simple** : Téléversement de fichiers et dialogue via une interface web créée avec Flask.
- **Traitement de PDF** : Extrait le texte de fichiers PDF en utilisant `unstructured`.
- **Génération d'Embeddings Locale** : Crée des embeddings de vecteurs à partir du texte en utilisant le modèle `gemma:2b` via Ollama, s'exécutant localement.
- **Stockage Vectoriel en Mémoire** : Stocke les embeddings dans une base de données ChromaDB en mémoire pour une recherche de similarité rapide.
- **Génération de Réponses** : Utilise un LLM pour générer des réponses contextuelles basées sur les documents fournis.

## Prérequis

1.  **Python 3.8+** : Assurez-vous que Python et `pip` sont installés.
2.  **Ollama** : Vous devez installer Ollama et télécharger les modèles nécessaires.
    - [Télécharger Ollama](https://ollama.com/)
    - Après l'installation, exécutez les commandes suivantes dans votre terminal pour télécharger les modèles :
      ```bash
      # Modèle pour la génération d'embeddings
      ollama pull nomic-embed-text

      # Modèle pour la génération de réponses
      ollama pull gemma:2b
      ```
3.  **(Optionnel) Clé API OpenRouter** : Si vous souhaitez utiliser un modèle d'OpenRouter (comme Llama 3) au lieu du `gemma:2b` local pour la génération de réponses, vous aurez besoin d'une clé API.

## Installation

1.  **Clonez ou téléchargez le projet.**

2.  **Naviguez dans le dossier du projet :**
    ```bash
    cd rag_flask_app
    ```

3.  **Créez un environnement virtuel (recommandé) :**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows : venv\Scripts\activate
    ```

4.  **Installez les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```
    *Remarque : L'installation, en particulier pour `unstructured`, peut prendre plusieurs minutes.*

## Comment l'utiliser

1.  **Assurez-vous qu'Ollama est en cours d'exécution** avec le modèle `gemma:2b` disponible.

2.  **Lancez l'application Flask :**
    ```bash
    python app.py
    ```

3.  **Ouvrez votre navigateur** et allez à l'adresse `http://127.0.0.1:5001`.

4.  **Étape 1 : Téléverser des PDF**
    - Cliquez sur "Choisir les fichiers" et sélectionnez un ou plusieurs documents PDF.
    - Cliquez sur "Téléverser et Traiter".
    - Attendez le message de confirmation. Le traitement peut prendre un certain temps en fonction de la taille des fichiers.

5.  **Étape 2 : Poser une question**
    - Une fois les documents traités, tapez votre question dans le champ de saisie.
    - Cliquez sur "Envoyer".
    - La réponse générée par l'IA apparaîtra en dessous.

## (Optionnel) Utiliser OpenRouter pour la génération de réponses

Par défaut, l'application utilise `gemma:2b` via Ollama pour générer les réponses afin de fonctionner sans clé API. Pour utiliser un modèle plus puissant d'OpenRouter :

1.  **Obtenez une clé API** sur [OpenRouter.ai](https://openrouter.ai/).

2.  **Modifiez `app.py` :**
    - Dans la section `--- (Optionnel) Configuration pour OpenRouter ---`, commentez la ligne `llm = ChatOllama(model="gemma:2b")`.
    - Décommentez le bloc de code pour `ChatOpenRouter`.
    - Assurez-vous que votre clé API est définie dans une variable d'environnement nommée `OPENROUTER_API_KEY`.

      Le code à décommenter ressemble à ceci :
      ```python
      # OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
      # if not OPENROUTER_API_KEY:
      #     print("AVERTISSEMENT: La variable d'environnement OPENROUTER_API_KEY n'est pas définie ou est vide.")
      #
      # llm = ChatOpenRouter(
      #     model_name="meta-llama/llama-3-8b-instruct", # Modèle de votre choix
      #     openrouter_api_key=OPENROUTER_API_KEY
      # )
      ```
3.  Relancez l'application.