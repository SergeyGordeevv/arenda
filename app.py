import os
import threading
from flask import Flask
import telebot
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748
CHECK_INTERVAL = 300

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

bot = telebot.TeleBot(BOT_TOKEN)
sent_offers = set()
app = Flask(__name__)

def parse_kufar():
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            if '/l/minsk/snyat/kvartiru/' in a['href'] and 'page' not in a['href']:
                txt = a.text.strip()
                if len(txt) > 5:
                    link = "https://re.kufar.by" + a['href'] if a['href'].startswith('/') else a['href']
                    offers.append(f"🏠 {txt[:50]}\n🔗 {link}")
                    if len(offers) >= 10:
                        break
    except:
        pass
    return offers

def parse_onliner():
    offers = []
    url = "https://r.onliner.by/flats/rent/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('offer' in x.lower() or 'form' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://r.onliner.by" + a['href'] if a['href'].startswith('/') else a['href']
                offers.append(f"🏠 {txt[:50]}\n🔗 {link}")
                if len(offers) >= 10:
                    break
    except:
        pass
    return offers

def parse_realt():
    offers = []
    url = "https://realt.by/rent/flats/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'offer' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://realt.by" + a['href'] if a['href'].startswith('/') else a['href']
                offers.append(f"🏠 {txt[:50]}\n🔗 {link}")
                if len(offers) >= 10:
                    break
    except:
        pass
    return offers

def get_all_offers():
    res = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг...")
    res += parse_kufar()
    res += parse_onliner()
    res += parse_realt()
    print(f"  Всего: {len(res)}")
    return res

def monitor():
    global sent_offers
    while True:
        try:
            curr = set(get_all_offers())
            new = curr - sent_offers
            if new:
                for o in new:
                    try:
                        bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{o}")
                        time.sleep(1)
                    except:
                        pass
                sent_offers = curr
        except:
            pass
        time.sleep(CHECK_INTERVAL)

@app.route('/')
def index():
    return "Бот работает ✅"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    print("🔄 Запуск...")
    sent_offers = set(get_all_offers())
    threading.Thread(target=monitor, daemon=True).start()
    print("🚀 Бот запущен")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
