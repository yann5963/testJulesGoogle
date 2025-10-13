// Variables globales
let selectedFiles = [];
let isProcessing = false;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    checkSystemStatus();
});

// Initialisation de l'application
function initializeApp() {
    // Mettre à jour le compteur de documents
    updateDocumentCount();
    
    // Configurer le drag and drop
    setupDragAndDrop();
    
    // Vérifier l'état du système
    checkSystemStatus();
}

// Configuration des écouteurs d'événements
function setupEventListeners() {
    // Formulaire de téléversement
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    
    uploadForm.addEventListener('submit', handleUpload);
    fileInput.addEventListener('change', handleFileSelection);
    
    // Formulaire de requête
    const queryForm = document.getElementById('query-form');
    queryForm.addEventListener('submit', handleQuery);
    
    // Boutons d'action
    document.getElementById('clear-btn').addEventListener('click', handleClear);
    document.getElementById('status-btn').addEventListener('click', handleStatus);
    document.getElementById('history-btn').addEventListener('click', handleHistory);
    document.getElementById('close-history').addEventListener('click', closeHistory);
    document.getElementById('copy-answer').addEventListener('click', copyAnswer);
    
    // Modales
    document.getElementById('close-error').addEventListener('click', closeErrorModal);
    
    // Fermer les modales en cliquant en dehors
    window.addEventListener('click', function(event) {
        const errorModal = document.getElementById('error-modal');
        const loadingModal = document.getElementById('loading-modal');
        
        if (event.target === errorModal) {
            closeErrorModal();
        }
        if (event.target === loadingModal) {
            closeLoadingModal();
        }
    });
}

// Configuration du drag and drop
function setupDragAndDrop() {
    const fileInputLabel = document.querySelector('.file-input-label');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileInputLabel.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileInputLabel.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileInputLabel.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        fileInputLabel.style.borderColor = '#0056b3';
        fileInputLabel.style.background = '#e3f2fd';
    }
    
    function unhighlight(e) {
        fileInputLabel.style.borderColor = '#007bff';
        fileInputLabel.style.background = '#f8f9fa';
    }
    
    fileInputLabel.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
}

// Gestion des fichiers sélectionnés
function handleFileSelection(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    selectedFiles = [];
    
    Array.from(files).forEach(file => {
        if (file.type === 'application/pdf') {
            selectedFiles.push(file);
            addFileToList(file);
        } else {
            showError(`Le fichier ${file.name} n'est pas un PDF valide.`);
        }
    });
    
    updateUploadButton();
}

