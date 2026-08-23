import os
import requests
from flask import Flask, request, jsonify, render_template
import logging

# Configurar logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

def call_api(region, uid):
    server_code = region.lower()
    # Usando a API funcional de Free Fire para buscar os dados e likes do jogador
    url = f"https://freefire-api-six.vercel.app/get_player_stats?server={server_code}&uid={uid}&matchmode=RANKED&gamemode=br"
    
    try:
        response = requests.get(url, timeout=20)
        if response.status_code != 200:
            return {"error": "Jogador não encontrado ou erro na API."}
        
        data = response.json()
        
        # Extraindo informações da resposta da API
        account_info = data.get("AccountInfo", {})
        player_name = account_info.get("PlayerName") or data.get("playerName") or "Jogador FF"
        player_likes = account_info.get("PlayerLikes", "N/A")
        
        return {
            "PlayerNickname": player_name,
            "UID": uid,
            "Region": region.upper(),
            "LikesGivenByAPI": "Perfil Carregado",
            "LikesafterCommand": player_likes
        }
    except Exception as e:
        logger.error(f"Erro na requisição: {e}")
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
