const form = document.getElementById('download-form');
const urlInput = document.getElementById('url-input');
const downloadBtn = document.getElementById('download-btn');
const resultsDiv = document.getElementById('results');
const loader = document.getElementById('loader');
const errorMessage = document.getElementById('error-message');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const url = urlInput.value;
    if (!url) { showError('Por favor, insira um link.'); return; }

    clearResults();
    showLoader(true);
    setButtonState(false);

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Ocorreu um erro.');
        }
        const data = await response.json();
        displayResult(data);
    } catch (error) {
        showError(error.message);
    } finally {
        showLoader(false);
        setButtonState(true);
    }
});

// Substitua a sua função displayResult antiga por esta
function displayResult(data) {
    const resultHTML = `
        <div class="result-item">
            <p>Título: ${data.title}</p>
            <a href="${data.url}" target="_blank" download>
                Seu vídeo está pronto! Clique para baixar
            </a>
        </div>
    `;
    resultsDiv.innerHTML = resultHTML;
    resultsDiv.classList.add('visible'); // Adiciona a classe para a animação
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

// Função ATUALIZADA para resetar a animação
function clearResults() {
    resultsDiv.innerHTML = '';
    errorMessage.classList.add('hidden');
    resultsDiv.classList.remove('visible'); // Remove a classe para resetar a animação
}

function showLoader(visible) {
    loader.classList.toggle('hidden', !visible);
}

function setButtonState(enabled) {
    downloadBtn.disabled = !enabled;
}
