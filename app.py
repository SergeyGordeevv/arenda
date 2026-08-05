import os
import threading
from flask import Flask
import telebot
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# ============================================
# НАСТРОЙКИ (Берутся из переменных окружения)
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -5568949748
CHECK_INTERVAL = 300

if not BOT_TOKEN:
    raise ValueError("Переменная TELEGRAM_BOT_TOKEN не установлена!")

bot = telebot.TeleBot(BOT_TOKEN)
sent_offers = set()
# ============================================

# --- (СЮДА ВСТАВЬТЕ ВАШИ ФУНКЦИИ ПАРСИНГА: parse_kufar, parse_onliner, parse_realt, get_all_offers) ---
# ... (скопируйте их из вашего файла main.py) ...

# ============================================
# ФУНКЦИЯ МОНИТОРИНГА (запускается в фоне)
# ============================================
def send_new_offers():
    global sent_offers
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Начинаю парсинг...")
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
# ЗАПУСК ПРИ ЗАПУСКЕ ПРИЛОЖЕНИЯ
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 БОТ АРЕНДА БЕЛАРУСЬ (НАЧАЛО ЗАГРУЗКИ)")
    print("=" * 50)

    # Инициализация: запоминаем текущие объявления
    print("🔄 Инициализация...")
    sent_offers = set(get_all_offers())
    print(f"✅ Отслеживается {len(sent_offers)} объявлений")

    # Запускаем мониторинг в отдельном потоке
    monitor_thread = threading.Thread(target=send_new_offers, daemon=True)
    monitor_thread.start()

    # Запускаем polling в отдельном потоке
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    print("✅ Бот и мониторинг запущены в фоне.")

    # Запускаем Flask-сервер для Render
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Запуск веб-сервера на порту {port}...")
    app.run(host="0.0.0.0", port=port)