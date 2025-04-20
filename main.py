import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN, MAIN_KEYBOARD, EDIT_KEYBOARD, BACK_BUTTON, DAYS_OF_WEEK
from logic import WorkoutStates, load_data, save_data, format_schedule

### --- Инициализация бота ---
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


### --- Клавиатуры ---
def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn)] for btn in MAIN_KEYBOARD],
        resize_keyboard=True
    )


def get_edit_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn)] for btn in EDIT_KEYBOARD],
        resize_keyboard=True
    )


def get_days_kb():
    buttons = [KeyboardButton(text=day) for day in DAYS_OF_WEEK]
    buttons.append(KeyboardButton(text=BACK_BUTTON))
    return ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)


### --- Обработчики команд ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Это бот для планирования тренировок. Выбери действие:",
        reply_markup=get_main_kb()
    )


@dp.message(F.text == "📅 Показать график")
async def show_schedule(message: types.Message):
    data = load_data(message.from_user.id)
    await message.answer(format_schedule(data), parse_mode="HTML")


@dp.message(F.text == "✏️ Редактировать график")
async def edit_schedule_menu(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=get_edit_kb())


@dp.message(F.text == BACK_BUTTON)
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_kb())


### --- Добавление упражнения ---
@dp.message(F.text == "➕ Добавить упражнение")
async def add_exercise_start(message: types.Message, state: FSMContext):
    await state.set_state(WorkoutStates.waiting_for_day)
    await message.answer("Выберите день:", reply_markup=get_days_kb())


@dp.message(WorkoutStates.waiting_for_day)
async def add_exercise_day(message: types.Message, state: FSMContext):
    if message.text not in DAYS_OF_WEEK:
        await message.answer("❌ Выберите день из списка!")
        return

    await state.update_data(day=message.text)
    await state.set_state(WorkoutStates.waiting_for_exercise)
    await message.answer("Введите упражнение:", reply_markup=types.ReplyKeyboardRemove())


@dp.message(WorkoutStates.waiting_for_exercise)
async def add_exercise_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    day = data["day"]
    exercise = message.text

    workout_data = load_data(message.from_user.id)
    if day not in workout_data:
        workout_data[day] = []

    workout_data[day].append({"name": exercise})
    save_data(message.from_user.id, workout_data)

    await state.clear()
    await message.answer(f"✅ Упражнение добавлено в {day}!", reply_markup=get_main_kb())


### --- Добавление веса к упражнению ---
@dp.message(F.text == "✏️ Добавить вес")
async def add_weight_start(message: types.Message, state: FSMContext):
    workout_data = load_data(message.from_user.id)
    if not workout_data:
        await message.answer("График пуст. Сначала добавьте упражнения.")
        return

    buttons = [KeyboardButton(text=day) for day in workout_data.keys()]
    buttons.append(KeyboardButton(text=BACK_BUTTON))

    kb = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)

    await state.set_state(WorkoutStates.waiting_for_edit_day)
    await message.answer("Выберите день для добавления веса:", reply_markup=kb)


@dp.message(WorkoutStates.waiting_for_edit_day, F.text.in_(DAYS_OF_WEEK))
async def add_weight_day(message: types.Message, state: FSMContext):
    workout_data = load_data(message.from_user.id)
    day = message.text

    if day not in workout_data or not workout_data[day]:
        await message.answer("❌ В этом дне нет упражнений!")
        return

    await state.update_data(day=day)
    exercises = workout_data[day]

    buttons = [KeyboardButton(text=str(i)) for i in range(1, len(exercises) + 1)]
    buttons.append(KeyboardButton(text=BACK_BUTTON))

    kb = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)

    response = f"Упражнения в {day}:\n"
    for i, ex_data in enumerate(exercises, 1):
        exercise = ex_data['name']
        weight = ex_data.get('weight', '')
        if weight:
            response += f"{i}. {exercise} ({weight} кг)\n"
        else:
            response += f"{i}. {exercise}\n"

    await state.set_state(WorkoutStates.waiting_for_edit_choice)
    await message.answer(response + "\nВведите номер упражнения для добавления веса:", reply_markup=kb)


