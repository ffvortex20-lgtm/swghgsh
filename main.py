import os
import requests
from flask import Flask, request, jsonify, render_template
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

def call_api(region, uid):
    # Substitua abaixo pela URL real da API que você estiver utilizando
    url = f"https://your-free-fire-like-api-domain/like?uid={uid}&server_name={region}"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code != 200:
            return {"error": "Limite máximo atingido ou erro na API."}
        return response.json()
    except:
        return {"error": "Falha na conexão com a API."}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/send-likes', methods=['POST'])
def web_send_likes():
    data = request.json
    uid = data.get('uid')
    region = data.get('region')

    if not uid or not region:
        return jsonify({"success": False, "error": "UID e Região são obrigatórios."}), 400

    response = call_api(region, uid)
    if "error" in response:
        return jsonify({"success": False, "error": response["error"]}), 400

    return jsonify({
        "success": True,
        "player_name": response.get("PlayerNickname", "N/A"),
        "uid": response.get("UID", uid),
        "region": response.get("Region", region),
        "likes_given": response.get("LikesGivenByAPI", "0"),
        "likes_after": response.get("LikesafterCommand", "0")
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
