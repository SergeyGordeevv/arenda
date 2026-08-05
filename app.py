import os
import requests
from flask import Flask, request
import time
from datetime import datetime
from bs4 import BeautifulSoup # Убедимся, что библиотека импортирована

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748

# !!! ВАЖНО: ЗАМЕНИ НА СВОЙ URL ОТ RENDER !!!
WEBHOOK_URL = "https://arenda-4pxf.onrender.com/webhook"

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

# --- ФУНКЦИИ ПАРСИНГА С ФИЛЬТРОМ ПО ЛОГОЙСКУ ---

def parse_kufar():
    """Парсинг Kufar.by с фильтром по Логойску"""
    offers = []
    # Добавляем параметр city[0]=logojsk в URL
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru?city[0]=logojsk"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Ищем элементы с объявлениями (этот селектор может меняться, нужно проверять)
        for item in soup.find_all('div', class_='styles_wrapper__1sPEG'):
            try:
                link_elem = item.find('a', class_='styles_title__1wEp7')
                if not link_elem: continue
                
                title = link_elem.text.strip()
                link = "https://re.kufar.by" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                price_elem = item.find('span', class_='styles_price__1N2aA')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                offers.append(f"🏠 {title}\n💰 {price}\n🔗 {link}")
                if len(offers) >= 5:
                    break
            except Exception as e:
                print(f"Ошибка парсинга объявления Kufar: {e}")
                continue
    except Exception as e:
        print(f"Kufar ошибка: {e}")
    return offers

def parse_onliner():
    """Парсинг Onliner.by с фильтром по Логойску"""
    offers = []
    # Добавляем параметр region=logojsk в URL
    url = "https://r.onliner.by/flats/rent/?region=logojsk"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for item in soup.find_all('div', class_='form__block'):
            try:
                link_elem = item.find('a', class_='offer__link')
                if not link_elem: continue
                
                title_elem = item.find('div', class_='offer__title')
                title = title_elem.text.strip() if title_elem else "Без названия"
                link = "https://r.onliner.by" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                price_elem = item.find('div', class_='offer__price')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                offers.append(f"🏠 {title}\n💰 {price}\n🔗 {link}")
                if len(offers) >= 5:
                    break
            except Exception as e:
                print(f"Ошибка парсинга объявления Onliner: {e}")
                continue
    except Exception as e:
        print(f"Onliner ошибка: {e}")
    return offers

def parse_realt():
    """Парсинг Realt.by с фильтром по Логойску"""
    offers = []
    # Добавляем параметр location=logojsk в URL
    url = "https://realt.by/rent/flats/?location=logojsk"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Ищем элементы с объявлениями (этот селектор может меняться)
        for item in soup.find_all('div', class_='search-item'):
            try:
                link_elem = item.find('a', class_='search-item-title')
                if not link_elem: continue
                
                title = link_elem.text.strip()
                link = "https://realt.by" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                price_elem = item.find('span', class_='price')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                offers.append(f"🏠 {title}\n💰 {price}\n🔗 {link}")
                if len(offers) >= 5:
                    break
            except Exception as e:
                print(f"Ошибка парсинга объявления Realt: {e}")
                continue
    except Exception as e:
        print(f"Realt ошибка: {e}")
    return offers

def parse_domovita():
    """Парсинг Domovita.by с фильтром по Логойску (пример)"""
    offers = []
    # URL для поиска по Логойску на Domovita
    url = "https://domovita.by/minskaja/logojsk/arenda/kvartiry/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Поиск элементов (селекторы нужно проверить на сайте)
        for item in soup.find_all('div', class_='object-item'):
            try:
                link_elem = item.find('a', class_='link-object')
                if not link_elem: continue
                
                title = link_elem.text.strip()
                link = "https://domovita.by" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                price_elem = item.find('span', class_='price')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                
                offers.append(f"🏠 {title}\n💰 {price}\n🔗 {link}")
                if len(offers) >= 5:
                    break
            except Exception as e:
                print(f"Ошибка парсинга объявления Domovita: {e}")
                continue
    except Exception as e:
        print(f"Domovita ошибка: {e}")
    return offers

def get_all_offers():
    all_offers = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг всех сайтов...")
    
    all_offers.extend(parse_kufar())
    all_offers.extend(parse_onliner())
    all_offers.extend(parse_realt())
    all_offers.extend(parse_domovita()) # Добавляем новый сайт
    
    print(f"  Всего найдено в Логойске: {len(all_offers)}")
    return all_offers

# --- ВЕБХУК И ОСТАЛЬНОЙ КОД (БЕЗ ИЗМЕНЕНИЙ) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    # ... (весь этот блок остается без изменений) ...
    data = request.get_json()
    if data and 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        
        if text == '/start':
            send_message(chat_id, "🤖 Бот запущен! Ищу объявления только в Логойске...")
            offers = get_all_offers()
            if offers:
                for o in offers[:3]:
                    send_message(chat_id, o)
                if len(offers) > 3:
                    send_message(chat_id, f"... и еще {len(offers) - 3} объявлений. Используй /all для просмотра всех.")
            else:
                send_message(chat_id, "😔 В Логойске пока нет новых объявлений.")
        elif text == '/stats':
            send_message(chat_id, "📊 Бот ищет квартиры в Логойске на Kufar, Onliner, Realt и Domovita.")
        else:
            send_message(chat_id, "Используй /start для поиска или /stats для информации.")
    return "OK", 200

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    try:
        r = requests.post(url, json={"url": WEBHOOK_URL})
        print(f"Webhook установлен: {r.json()}")
    except Exception as e:
        print(f"Ошибка установки webhook: {e}")

@app.route('/')
def index():
    return "🤖 Бот работает! Вебхук: " + WEBHOOK_URL

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ЗАПУСК БОТА (ЛОГОЙСК)")
    print("=" * 50)
    
    set_webhook()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"Сервер запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
