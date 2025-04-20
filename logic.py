import json
import os
from aiogram.fsm.state import State, StatesGroup
from config import DATA_DIR


### --- Состояния FSM ---
class WorkoutStates(StatesGroup):
    waiting_for_day = State()
    waiting_for_exercise = State()
    waiting_for_weight = State()
    waiting_for_edit_day = State()
    waiting_for_edit_choice = State()


### --- Работа с данными ---
def get_user_file(user_id: int) -> str:
    """Возвращает путь к файлу данных пользователя"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    return os.path.join(DATA_DIR, f'{user_id}.json')


def load_data(user_id: int) -> dict:
    """Загружает данные тренировок пользователя из JSON."""
    file_path = get_user_file(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_data(user_id: int, data: dict) -> None:
    """Сохраняет данные тренировок пользователя в JSON."""
    file_path = get_user_file(user_id)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def format_schedule(data: dict) -> str:
    """Форматирует данные тренировок в читаемый текст."""
    if not data:
        return "График тренировок пуст. Добавьте упражнения через меню редактирования."

    response = "📅 Ваш график тренировок:\n\n"
    for day, exercises in data.items():
        response += f"<b>{day}:</b>\n"
        for i, exercise_data in enumerate(exercises, 1):
            exercise = exercise_data['name']
            weight = exercise_data.get('weight', '')
            if weight:
                response += f"{i}. {exercise} ({weight} кг)\n"
            else:
                response += f"{i}. {exercise}\n"
        response += "\n"
    return response
