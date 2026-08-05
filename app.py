import os
import threading
import time
from flask import Flask, request
import telebot
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

CHAT_ID = -5568949748
CHECK_INTERVAL = 300

bot = telebot.TeleBot(BOT_TOKEN)
sent_offers = set()
app = Flask(__name__)

# ============================================
# ПАРСИНГ
# ============================================
def parse_kufar():
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru?m=1"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for item in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'card' in x.lower())):
            try:
                title_elem = item.find('a', class_=lambda x: x and ('title' in x.lower() or 'link' in x.lower()))
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                link = title_elem.get('href')
                if link and link.startswith('/'):
                    link = "https://re.kufar.by" + link
                price_elem = item.find('span', class_=lambda x: x and 'price' in x.lower())
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                offer_text = f"🏠 {title[:50]}\n💰 {price}\n🔗 {link}"
                offers.append(offer_text)
                if len(offers) >= 10:
                    break
            except:
                continue
    except Exception as e:
        print(f"Ошибка Kufar: {e}")
    return offers

def parse_onliner():
    offers = []
    url = "https://r.onliner.by/flats/rent/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('offer' in x.lower() or 'form' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://r.onliner.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"Ошибка Onliner: {e}")
    return offers

def parse_realt():
    offers = []
    url = "https://realt.by/rent/flats/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for div in soup.find_all('div', class_=lambda x: x and ('item' in x.lower() or 'offer' in x.lower())):
            a = div.find('a')
            if a and a.get('href'):
                txt = a.text.strip()
                link = "https://realt.by" + a['href'] if a['href'].startswith('/') else a['href']
                if txt:
                    offer_text = f"🏠 {txt[:50]}\n🔗 {link}"
                    offers.append(offer_text)
                if len(offers) >= 10:
                    break
    except Exception as e:
        print(f"Ошибка Realt: {e}")
    return offers

def get_all_offers():
    res = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг...")
    kufar = parse_kufar()
    res.extend(kufar)
    print(f"  Kufar: {len(kufar)}")
    onliner = parse_onliner()
    res.extend(onliner)
    print(f"  Onliner: {len(onliner)}")
    realt = parse_realt()
    res.extend(realt)
    print(f"  Realt: {len(realt)}")
    print(f"  Всего: {len(res)}")
    return res

# ============================================
# МОНИТОРИНГ
# ============================================
def monitor_offers():
    global sent_offers
    while True:
        try:
            current = set(get_all_offers())
            new = current - sent_offers
            if new:
                print(f"🔔 НОВЫХ: {len(new)}")
                for offer in new:
                    try:
                        bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                        print("  ✅ Отправлено")
                        time.sleep(1)
                    except:
                        pass
                sent_offers = current
            else:
                print("Новых нет")
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(CHECK_INTERVAL)

# ============================================
# КОМАНДЫ БОТА
# ============================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "🤖 Бот запущен и работает!")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    bot.reply_to(message, f"📊 Объявлений: {len(sent_offers)}")

# ============================================
# ВЕБХУК (ПРИНИМАЕТ СООБЩЕНИЯ ОТ TELEGRAM)
# ============================================
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
            return "OK", 200
        except Exception as e:
            print(f"Ошибка: {e}")
            return "ERROR", 500
    return "Бот работает", 200

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("🔄 Запуск...")
    sent_offers = set(get_all_offers())
    bot.remove_webhook()
    threading.Thread(target=monitor_offers, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
