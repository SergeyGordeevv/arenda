import os
import requests
from flask import Flask, request
import time
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

# URL твоего бота на Render (ЗАМЕНИ НА СВОЙ!)
WEBHOOK_URL = "https://arenda-4pxf.onrender.com"

# ============================================
# ФУНКЦИИ ПАРСИНГА
# ============================================
def parse_kufar():
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if '/l/minsk/snyat/kvartiru/' in a['href'] and 'page' not in a['href']:
                txt = a.text.strip()
                if len(txt) > 5:
                    link = "https://re.kufar.by" + a['href'] if a['href'].startswith('/') else a['href']
                    offers.append(f"🏠 {txt[:50]}\n🔗 {link}")
                    if len(offers) >= 5:
                        break
    except Exception as e:
        print(f"Kufar ошибка: {e}")
    return offers

def parse_onliner():
    offers = []
    url = "https://r.onliner.by/flats/rent/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if '/flats/rent/' in a['href'] and 'page' not in a['href']:
                txt = a.text.strip()
                if len(txt) > 5:
                    link = "https://r.onliner.by" + a['href'] if a['href'].startswith('/') else a['href']
                    offers.append(f"🏠 {txt[:50]}\n🔗 {link}")
                    if len(offers) >= 5:
                        break
    except Exception as e:
        print(f"Onliner ошибка: {e}")
    return offers

def get_all_offers():
    all_offers = []
    all_offers.extend(parse_kufar())
    all_offers.extend(parse_onliner())
    return all_offers

# ============================================
# ВЕБХУК ДЛЯ TELEGRAM
# ============================================
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        
        if text == '/start':
            send_message(chat_id, "🤖 Бот запущен! Проверяю объявления...")
            offers = get_all_offers()
            if offers:
                for o in offers[:3]:
                    send_message(chat_id, o)
            else:
                send_message(chat_id, "Новых объявлений пока нет")
        elif text == '/stats':
            send_message(chat_id, "📊 Бот работает, проверяет Kufar и Onliner")
        else:
            send_message(chat_id, "Используй /start или /stats")
    return "OK", 200

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Ошибка отправки: {e}")

# ============================================
# НАСТРОЙКА ВЕБХУКА
# ============================================
def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    try:
        r = requests.post(url, json={"url": WEBHOOK_URL})
        print(f"Webhook установлен: {r.json()}")
    except Exception as e:
        print(f"Ошибка установки webhook: {e}")

# ============================================
# ЗАПУСК
# ============================================
@app.route('/')
def index():
    return "🤖 Бот работает! Вебхук: " + WEBHOOK_URL

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ЗАПУСК БОТА (ВЕБХУК)")
    print("=" * 50)
    
    # Устанавливаем вебхук
    set_webhook()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"Сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
