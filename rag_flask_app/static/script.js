document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const statusDiv = document.getElementById('upload-status');
    statusDiv.textContent = 'Téléversement et traitement en cours...';

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    statusDiv.textContent = result.message || result.error;
});

document.getElementById('query-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const question = document.getElementById('question').value;
    const answerP = document.getElementById('answer');
    answerP.textContent = 'Recherche de la réponse...';

    const response = await fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: question })
    });

    const result = await response.json();
    if (result.error) {
        answerP.textContent = `Erreur : ${result.error}`;
    } else {
        answerP.textContent = result.answer;
    }
});