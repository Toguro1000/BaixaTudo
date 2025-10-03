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
    
    ydl_opts = {'noplaylist': True, 'quiet': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Lógica V3 para filtrar e limpar os formatos
            filtered_formats = {}
            best_audio = None

            for f in info.get('formats', []):
                if not f.get('url'):
                    continue

                # Encontra o melhor áudio separado
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    if not best_audio or (f.get('abr', 0) > best_audio.get('abr', 0)):
                        best_audio = f
                
                # Encontra vídeos com vídeo e áudio juntos
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    height = f.get('height')
                    if height:
                        label = f"Vídeo ({height}p)"
                        # Adiciona apenas se for uma qualidade nova ou melhor para essa resolução
                        if label not in filtered_formats or f.get('filesize', 0) > filtered_formats[label].get('filesize', 0):
                             filtered_formats[label] = {
                                "quality": label,
                                "ext": f.get('ext'),
                                "size_mb": round(f.get('filesize', 0) / (1024*1024), 2) if f.get('filesize') else "N/A",
                                "download_url": f.get('url')
                            }

            # Se não encontrámos vídeos com áudio, pegamos o melhor de tudo
            if not filtered_formats and info.get('url'):
                 filtered_formats['Melhor Qualidade'] = {
                    "quality": "Melhor Qualidade",
                    "ext": info.get('ext', 'mp4'),
                    "size_mb": "N/A",
                    "download_url": info.get('url')
                }

            # Adiciona a opção de apenas áudio, se encontrámos uma
            if best_audio:
                label_audio = f"Apenas Áudio ({best_audio.get('ext')})"
                filtered_formats[label_audio] = {
                    "quality": label_audio,
                    "ext": best_audio.get('ext'),
                    "size_mb": round(best_audio.get('filesize', 0) / (1024*1024), 2) if best_audio.get('filesize') else "N/A",
                    "download_url": best_audio.get('url')
                }

            response_data = {
                "title": info.get('title', 'Título não encontrado'),
                "formats": list(filtered_formats.values()) # Transforma o dicionário de volta em lista
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
    file_ext = request.args.get('ext', 'mp4')
    if not video_url:
        return "URL para download não fornecida.", 400

    try:
        req = requests.get(video_url, stream=True, headers={'Referer': 'https://www.google.com/'})
        
        return Response(req.iter_content(chunk_size=1024*1024),
                        content_type=req.headers.get('content-type', 'application/octet-stream'),
                        headers={"Content-Disposition": f"attachment; filename=video.{file_ext}"})
    except Exception as e:
        logging.error(f"Falha no proxy-download para {video_url}: {e}")
        return "Não foi possível baixar o ficheiro.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
