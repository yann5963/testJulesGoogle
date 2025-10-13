# Application RAG Avancée

Une application web Flask moderne pour la Recherche Augmentée par Génération (RAG) avec interface utilisateur intuitive et fonctionnalités avancées.

## 🚀 Fonctionnalités

### ✨ Caractéristiques Principales
- **Interface Web Moderne**: Design responsive avec expérience utilisateur optimisée
- **Traitement de Documents PDF**: Extraction et analyse intelligente de contenu
- **Recherche Sémantique**: Utilisation d'embeddings pour une recherche pertinente
- **Gestion de Session**: Persistance des données et historique des requêtes
- **Sécurité Renforcée**: Validation des entrées et gestion sécurisée des fichiers
- **Logging Complet**: Surveillance détaillée de l'application
- **Performance Optimisée**: Cache d'embeddings et paramètres optimisés

### 🛠️ Fonctionnalités Techniques
- **Architecture Modulaire**: Séparation claire des préoccupations
- **Gestion d'Erreurs**: Gestion centralisée des erreurs avec messages utilisateur
- **Validation Côté Client**: Validation des formulaires pour une meilleure UX
- **Drag & Drop**: Téléversement intuitif des fichiers
- **Historique des Requêtes**: Stockage et consultation des questions/réponses
- **Statut en Temps Réel**: Monitoring du système et des documents chargés

## 📁 Structure du Projet

```
rag_flask_app/
├── app.py                 # Application Flask principale
├── config.py             # Configuration centralisée
├── document_manager.py   # Gestion des documents et embeddings
├── utils.py              # Utilitaires et fonctions helpers
├── requirements.txt      # Dépendances Python
├── .env                  # Variables d'environnement
├── .env_example         # Exemple de configuration
├── templates/
│   └── index.html        # Template principal
├── static/
│   ├── style.css         # Styles CSS
│   └── script.js         # JavaScript interactif
├── uploads/              # Dossier des fichiers uploadés
├── chroma_db/            # Base de données vectorielle
└── logs/                 # Fichiers de log
```

## 🛠️ Installation

### Prérequis
- Python 3.8+
- Ollama installé avec le modèle `nomic-embed-text`
- Clé API OpenRouter

### Étapes d'Installation

1. **Cloner le dépôt**
```bash
git clone <repository-url>
cd rag_flask_app
```

2. **Créer l'environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer Ollama**
```bash
ollama pull nomic-embed-text
```

5. **Configurer les variables d'environnement**
```bash
cp .env_example .env
# Éditer .env avec votre clé API OpenRouter
```

6. **Lancer l'application**
```bash
python app.py
```

L'application sera disponible à l'adresse: `http://localhost:5001`

## 🔧 Configuration

### Variables d'Environnement (.env)
```env
OPENROUTER_API_KEY=votre_clé_api_openrouter
SECRET_KEY=clé_secrète_aleatoire_optionnelle
```

### Paramètres Configurables (config.py)
- `CHUNK_SIZE`: Taille des chunks de texte (1500 par défaut)
- `CHUNK_OVERLAP`: Chevauchement des chunks (100 par défaut)
- `RETRIEVE_K`: Nombre de documents à récupérer (5 par défaut)
- `MAX_CONTENT_LENGTH`: Taille maximale des fichiers (16MB par défaut)
- `EMBEDDING_MODEL`: Modèle d'embedding (nomic-embed-text par défaut)
- `LLM_MODEL`: Modèle LLM (openai/gpt-oss-20b:free par défaut)

## 📚 Utilisation

### 1. Téléverser des Documents
- Cliquez sur "Choisir des fichiers PDF" ou glissez-déposez les fichiers
- Sélectionnez un ou plusieurs fichiers PDF
- Cliquez sur "Traiter les fichiers"

### 2. Poser des Questions
- Une fois les documents traités, entrez votre question
- Cliquez sur "Envoyer" ou appuyez sur Entrée
- La réponse s'affichera avec la source pertinente

### 3. Fonctionnalités Avancées
- **Historique**: Consultez vos requêtes précédentes
- **Statut**: Vérifiez l'état du système
- **Effacer**: Réinitialisez toute l'application
- **Copier**: Copiez les réponses dans le presse-papiers

## 🔍 API Endpoints

### Endpoints Principaux
- `GET /` - Page d'accueil
- `POST /upload` - Téléverser et traiter des fichiers
- `POST /query` - Poser une question
- `GET /status` - Obtenir le statut du système
- `POST /clear` - Réinitialiser le système
- `GET /history` - Obtenir l'historique des requêtes
- `GET /health` - Vérifier la santé de l'application

### Format des Réponses
Toutes les réponses API suivent un format standardisé:
```json
{
  "success": true,
  "data": {...},
  "error": null,
  "timestamp": "2024-01-01T00:00:00"
}
```

## 🚀 Déploiement

### Développement
```bash
python app.py
```

### Production
Utilisez un serveur WSGI comme Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5001

CMD ["python", "app.py"]
```

## 📊 Performance et Optimisation

### Caractéristiques d'Optimisation
- **Cache d'Embeddings**: Évite les recalculs coûteux
- **Chunking Optimisé**: Paramètres ajustés pour le meilleur équilibre
- **Recherche MMR**: Maximal Marginal Relevance pour des résultats pertinents
- **Logging Structuré**: Surveillance des performances
- **Gestion de Mémoire**: Libération des ressources inutilisées

### Bonnes Pratiques
- Limiter le nombre de documents simultanés
- Utiliser des fichiers de taille raisonnable (< 10MB)
- Monitorer l'utilisation de la mémoire
- Sauvegarder régulièrement la base de données

## 🔐 Sécurité

### Mesures de Sécurité
- Validation des entrées côté serveur et client
- Nettoyage des noms de fichiers
- Limitation de la taille des uploads
- Gestion sécurisée des clés API
- Protection contre les injections

## 🐛 Dépannage

### Problèmes Courants

1. **Erreur de clé API**
   - Vérifiez que la clé OpenRouter est correcte dans `.env`
   - Assurez-vous que le quota n'est pas dépassé

2. **Problèmes d'embedding**
   - Vérifiez qu'Ollama est en cours d'exécution
   - Confirmez que le modèle `nomic-embed-text` est installé

3. **Erreurs de mémoire**
   - Réduisez la taille des fichiers
   - Augmentez la taille de la swap si nécessaire
   - Redémarrez l'application

4. **Problèmes de performance**
   - Vérifiez l'utilisation du CPU et de la mémoire
   - Consultez les fichiers de log pour les erreurs

### Logs
Les logs sont disponibles dans le dossier `logs/`:
- `rag_app.log`: Logs de l'application
- Format structuré avec timestamps et niveaux de gravité

## 🤝 Contribuer

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Faites un commit de vos changements
4. Poussez vers la branche
5. Créez un Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🙏 Remerciements

- [LangChain](https://github.com/langchain-ai/langchain) pour le framework RAG
- [ChromaDB](https://www.trychroma.com/) pour la base de données vectorielle
- [Ollama](https://ollama.com/) pour l'inférence locale
- [OpenRouter](https://openrouter.ai/) pour l'accès aux modèles avancés

---

**Version**: 1.0.0  
**Dernière mise à jour**: 2024