// Ajouter un fichier à la liste
function addFileToList(file) {
    const fileList = document.getElementById('file-list');
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    
    const fileSize = formatFileSize(file.size);
    
    fileItem.innerHTML = `
        <div class="file-item-info">
            <i class="fas fa-file-pdf" style="color: #dc3545;"></i>
            <span class="file-item-name">${file.name}</span>
            <span class="file-item-size">${fileSize}</span>
        </div>
        <button type="button" class="file-item-remove" onclick="removeFile('${file.name}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    fileList.appendChild(fileItem);
}

// Supprimer un fichier de la liste
function removeFile(fileName) {
    selectedFiles = selectedFiles.filter(file => file.name !== fileName);
    updateFileList();
    updateUploadButton();
}

// Mettre à jour la liste des fichiers
function updateFileList() {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';
    
    selectedFiles.forEach(file => {
        addFileToList(file);
    });
}

// Mettre à jour le bouton de téléversement
function updateUploadButton() {
    const uploadButton = document.querySelector('#upload-form button[type="submit"]');
    const clearButton = document.getElementById('clear-btn');
    
    if (selectedFiles.length > 0) {
        uploadButton.disabled = false;
        clearButton.style.display = 'inline-flex';
    } else {
        uploadButton.disabled = true;
        clearButton.style.display = 'none';
    }
}

// Formater la taille du fichier
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Gérer le téléversement
async function handleUpload(e) {
    e.preventDefault();
    
    if (selectedFiles.length === 0) {
        showError('Veuillez sélectionner au moins un fichier PDF.');
        return;
    }
    
    if (isProcessing) return;
    
    isProcessing = true;
    showLoading('Préparation des fichiers...');
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(result.message);
            selectedFiles = [];
            updateFileList();
            updateDocumentCount();
            updateUploadButton();
            
            // Mettre à jour le statut
            updateSystemStatus();
        } else {
            showError(result.error || 'Erreur lors du téléversement.');
        }
    } catch (error) {
        showError('Erreur réseau. Veuillez réessayer.');
        console.error('Upload error:', error);
    } finally {
        isProcessing = false;
        closeLoadingModal();
    }
}

// Gérer la requête
async function handleQuery(e) {
    e.preventDefault();
    
    const questionInput = document.getElementById('question');
    const question = questionInput.value.trim();
    
    if (!question) {
        showError('Veuillez entrer une question.');
        return;
    }
    
    if (isProcessing) return;
    
    isProcessing = true;
    showLoading('Recherche de la réponse...');
    
    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        console.log('Statut de la réponse:', response.status, response.statusText);
        const result = await response.json();
        console.log('Réponse du serveur:', result);
        
        // Vérifier si la réponse est OK
        if (response.ok) {
            // La structure est : {success: true, data: {answer: "...", question: "...", doc_count: X}}
            if (result.data && result.data.answer) {
                console.log('Réponse à afficher:', result.data.answer);
                displayAnswer(result.data.answer);
                questionInput.value = '';
            } else {
                console.error('Réponse serveur OK mais pas de réponse:', result);
                showError('Le serveur a répondu mais n\'a pas fourni de réponse.');
            }
        } else {
            console.error('Erreur de la réponse:', result);
            showError(result.error || 'Erreur lors de la requête.');
        }
    } catch (error) {
        showError('Erreur réseau. Veuillez réessayer.');
        console.error('Query error:', error);
    } finally {
        isProcessing = false;
        closeLoadingModal();
    }
}

// Afficher la réponse
function displayAnswer(answer) {
    console.log('displayAnswer appelée avec:', answer);
    const responseContainer = document.getElementById('response-container');
    const answerElement = document.getElementById('answer');
    
    if (!responseContainer) {
        console.error('Element response-container non trouvé');
        return;
    }
    
    if (!answerElement) {
        console.error('Element answer non trouvé');
        return;
    }
    
    answerElement.textContent = answer;
    responseContainer.style.display = 'block';
    
    console.log('Réponse affichée dans le DOM');
    
    // Faire défiler vers la réponse
    responseContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Copier la réponse
function copyAnswer() {
    const answerElement = document.getElementById('answer');
    const answer = answerElement.textContent;
    
    navigator.clipboard.writeText(answer).then(() => {
        showSuccess('Réponse copiée dans le presse-papiers!');
    }).catch(err => {
        showError('Erreur lors de la copie.');
        console.error('Copy error:', err);
    });
}

// Gérer l'effacement
async function handleClear() {
    if (!confirm('Êtes-vous sûr de vouloir supprimer tous les documents et réinitialiser le système?')) {
        return;
    }
    
    showLoading('Réinitialisation en cours...');
    
    try {
        const response = await fetch('/clear', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(result.message);
            updateDocumentCount();
            updateSystemStatus();
            document.getElementById('response-container').style.display = 'none';
        } else {
            showError(result.error || 'Erreur lors de la réinitialisation.');
        }
    } catch (error) {
        showError('Erreur réseau. Veuillez réessayer.');
        console.error('Clear error:', error);
    } finally {
        closeLoadingModal();
    }
}

// Gérer le statut
async function handleStatus() {
    showLoading('Récupération du statut...');
    
    try {
        const response = await fetch('/status');
        const result = await response.json();
        
        if (response.ok) {
            let statusHtml = `
                <div class="status-info">
                    <h3>Statut du système</h3>
                    <p><strong>Documents chargés:</strong> ${result.data.doc_count}</p>
                    <p><strong>Système prêt:</strong> ${result.data.has_retriever ? 'Oui' : 'Non'}</p>
                    <p><strong>Dernier téléversement:</strong> ${result.data.last_upload || 'Aucun'}</p>
                </div>
            `;
            
            showStatusMessage(statusHtml, 'info');
        } else {
            showError(result.error || 'Erreur lors de la récupération du statut.');
        }
    } catch (error) {
        showError('Erreur réseau. Veuillez réessayer.');
        console.error('Status error:', error);
    } finally {
        closeLoadingModal();
    }
}

// Gérer l'historique
async function handleHistory() {
    showLoading('Récupération de l\'historique...');
    
    try {
        const response = await fetch('/history');
        const result = await response.json();
        
        if (response.ok) {
            displayHistory(result.data);
        } else {
            showError(result.error || 'Erreur lors de la récupération de l\'historique.');
        }
    } catch (error) {
        showError('Erreur réseau. Veuillez réessayer.');
        console.error('History error:', error);
    } finally {
        closeLoadingModal();
    }
}

// Afficher l'historique
function displayHistory(history) {
    const historySection = document.getElementById('history-section');
    const historyList = document.getElementById('history-list');
    
    historyList.innerHTML = '';
    
    if (history.length === 0) {
        historyList.innerHTML = '<p>Aucune requête dans l\'historique.</p>';
    } else {
        history.forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            
            const date = new Date(item.timestamp).toLocaleString('fr-FR');
            
            historyItem.innerHTML = `
                <div class="history-item-question">${item.question}</div>
                <div class="history-item-answer">${item.answer}</div>
                <div class="history-item-time">${date}</div>
            `;
            
            historyList.appendChild(historyItem);
        });
    }
    
    historySection.style.display = 'block';
    historySection.scrollIntoView({ behavior: 'smooth' });
}

// Fermer l'historique
function closeHistory() {
    document.getElementById('history-section').style.display = 'none';
}

// Mettre à jour le compteur de documents
async function updateDocumentCount() {
    try {
        const response = await fetch('/status');
        const result = await response.json();
        
        if (response.ok) {
            const docCount = result.data.doc_count;
            document.getElementById('doc-count').innerHTML = `
                <i class="fas fa-file-pdf"></i> Documents: ${docCount}
            `;
        }
    } catch (error) {
        console.error('Error updating document count:', error);
    }
}

// Mettre à jour le statut du système
async function updateSystemStatus() {
    try {
        const response = await fetch('/health');
        const result = await response.json();
        
        const statusElement = document.getElementById('system-status');
        const statusIcon = statusElement.querySelector('i');
        
        if (result.status === 'healthy') {
            statusIcon.style.color = '#28a745';
            statusElement.innerHTML = `
                <i class="fas fa-circle" style="color: #28a745;"></i> Système: Actif
            `;
        } else {
            statusIcon.style.color = '#dc3545';
            statusElement.innerHTML = `
                <i class="fas fa-circle" style="color: #dc3545;"></i> Système: Erreur
            `;
        }
    } catch (error) {
        console.error('Error updating system status:', error);
    }
}

// Vérifier l'état du système
async function checkSystemStatus() {
    await updateDocumentCount();
    await updateSystemStatus();
}

// Afficher le modal de chargement
function showLoading(message = 'Traitement en cours...') {
    const modal = document.getElementById('loading-modal');
    const messageElement = document.getElementById('loading-message');
    
    messageElement.textContent = message;
    modal.style.display = 'block';
}

// Fermer le modal de chargement
function closeLoadingModal() {
    document.getElementById('loading-modal').style.display = 'none';
}

// Afficher le modal d'erreur
function showError(message) {
    const modal = document.getElementById('error-modal');
    const messageElement = document.getElementById('error-message');
    
    messageElement.textContent = message;
    modal.style.display = 'block';
}

// Fermer le modal d'erreur
function closeErrorModal() {
    document.getElementById('error-modal').style.display = 'none';
}

// Afficher un message de statut
function showStatusMessage(html, type = 'info') {
    const statusElement = document.getElementById('upload-status');
    statusElement.innerHTML = html;
    statusElement.className = `status-message status-${type}`;
    
    // Auto-effacer après 5 secondes
    setTimeout(() => {
        statusElement.innerHTML = '';
        statusElement.className = 'status-message';
    }, 5000);
}

// Afficher un message de succès
function showSuccess(message) {
    const statusElement = document.getElementById('upload-status');
    statusElement.innerHTML = `
        <div class="status-success">
            <i class="fas fa-check-circle"></i> ${message}
        </div>
    `;
    
    // Auto-effacer après 5 secondes
    setTimeout(() => {
        statusElement.innerHTML = '';
        statusElement.className = 'status-message';
    }, 5000);
}