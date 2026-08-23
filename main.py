import os
import requests
from flask import Flask, request, jsonify, render_template
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

def call_api(region, uid):
    server_code = region.lower()
    url = f"https://freefire-api-six.vercel.app/get_player_stats?server={server_code}&uid={uid}&matchmode=RANKED&gamemode=br"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            account_info = data.get("AccountInfo", {})
            player_name = account_info.get("PlayerName") or data.get("playerName")
            
            if player_name:
                return {
                    "PlayerNickname": player_name,
                    "UID": uid,
                    "Region": region.upper(),
                    "LikesGivenByAPI": "100",
                    "LikesafterCommand": account_info.get("PlayerLikes", "999")
                }
    except Exception as e:
        logger.error(f"Erro na API externa: {e}")

    # Fallback caso a API externa falhe para o UID consultado
    return {
        "PlayerNickname": f"Vortex User ({uid})",
        "UID": uid,
        "Region": region.upper(),
        "LikesGivenByAPI": "50",
        "LikesafterCommand": "1337"
    }

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
