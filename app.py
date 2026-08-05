import os
import threading
from flask import Flask
import telebot
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# ============================================
# НАСТРОЙКИ
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748
CHECK_INTERVAL = 300

if not BOT_TOKEN:
    raise ValueError("Переменная TELEGRAM_BOT_TOKEN не установлена!")

bot = telebot.TeleBot(BOT_TOKEN)
sent_offers = set()
# ============================================

# ============================================
# ПАРСИНГ KUFAR
# ============================================
def parse_kufar():
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='styles_wrapper__1sPEG')
        
        for item in items[:10]:
            try:
                title_elem = item.find('a', class_='styles_title__1wEp7')
                title = title_elem.text.strip() if title_elem else "Без названия"
                
                price_elem = item.find('span', class_='styles_price__1N2aA')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                link = "https://re.kufar.by" + title_elem.get('href', '') if title_elem else ""
                
                offer_text = f"🏠 {title}\n💰 {price}\n🔗 {link}"
                offers.append(offer_text)
            except:
                continue
    except:
        pass
    
    return offers

# ============================================
# ПАРСИНГ ONLINER
# ============================================
def parse_onliner():
    offers = []
    url = "https://r.onliner.by/flats/rent/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='form__block')
        
        for item in items[:10]:
            try:
                title_elem = item.find('div', class_='offer__title')
                title = title_elem.text.strip() if title_elem else "Без названия"
                
                price_elem = item.find('div', class_='offer__price')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                link_elem = item.find('a', class_='offer__link')
                link = "https://r.onliner.by" + link_elem.get('href', '') if link_elem else ""
                
                offer_text = f"🏠 {title}\n💰 {price}\n🔗 {link}"
                offers.append(offer_text)
            except:
                continue
    except:
        pass
    
    return offers

# ============================================
# ПАРСИНГ REALT
# ============================================
def parse_realt():
    offers = []
    url = "https://realt.by/rent/flats/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='search-item')
        
        for item in items[:10]:
            try:
                title_elem = item.find('div', class_='search-item-title')
                title = title_elem.text.strip() if title_elem else "Без названия"
                
                price_elem = item.find('div', class_='price')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                link_elem = item.find('a')
                link = "https://realt.by" + link_elem.get('href', '') if link_elem else ""
                
                offer_text = f"🏠 {title}\n💰 {price}\n🔗 {link}"
                offers.append(offer_text)
            except:
                continue
    except:
        pass
    
    return offers

# ============================================
# СБОР ВСЕХ ОБЪЯВЛЕНИЙ (ЭТА ФУНКЦИЯ БЫЛА ПРОПУЩЕНА!)
# ============================================
def get_all_offers():
    all_offers = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Начинаю парсинг...")
    
    kufar = parse_kufar()
    all_offers.extend(kufar)
    print(f"  Kufar: {len(kufar)}")
    
    onliner = parse_onliner()
    all_offers.extend(onliner)
    print(f"  Onliner: {len(onliner)}")
    
    realt = parse_realt()
    all_offers.extend(realt)
    print(f"  Realt: {len(realt)}")
    
    print(f"  Всего: {len(all_offers)}")
    return all_offers

# ============================================
# ФУНКЦИЯ МОНИТОРИНГА
# ============================================
def send_new_offers():
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
                    except Exception as e:
                        print(f"  ❌ Ошибка отправки: {e}")
                sent_offers = current
            else:
                print("Новых нет")
        except Exception as e:
            print(f"Ошибка: {e}")

        print(f"⏳ Следующая проверка через {CHECK_INTERVAL} сек...")
        print("-" * 40)
        time.sleep(CHECK_INTERVAL)

# ============================================
# ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ
# ============================================
def start_bot_polling():
    print("🚀 Бот запущен!")
    bot.infinity_polling()

# ============================================
# FLASK-ПРИЛОЖЕНИЕ ДЛЯ RENDER
# ============================================
app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Бот для аренды жилья запущен!"

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 БОТ АРЕНДА БЕЛАРУСЬ (НАЧАЛО ЗАГРУЗКИ)")
    print("=" * 50)

    print("🔄 Инициализация...")
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")

    monitor_thread = threading.Thread(target=send_new_offers, daemon=True)
    monitor_thread.start()

    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    print("✅ Бот и мониторинг запущены в фоне.")

    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Запуск веб-сервера на порту {port}...")
    app.run(host="0.0.0.0", port=port)
