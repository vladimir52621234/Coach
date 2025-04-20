import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_DIR = 'user_data'  # Папка для хранения данных пользователей

MAIN_KEYBOARD = ["📅 Показать график", "✏️ Редактировать график"]
EDIT_KEYBOARD = ["➕ Добавить упражнение", "✏️ Добавить вес", "🗑️ Удалить упражнение", "🔙 Назад"]
BACK_BUTTON = "🔙 Назад"

DAYS_OF_WEEK = [
    "Понедельник", "Вторник", "Среда",
    "Четверг", "Пятница", "Суббота", "Воскресенье"
]
