import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, MAIN_KEYBOARD, EDIT_KEYBOARD, BACK_BUTTON
from logic import WorkoutStates, load_data, save_data, format_schedule

### --- Инициализация бота ---
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


### --- Клавиатуры ---
def get_main_kb():
    """Клавиатура главного меню."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn)] for btn in MAIN_KEYBOARD],
        resize_keyboard=True
    )


def get_edit_kb():
    """Клавиатура меню редактирования."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn)] for btn in EDIT_KEYBOARD],
        resize_keyboard=True
    )


def get_days_kb():
    """Клавиатура с днями недели."""
    data = load_data()
    buttons = [KeyboardButton(text=day) for day in data.keys()]
    buttons.append(KeyboardButton(text=BACK_BUTTON))
    return ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)


### --- Обработчики команд ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    await message.answer(
        "Привет! Это бот для планирования тренировок. Выбери действие:",
        reply_markup=get_main_kb()
    )


### --- Показать график ---
@dp.message(F.text == "📅 Показать график")
async def show_schedule(message: types.Message):
    """Показывает текущий график тренировок."""
    data = load_data()
    await message.answer(format_schedule(data), parse_mode="HTML")


### --- Редактировать график ---
@dp.message(F.text == "✏️ Редактировать график")
async def edit_schedule_menu(message: types.Message):
    """Меню редактирования графика."""
    await message.answer("Выберите действие:", reply_markup=get_edit_kb())


### --- Назад в главное меню ---
@dp.message(F.text == BACK_BUTTON)
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Возвращает в главное меню."""
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_kb())


### --- Добавление упражнения ---
@dp.message(F.text == "➕ Добавить упражнение")
async def add_exercise_start(message: types.Message, state: FSMContext):
    """Начало добавления упражнения."""
    await state.set_state(WorkoutStates.waiting_for_day)
    await message.answer("Введите день недели:", reply_markup=types.ReplyKeyboardRemove())


@dp.message(WorkoutStates.waiting_for_day)
async def add_exercise_day(message: types.Message, state: FSMContext):
    """Получает день и запрашивает упражнение."""
    await state.update_data(day=message.text)
    await state.set_state(WorkoutStates.waiting_for_exercise)
    await message.answer("Теперь введите упражнение:")


@dp.message(WorkoutStates.waiting_for_exercise)
async def add_exercise_finish(message: types.Message, state: FSMContext):
    """Сохраняет упражнение и завершает FSM."""
    data = await state.get_data()
    day = data["day"]
    exercise = message.text

    workout_data = load_data()
    if day not in workout_data:
        workout_data[day] = []
    workout_data[day].append(exercise)
    save_data(workout_data)

    await state.clear()
    await message.answer(f"✅ Упражнение добавлено в {day}!", reply_markup=get_main_kb())


### --- Удаление упражнения ---
@dp.message(F.text == "🗑️ Удалить упражнение")
async def remove_exercise_start(message: types.Message, state: FSMContext):
    """Начало удаления упражнения."""
    data = load_data()
    if not data:
        await message.answer("График пуст. Нечего удалять.")
        return

    await state.set_state(WorkoutStates.waiting_for_edit_day)
    await message.answer("Выберите день:", reply_markup=get_days_kb())


@dp.message(WorkoutStates.waiting_for_edit_day)
async def remove_exercise_day(message: types.Message, state: FSMContext):
    """Получает день и предлагает выбрать упражнение."""
    if message.text == BACK_BUTTON:
        await state.clear()
        return await edit_schedule_menu(message)

    workout_data = load_data()
    if message.text not in workout_data:
        await message.answer("Такого дня нет. Попробуйте снова.")
        return

    await state.update_data(day=message.text)
    exercises = workout_data[message.text]

    if not exercises:
        await message.answer("В этом дне нет упражнений.")
        await state.clear()
        return

    buttons = [KeyboardButton(text=str(i)) for i in range(1, len(exercises) + 1)]
    buttons.append(KeyboardButton(text=BACK_BUTTON))

    kb = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)

    response = f"Упражнения в {message.text}:\n"
    for i, ex in enumerate(exercises, 1):
        response += f"{i}. {ex}\n"

    await state.set_state(WorkoutStates.waiting_for_edit_choice)
    await message.answer(response + "\nВведите номер для удаления:", reply_markup=kb)


@dp.message(WorkoutStates.waiting_for_edit_choice)
async def remove_exercise_finish(message: types.Message, state: FSMContext):
    """Удаляет выбранное упражнение."""
    if message.text == BACK_BUTTON:
        await state.clear()
        return await edit_schedule_menu(message)

    try:
        num = int(message.text)
    except ValueError:
        await message.answer("Введите номер упражнения!")
        return

    data = await state.get_data()
    day = data["day"]

    workout_data = load_data()
    exercises = workout_data[day]

    if num < 1 or num > len(exercises):
        await message.answer("Неверный номер!")
        return

    removed_ex = exercises.pop(num - 1)
    if not exercises:
        del workout_data[day]

    save_data(workout_data)
    await state.clear()
    await message.answer(f"❌ Удалено: {removed_ex}", reply_markup=get_main_kb())


### --- Запуск бота ---
if __name__ == "__main__":
    dp.run_polling(bot)
