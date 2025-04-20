import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = 'workout_data.json'

MAIN_KEYBOARD = ["📅 Показать график", "✏️ Редактировать график"]

EDIT_KEYBOARD = ["➕ Добавить упражнение", "🗑️ Удалить упражнение", "🔙 Назад"]

BACK_BUTTON = "🔙 Назад"
