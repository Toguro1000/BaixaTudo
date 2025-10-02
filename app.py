from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'public')
app = Flask(__name__, static_folder=PUBLIC_DIR)
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(PUBLIC_DIR, path)

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "Nenhum link (URL) foi fornecido."}), 400
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            response_data = {
                "title": info.get('title', 'Título não encontrado'),
                "url": info.get('url'),
                "format": info.get('format_note', 'Qualidade desconhecida')
            }
            return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": "Não foi possível processar o link. Verifique se é válido."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
