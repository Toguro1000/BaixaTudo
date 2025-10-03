const form = document.getElementById('download-form');
const urlInput = document.getElementById('url-input');
const downloadBtn = document.getElementById('download-btn');
const resultsDiv = document.getElementById('results');
const loader = document.getElementById('loader');
const errorMessage = document.getElementById('error-message');
const statusMessage = document.getElementById('status-message');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const url = urlInput.value.trim();

    // Validação de URL no Front-end
    try {
        new URL(url);
    } catch (_) {
        showError('Por favor, insira um link (URL) válido.');
        return;
    }

    clearAll();
    showLoader(true);
    setButtonState(false);

    try {
        const response = await fetch('/api/v1/fetch-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Ocorreu um erro desconhecido.');
        }

        showLoader(false);
        showStatus('Gerando links de download...');
        displayResult(data);

    } catch (error) {
        showLoader(false);
        showError(error.message);
    } finally {
        setButtonState(true);
    }
});

function displayResult(data) {
    let resultHTML = `<div class="result-item"><p>Título: ${data.title}</p>`;
    
    data.formats.forEach(format => {
        // Agora o link aponta para o nosso endpoint de proxy-download
        const proxyUrl = `/api/v1/proxy-download?url=${encodeURIComponent(format.download_url)}`;
        resultHTML += `<a href="${proxyUrl}" target="_blank">Baixar ${format.quality} (${format.ext}) - ${format.size_mb} MB</a>`;
    });

    resultHTML += `</div>`;
    resultsDiv.innerHTML = resultHTML;
    showStatus(''); // Limpa a mensagem de status
    resultsDiv.classList.add('visible');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function showStatus(message) {
    if (message) {
        statusMessage.textContent = message;
        statusMessage.classList.remove('hidden');
    } else {
        statusMessage.classList.add('hidden');
    }
}

function clearAll() {
    resultsDiv.innerHTML = '';
    errorMessage.classList.add('hidden');
    resultsDiv.classList.remove('visible');
    statusMessage.classList.add('hidden');
}

function showLoader(visible) {
    loader.classList.toggle('hidden', !visible);
}

function setButtonState(enabled) {
    downloadBtn.disabled = !enabled;
}

