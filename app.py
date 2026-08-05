import os
import threading
import time
from flask import Flask, request
import telebot
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ============================================
# НАСТРОЙКИ
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

CHAT_ID = -5568949748  # ПРОВЕРЬ ЭТОТ ID!
CHECK_INTERVAL = 300

bot = telebot.TeleBot(BOT_TOKEN)
sent_offers = set()
app = Flask(__name__)

# ============================================
# ПАРСИНГ KUFAR
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

# ============================================
# ПАРСИНГ ONLINER
# ============================================
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

# ============================================
# ПАРСИНГ REALT
# ============================================
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

# ============================================
# СБОР ВСЕХ ОБЪЯВЛЕНИЙ
# ============================================
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
# МОНИТОРИНГ НОВЫХ ОБЪЯВЛЕНИЙ
# ============================================
def monitor_offers():
    global sent_offers
    print("🔄 Мониторинг объявлений запущен...")
    while True:
        try:
            current_offers = set(get_all_offers())
            new_offers = current_offers - sent_offers
            if new_offers:
                print(f"🔔 Найдено {len(new_offers)} новых объявлений!")
                for offer in new_offers:
                    bot.send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ!\n\n{offer}")
                    print("  ✅ Отправлено")
                    time.sleep(1)
                sent_offers = current_offers
            else:
                print("Новых объявлений нет.")
        except Exception as e:
            print(f"❌ Ошибка в мониторинге: {e}")
        time.sleep(CHECK_INTERVAL)

# ============================================
# ОБРАБОТЧИК КОМАНД
# ============================================
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "🤖 Бот запущен и работает!\n\n"
                          "📌 Отслеживаю объявления на:\n"
                          "• Kufar.by\n"
                          "• Onliner.by\n"
                          "• Realt.by\n\n"
                          "🔄 Проверка каждые 5 минут\n"
                          "📊 Статистика: /stats")

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    bot.reply_to(message, f"📊 СТАТИСТИКА\n\n"
                          f"• Отслеживается: {len(sent_offers)} объявлений\n"
                          f"• Интервал: {CHECK_INTERVAL} сек\n"
                          f"• Статус: ✅ Активен")

# ============================================
# ВЕБ-ИНТЕРФЕЙС ДЛЯ RENDER (КРИТИЧНО ВАЖНО!)
# ============================================
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
            return "OK", 200
        except Exception as e:
            print(f"Ошибка обработки вебхука: {e}")
            return "ERROR", 500
    return "🤖 Бот для аренды жилья запущен!", 200

@app.route('/health')
def health_check():
    return "OK", 200

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 БОТ АРЕНДА БЕЛАРУСЬ")
    print("=" * 50)
    
    print("🔄 Инициализация...")
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")
    
    # Удаляем вебхук
    bot.remove_webhook()
    print("✅ Вебхук удален")
    
    # Запускаем мониторинг
    threading.Thread(target=monitor_offers, daemon=True).start()
    print("🚀 Мониторинг запущен!")
    
    # Запускаем веб-сервер
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Веб-сервер на порту {port}...")
    app.run(host="0.0.0.0", port=port)