@dp.message(WorkoutStates.waiting_for_edit_choice, F.text.regexp(r'^\d+$'))
async def add_weight_exercise(message: types.Message, state: FSMContext):
    num = int(message.text)
    data = await state.get_data()
    day = data["day"]

    workout_data = load_data(message.from_user.id)
    exercises = workout_data[day]

    if num < 1 or num > len(exercises):
        await message.answer("❌ Неверный номер!")
        return

    await state.update_data(exercise_num=num - 1)
    await state.set_state(WorkoutStates.waiting_for_weight)
    await message.answer("Введите вес (в кг):", reply_markup=types.ReplyKeyboardRemove())


@dp.message(WorkoutStates.waiting_for_weight)
async def add_weight_finish(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text)
        if weight <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректный вес (положительное число)!")
        return

    data = await state.get_data()
    day = data["day"]
    exercise_num = data["exercise_num"]

    workout_data = load_data(message.from_user.id)
    workout_data[day][exercise_num]['weight'] = f"{weight:.1f}".rstrip('0').rstrip('.')
    save_data(message.from_user.id, workout_data)

    exercise_name = workout_data[day][exercise_num]['name']
    await state.clear()
    await message.answer(
        f"✅ Вес {weight} кг добавлен к упражнению '{exercise_name}' в {day}!",
        reply_markup=get_main_kb()
    )


### --- Удаление упражнения ---
@dp.message(F.text == "🗑️ Удалить упражнение")
async def remove_exercise_start(message: types.Message, state: FSMContext):
    workout_data = load_data(message.from_user.id)
    if not workout_data:
        await message.answer("График пуст. Нечего удалять.")
        return

    buttons = [KeyboardButton(text=day) for day in workout_data.keys()]
    buttons.append(KeyboardButton(text=BACK_BUTTON))

    kb = ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)

    await state.set_state(WorkoutStates.waiting_for_edit_day)
    await message.answer("Выберите день для удаления:", reply_markup=kb)


@dp.message(WorkoutStates.waiting_for_edit_day)
async def remove_exercise_day(message: types.Message, state: FSMContext):
    if message.text == BACK_BUTTON:
        await state.clear()
        return await edit_schedule_menu(message)

    workout_data = load_data(message.from_user.id)
    if message.text not in workout_data:
        await message.answer("❌ Такого дня нет в графике!")
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
    for i, ex_data in enumerate(exercises, 1):
        exercise = ex_data['name']
        weight = ex_data.get('weight', '')
        if weight:
            response += f"{i}. {exercise} ({weight} кг)\n"
        else:
            response += f"{i}. {exercise}\n"

    await state.set_state(WorkoutStates.waiting_for_edit_choice)
    await message.answer(response + "\nВведите номер для удаления:", reply_markup=kb)


@dp.message(WorkoutStates.waiting_for_edit_choice)
async def remove_exercise_finish(message: types.Message, state: FSMContext):
    if message.text == BACK_BUTTON:
        await state.clear()
        return await edit_schedule_menu(message)

    try:
        num = int(message.text)
    except ValueError:
        await message.answer("❌ Введите номер упражнения!")
        return

    data = await state.get_data()
    day = data["day"]

    workout_data = load_data(message.from_user.id)
    exercises = workout_data[day]

    if num < 1 or num > len(exercises):
        await message.answer("❌ Неверный номер!")
        return

    removed_ex = exercises.pop(num - 1)['name']
    if not exercises:
        del workout_data[day]

    save_data(message.from_user.id, workout_data)
    await state.clear()
    await message.answer(f"❌ Удалено: {removed_ex}", reply_markup=get_main_kb())


### --- Запуск бота ---
if __name__ == "__main__":
    dp.run_polling(bot)
