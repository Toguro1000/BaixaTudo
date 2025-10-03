from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import yt_dlp
import os
import logging
import requests

# Configuração de Logging para o Render
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

@app.route('/api/v1/fetch-info', methods=['POST'])
def fetch_info():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "Nenhum link (URL) foi fornecido."}), 400

    logging.info(f"Recebida requisição para a URL: {url}")
    
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Pega os melhores formatos separados para MP4
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            for f in info.get('formats', []):
                # Filtra para ter apenas formatos com URL de download e algum detalhe de qualidade
                if f.get('url') and (f.get('format_note') or f.get('resolution')):
                    formats.append({
                        "id": f.get('format_id'),
                        "quality": f.get('format_note', f'{f.get("height", "...")}p'),
                        "ext": f.get('ext'),
                        "size_mb": round(f.get('filesize', 0) / (1024*1024), 2) if f.get('filesize') else "N/A",
                        "download_url": f.get('url')
                    })

            # Adiciona o formato de áudio se disponível
            if info.get('acodec', 'none') != 'none':
                 formats.append({
                    "id": "audio_only",
                    "quality": f"Áudio ({info.get('acodec', '')})",
                    "ext": info.get('audio_ext', 'm4a'),
                    "size_mb": "N/A",
                    "download_url": info.get('url') # URL principal pode servir para áudio
                })

            if not formats:
                 # Se nenhum formato foi encontrado, usa o URL principal
                formats.append({
                    "id": "best",
                    "quality": "Melhor Qualidade",
                    "ext": info.get('ext', 'mp4'),
                    "size_mb": "N/A",
                    "download_url": info.get('url')
                })

            response_data = {
                "title": info.get('title', 'Título não encontrado'),
                "formats": formats
            }
            return jsonify(response_data)

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp DownloadError para {url}: {e}")
        return jsonify({"error": "Plataforma não suportada ou link inválido."}), 400
    except Exception as e:
        logging.error(f"Erro genérico para {url}: {e}")
        return jsonify({"error": "Ocorreu um erro inesperado no servidor. Tente novamente."}), 500

@app.route('/api/v1/proxy-download')
def proxy_download():
    video_url = request.args.get('url')
    if not video_url:
        return "URL para download não fornecida.", 400

    try:
        # Usamos stream=True para não carregar o vídeo inteiro na memória do servidor
        req = requests.get(video_url, stream=True, headers={'Referer': 'https://www.google.com/'})
        
        # Passamos o conteúdo e os cabeçalhos para o utilizador
        return Response(req.iter_content(chunk_size=1024*1024),
                        content_type=req.headers['content-type'],
                        headers={"Content-Disposition": "attachment; filename=video.mp4"})
    except Exception as e:
        logging.error(f"Falha no proxy-download para {video_url}: {e}")
        return "Não foi possível baixar o ficheiro.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
