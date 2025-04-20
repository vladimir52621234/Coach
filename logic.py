import json
import os
from aiogram.fsm.state import State, StatesGroup
from config import DATA_FILE


### --- Состояния FSM ---
class WorkoutStates(StatesGroup):
    waiting_for_day = State()  # Ожидание дня для добавления
    waiting_for_exercise = State()  # Ожидание упражнения
    waiting_for_edit_day = State()  # Ожидание дня для удаления
    waiting_for_edit_choice = State()  # Ожидание номера упражнения для удаления


### --- Работа с данными ---
def load_data() -> dict:
    """Загружает данные тренировок из JSON."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_data(data: dict) -> None:
    """Сохраняет данные тренировок в JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def format_schedule(data: dict) -> str:
    """Форматирует данные тренировок в читаемый текст."""
    if not data:
        return "График тренировок пуст. Добавьте упражнения через меню редактирования."

    response = "📅 Ваш график тренировок:\n\n"
    for day, exercises in data.items():
        response += f"<b>{day}:</b>\n"
        for i, exercise in enumerate(exercises, 1):
            response += f"{i}. {exercise}\n"
        response += "\n"
    return response
