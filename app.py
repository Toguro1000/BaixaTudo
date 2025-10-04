from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import yt_dlp
import os
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')
app = Flask(__name__, static_folder=PUBLIC_DIR)
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(PUBLIC_DIR, path)

# Endpoint V4 - Simplificado para buscar apenas o melhor vídeo
@app.route('/api/v1/fetch-info', methods=['POST'])
def fetch_info():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "Nenhum link (URL) foi fornecido."}), 400

    logging.info(f"Recebida requisição para a URL: {url}")
    
    # Pede ao yt-dlp para encontrar o melhor formato mp4 (vídeo+áudio) ou o melhor de tudo
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'format': 'best[ext=mp4]/best' 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Prepara uma resposta simples com apenas o necessário
            response_data = {
                "title": info.get('title', 'Título não encontrado'),
                "download_url": info.get('url'),
                "ext": info.get('ext', 'mp4')
            }
            return jsonify(response_data)

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp DownloadError para {url}: {e}")
        return jsonify({"error": "Plataforma não suportada ou link inválido."}), 400
    except Exception as e:
        logging.error(f"Erro genérico para {url}: {e}")
        return jsonify({"error": "Ocorreu um erro inesperado no servidor. Tente novamente."}), 500

# Dentro do seu app.py, substitua apenas esta função:
@app.route('/api/v1/proxy-download')
def proxy_download():
    video_url = request.args.get('url')
    file_ext = request.args.get('ext', 'mp4')
    if not video_url:
        return "URL para download não fornecida.", 400

    try:
        req = requests.get(video_url, stream=True, headers={'Referer': 'https://www.google.com/'})
        
        # Pega o tamanho do ficheiro para a barra de progresso
        total_length = req.headers.get('content-length')
        
        headers = {
            "Content-Disposition": f"attachment; filename=video.{file_ext}",
            "Content-Type": req.headers.get('content-type', 'application/octet-stream'),
        }
        
        # Adiciona o tamanho do ficheiro ao cabeçalho da resposta
        if total_length:
            headers["Content-Length"] = total_length

        return Response(req.iter_content(chunk_size=1024*1024), headers=headers)
    except Exception as e:
        logging.error(f"Falha no proxy-download para {video_url}: {e}")
        return "Não foi possível baixar o ficheiro.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
