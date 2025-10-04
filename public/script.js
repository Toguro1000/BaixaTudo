const form = document.getElementById('download-form');
const urlInput = document.getElementById('url-input');
const downloadBtn = document.getElementById('download-btn');
const resultsDiv = document.getElementById('results');
const loader = document.getElementById('loader');
const errorMessage = document.getElementById('error-message');
const statusMessage = document.getElementById('status-message');

// Event listener para o formulário principal
form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const url = urlInput.value.trim();
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
        displayResult(data);
    } catch (error) {
        showLoader(false);
        showError(error.message);
    } finally {
        setButtonState(true);
    }
});

// Função ATUALIZADA para mostrar o botão que INICIA o download
function displayResult(data) {
    const proxyUrl = `/api/v1/proxy-download?url=${encodeURIComponent(data.download_url)}&ext=${data.ext}`;
    
    // Cria um novo elemento de progresso
    const progressHTML = `
        <div id="progress-container" style="display: none; margin-top: 1rem;">
            <div id="progress-bar" style="width: 0%; height: 24px; background-color: var(--success-color); border-radius: 6px; text-align: center; color: white; line-height: 24px; font-weight: bold;">0%</div>
            <p id="progress-text" style="text-align: center; margin-top: 0.5rem; color: var(--light-text-color);"></p>
        </div>
    `;

    const resultHTML = `
        <div class="result-item">
            <p>Título: ${data.title}</p>
            <button id="start-download-btn" class="download-button">Seu vídeo está pronto! Clique para baixar</button>
            ${progressHTML}
        </div>
    `;
    resultsDiv.innerHTML = resultHTML;
    resultsDiv.classList.add('visible');

    // Adiciona o event listener ao novo botão de download
    document.getElementById('start-download-btn').addEventListener('click', () => {
        downloadWithProgress(proxyUrl, data.title);
    });
}

// NOVA FUNÇÃO para o download com barra de progresso
async function downloadWithProgress(url, filename) {
    const startBtn = document.getElementById('start-download-btn');
    startBtn.disabled = true;
    startBtn.textContent = 'A baixar...';

    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    progressContainer.style.display = 'block';

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Erro de rede: ${response.statusText}`);
        }

        const contentLength = +response.headers.get('Content-Length');
        const reader = response.body.getReader();
        let receivedLength = 0;
        let chunks = [];
        
        while(true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            chunks.push(value);
            receivedLength += value.length;
            
            if (contentLength) {
                const percentage = Math.round((receivedLength / contentLength) * 100);
                progressBar.style.width = `${percentage}%`;
                progressBar.textContent = `${percentage}%`;
                
                const receivedMB = (receivedLength / (1024 * 1024)).toFixed(2);
                const totalMB = (contentLength / (1024 * 1024)).toFixed(2);
                progressText.textContent = `Baixado: ${receivedMB} MB / ${totalMB} MB`;
            }
        }
        
        progressBar.textContent = '100% - A processar...';
        const blob = new Blob(chunks);
        const objectUrl = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = objectUrl;
        a.download = `${filename}.mp4` || 'video.mp4';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(objectUrl);

        startBtn.textContent = 'Download Concluído!';

    } catch (error) {
        showError('Falha ao baixar o ficheiro. Tente novamente.');
        startBtn.disabled = false;
        startBtn.textContent = 'Tentar Novamente';
    }
}

// Funções de ajuda (sem alterações)
function showError(message) { errorMessage.textContent = message; errorMessage.classList.remove('hidden'); }
function clearAll() { resultsDiv.innerHTML = ''; errorMessage.classList.add('hidden'); resultsDiv.classList.remove('visible'); if(statusMessage) statusMessage.classList.add('hidden');}
function showLoader(visible) { loader.classList.toggle('hidden', !visible); }
function setButtonState(enabled) { downloadBtn.disabled = !enabled; }
function showStatus(message) { if(statusMessage) { if (message) { statusMessage.textContent = message; statusMessage.classList.remove('hidden'); } else { statusMessage.classList.add('hidden'); }}}

// Precisamos de um pequeno CSS para o novo botão de download, adicione isto ao seu style.css
const extraStyles = `
.download-button {
    display: block; width: 100%; background-color: var(--success-color); color: white;
    text-decoration: none; padding: 14px; border-radius: 6px; font-weight: bold; text-align: center;
    transition: background-color 0.2s, transform 0.2s; border: none; font-size: 1rem; cursor: pointer;
    box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08);
}
.download-button:hover { background-color: #27b97a; transform: translateY(-2px); }
.download-button:disabled { background-color: #a0f1ce; cursor: not-allowed; transform: none; }
`;
const styleSheet = document.createElement("style");
styleSheet.innerText = extraStyles;
document.head.appendChild(styleSheet);
