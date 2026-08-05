import os
import requests
from flask import Flask, request
import time
import threading
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748
WEBHOOK_URL = "https://arenda-4pxf.onrender.com/webhook"

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан!")

sent_offers = set()

# ============================================
# ФУНКЦИИ ДЛЯ КНОПОК (КЛАВИАТУРА)
# ============================================

def get_main_keyboard():
    """Главное меню с кнопками"""
    keyboard = {
        "keyboard": [
            [{"text": "🔍 Найти сейчас"}, {"text": "📊 Статистика"}],
            [{"text": "ℹ️ О боте"}, {"text": "🔄 Обновить"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    return keyboard

def get_help_text():
    return """🤖 *Бот для аренды жилья в Логойске*

🏠 *Отслеживает сайты:*
• Kufar.by
• Onliner.by  
• Realt.by
• Domovita.by

📍 *Город:* Логойск
⏱ *Проверка:* Каждые 5 минут

📌 *Как использовать:*
Нажми на кнопку *🔍 Найти сейчас* — бот покажет свежие объявления
Нажми *📊 Статистика* — узнаешь сколько объявлений в базе
Нажми *ℹ️ О боте* — увидишь эту информацию

🔔 *Новые объявления* приходят автоматически в группу!

📱 *Разработчик:* @Sergey_Gordeev0
🌐 *Сайт:* arenda-4pxf.onrender.com"""

# ============================================
# ФУНКЦИИ ПАРСИНГА (Логойск)
# ============================================

def parse_kufar():
    offers = []
    url = "https://re.kufar.by/l/minsk/snyat/kvartiru?city[0]=logojsk"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for item in soup.find_all('div', class_='styles_wrapper__1sPEG'):
            try:
                link_elem = item.find('a', class_='styles_title__1wEp7')
                if not link_elem: continue
                title = link_elem.text.strip()
                link = "https://re.kufar.by" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                price_elem = item.find('span', class_='styles_price__1N2aA')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                offers.append(f"🏠 {title}\n💰 {price}\n🔗 {link}")
                if len(offers) >= 10: break
            except: continue
    except Exception as e:
        print(f"Kufar ошибка: {e}")
    return offers

def parse_onliner():
    offers = []
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
                if len(offers) >= 10: break
            except: continue
    except Exception as e:
        print(f"Onliner ошибка: {e}")
    return offers

def parse_realt():
    offers = []
    url = "https://realt.by/rent/flats/?location=logojsk"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for item in soup.find_all('div', class_='search-item'):
            try:
                link_elem = item.find('a', class_='search-item-title')
                if not link_elem: continue
                title = link_elem.text.strip()
                link = "https://realt.by" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                price_elem = item.find('span', class_='price')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                offers.append(f"🏠 {title}\n💰 {price}\n🔗 {link}")
                if len(offers) >= 10: break
            except: continue
    except Exception as e:
        print(f"Realt ошибка: {e}")
    return offers

def parse_domovita():
    offers = []
    url = "https://domovita.by/minskaja/logojsk/arenda/kvartiry/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for item in soup.find_all('div', class_='object-item'):
            try:
                link_elem = item.find('a', class_='link-object')
                if not link_elem: continue
                title = link_elem.text.strip()
                link = "https://domovita.by" + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                price_elem = item.find('span', class_='price')
                price = price_elem.text.strip() if price_elem else "Цена не указана"
                offers.append(f"🏠 {title}\n💰 {price}\n🔗 {link}")
                if len(offers) >= 10: break
            except: continue
    except Exception as e:
        print(f"Domovita ошибка: {e}")
    return offers

def get_all_offers():
    all_offers = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Парсинг Логойск...")
    all_offers.extend(parse_kufar())
    all_offers.extend(parse_onliner())
    all_offers.extend(parse_realt())
    all_offers.extend(parse_domovita())
    print(f"  Всего: {len(all_offers)}")
    return all_offers

# ============================================
# ФОНОВЫЙ МОНИТОРИНГ (АВТО-УВЕДОМЛЕНИЯ)
# ============================================

def send_new_offers():
    global sent_offers
    while True:
        try:
            current = set(get_all_offers())
            new = current - sent_offers
            
            if new:
                print(f"🔔 НОВЫХ ОБЪЯВЛЕНИЙ: {len(new)}")
                for offer in new:
                    try:
                        send_message(CHAT_ID, f"🔔 НОВОЕ ОБЪЯВЛЕНИЕ В ЛОГОЙСКЕ!\n\n{offer}")
                        print("  ✅ Отправлено")
                        time.sleep(2)
                    except Exception as e:
                        print(f"  ❌ Ошибка отправки: {e}")
                sent_offers = current
            else:
                print("Новых объявлений нет")
        except Exception as e:
            print(f"Ошибка в мониторинге: {e}")
        
        time.sleep(300)

# ============================================
# ОТПРАВКА СООБЩЕНИЙ С КНОПКАМИ
# ============================================

def send_message_with_keyboard(chat_id, text, keyboard=None):
    """Отправляет сообщение с клавиатурой"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard or get_main_keyboard()
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def send_message(chat_id, text):
    """Отправляет обычное сообщение"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print(f"Ошибка отправки: {e}")

# ============================================
# ВЕБХУК
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        
        # Обработка команд и кнопок
        if text in ['/start', '🔍 Найти сейчас']:
            send_message_with_keyboard(chat_id, "🔍 *Ищу свежие объявления в Логойске...*\n\nПодожди пару секунд ⏳", get_main_keyboard())
            offers = get_all_offers()
            if offers:
                for i, offer in enumerate(offers[:5]):
                    send_message(chat_id, offer)
                    time.sleep(0.5)
                if len(offers) > 5:
                    send_message(chat_id, f"📌 *Всего найдено: {len(offers)} объявлений*\nНажми *🔄 Обновить* чтобы посмотреть ещё.")
            else:
                send_message_with_keyboard(chat_id, "😔 *В Логойске пока нет новых объявлений.*\n\nПопробуй позже или нажми *🔄 Обновить*", get_main_keyboard())
                
        elif text in ['/stats', '📊 Статистика']:
            stats_text = f"📊 *Статистика бота*\n\n"
            stats_text += f"🏠 *Отслеживается:* {len(sent_offers)} объявлений\n"
            stats_text += f"📍 *Город:* Логойск\n"
            stats_text += f"🌐 *Сайты:* Kufar, Onliner, Realt, Domovita\n"
            stats_text += f"⏱ *Проверка:* каждые 5 минут\n"
            stats_text += f"🔄 *Обновлено:* {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            send_message_with_keyboard(chat_id, stats_text, get_main_keyboard())
            
        elif text in ['/help', 'ℹ️ О боте']:
            send_message_with_keyboard(chat_id, get_help_text(), get_main_keyboard())
            
        elif text in ['🔄 Обновить']:
            send_message_with_keyboard(chat_id, "🔄 *Обновляю данные...*", get_main_keyboard())
            offers = get_all_offers()
            if offers:
                for i, offer in enumerate(offers[:5]):
                    send_message(chat_id, offer)
                    time.sleep(0.5)
                if len(offers) > 5:
                    send_message(chat_id, f"📌 *Показано 5 из {len(offers)} объявлений*")
            else:
                send_message_with_keyboard(chat_id, "😔 *Новых объявлений нет*", get_main_keyboard())
        else:
            send_message_with_keyboard(chat_id, "🤖 *Используй кнопки меню:*\n\n🔍 Найти сейчас — свежие объявления\n📊 Статистика — информация\nℹ️ О боте — справка", get_main_keyboard())
            
    return "OK", 200

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    try:
        r = requests.post(url, json={"url": WEBHOOK_URL})
        print(f"Webhook установлен: {r.json()}")
    except Exception as e:
        print(f"Ошибка установки webhook: {e}")

@app.route('/')
def index():
    return "🤖 Бот для аренды в Логойске работает!"

@app.route('/health')
def health():
    return "OK", 200

# ============================================
# ЗАПУСК
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 БОТ АРЕНДА ЛОГОЙСК (С КНОПКАМИ)")
    print("=" * 50)
    
    print("🔄 Инициализация...")
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")
    
    monitor_thread = threading.Thread(target=send_new_offers, daemon=True)
    monitor_thread.start()
    print("✅ Авто-уведомления запущены")
    
    set_webhook()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Сервер запущен на порту {port}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port)
