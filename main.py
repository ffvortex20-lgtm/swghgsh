import os
import telebot
import requests
import time
import threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, jsonify, render_template
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === CONFIGURAÇÕES ===
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN não encontrado nas variáveis de ambiente.")
    sys.exit(1)

REQUIRED_CHANNELS = ["@su_canal_aqui"] # Ajuste para seus canais se necessário
GROUP_JOIN_LINK = "https://t.me/seu_grupo_aqui"
OWNER_ID = 000000000  # Insira seu ID do Telegram (inteiro)
OWNER_USERNAME = "@seu_usuario"

bot = telebot.TeleBot(BOT_TOKEN)
like_tracker = {}

# Configurando o Flask para rodar a interface web
app = Flask(__name__, template_folder='templates')

def reset_limits():
    while True:
        try:
            now_utc = datetime.utcnow()
            next_reset = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            sleep_seconds = (next_reset - now_utc).total_seconds()
            time.sleep(sleep_seconds)
            like_tracker.clear()
            logger.info("✅ Limites diários resetados.")
        except Exception as e:
            logger.error(f"Erro no reset: {e}")

threading.Thread(target=reset_limits, daemon=True).start()

def is_user_in_channel(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except:
        return True # Se falhar a verificação por grupo privado, deixa passar

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

def get_user_limit(user_id):
    if user_id == OWNER_ID:
        return 999999999
    return 1

# === ROTAS DO SITE (WEB) ===
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

# === ROTAS DO TELEGRAM ===
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "✅ **Vortex Likes Bot** online! Use `/like <região> <uid>` para enviar curtidas.", parse_mode="Markdown")

@bot.message_handler(commands=['like'])
def handle_like(message):
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❌ Use o formato correto: `/like BR 123456789`", parse_mode="Markdown")
        return
    
    region, uid = args[1], args[2]
    processing = bot.reply_to(message, "⏳ Processando curtidas...")
    
    response = call_api(region, uid)
    if "error" in response:
        bot.edit_message_text(f"⚠️ Erro: {response['error']}", message.chat.id, processing.message_id)
        return

    text = f"""✅ *Sucesso!*
👤 *Nome:* `{response.get('PlayerNickname', 'N/A')}`
🆔 *UID:* `{response.get('UID', uid)}`
📈 *Adicionados:* `{response.get('LikesGivenByAPI', '0')}`
🗿 *Total Agora:* `{response.get('LikesafterCommand', '0')}`
👑 *Vortex Hub*"""
    bot.edit_message_text(text, message.chat.id, processing.message_id, parse_mode="Markdown")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return '', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
