import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
import math

TOKEN = "7544908894:AAFbDrA2u79O6ymTwdbY_UfXAzluDVmpCSk"
DB_PATH = "goactive.db"
RADIUS_KM = 2

# База данных
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        lat REAL,
        lon REAL,
        is_ready INTEGER DEFAULT 0,
        comment TEXT,
        last_update TIMESTAMP
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_id INTEGER,
        description TEXT,
        lat REAL,
        lon REAL,
        event_time TIMESTAMP,
        max_participants INTEGER,
        participants TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Haversine distance
def distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2-lat1)
    dlambda = math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# FSM для создания события
class EventStates(StatesGroup):
    description = State()
    location = State()
    event_time = State()

class JoinEventStates(StatesGroup):
    event_id = State()

class ProfileStates(StatesGroup):
    comment = State()

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Команды

@dp.message(Command("start"))
async def start(msg: types.Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (telegram_id, username, last_update) VALUES (?, ?, ?)",
              (msg.from_user.id, msg.from_user.username, datetime.now()))
    conn.commit()
    conn.close()
    await msg.answer("Привет! Это GoActive — сервис поиска людей для совместных активностей. "
                     "\n\n📍 Отправь мне своё местоположение через скрепку, чтобы другие могли тебя найти.")

@dp.message(F.location)
async def location(msg: types.Message):
    lat, lon = msg.location.latitude, msg.location.longitude
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET lat=?, lon=?, last_update=? WHERE telegram_id=?",
              (lat, lon, datetime.now(), msg.from_user.id))
    conn.commit()
    conn.close()
    await msg.answer("Локация сохранена! Теперь ты можешь искать людей или мероприятия рядом. "
                     "\nИспользуй /ready чтобы стать видимым для поиска.")

@dp.message(Command("profile"))
async def profile(msg: types.Message, state: FSMContext):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT comment, is_ready FROM users WHERE telegram_id=?", (msg.from_user.id,))
    res = c.fetchone()
    comment = res[0] if res else ""
    is_ready = "Готов сейчас" if res and res[1] else "Не готов"
    await msg.answer(f"Твой профиль:\n\nСтатус: {is_ready}\nКомментарий: {comment or 'нет'}"
                     "\n\nЧтобы добавить или изменить комментарий, напиши /comment")
    conn.close()

@dp.message(Command("comment"))
async def comment_start(msg: types.Message, state: FSMContext):
    await msg.answer("Напиши свой новый комментарий (до 200 символов):")
    await state.set_state(ProfileStates.comment)

@dp.message(ProfileStates.comment, F.text)
async def update_comment(msg: types.Message, state: FSMContext):
    comment = msg.text[:200]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET comment=? WHERE telegram_id=?", (comment, msg.from_user.id))
    conn.commit()
    conn.close()
    await msg.answer("Комментарий обновлён! Используй /profile чтобы проверить.")
    await state.clear()

@dp.message(Command("ready"))
async def ready(msg: types.Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_ready=1 WHERE telegram_id=?", (msg.from_user.id,))
    conn.commit()
    conn.close()
    await msg.answer("Теперь ты отмечен как 'Готов сейчас' и появляешься в поиске!")

@dp.message(Command("notready"))
async def notready(msg: types.Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_ready=0 WHERE telegram_id=?", (msg.from_user.id,))
    conn.commit()
    conn.close()
    await msg.answer("Ты больше не видим для поиска.")

@dp.message(Command("find_people"))
async def find_people(msg: types.Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lat, lon FROM users WHERE telegram_id=?", (msg.from_user.id,))
    user_loc = c.fetchone()
    if not user_loc or user_loc[0] is None or user_loc[1] is None:
        await msg.answer("Сначала отправь свою геолокацию!")
        conn.close()
        return
    my_lat, my_lon = user_loc
    c.execute("SELECT telegram_id, username, comment, lat, lon FROM users WHERE is_ready=1 AND telegram_id<>?", (msg.from_user.id,))
    users = c.fetchall()
    res = []
    for u in users:
        if u[3] is None or u[4] is None:
            continue
        dist = distance(my_lat, my_lon, u[3], u[4])
        if dist <= RADIUS_KM:
            res.append(f"@{u[1] or u[0]} — {u[2] or 'нет описания'} ({dist:.1f} км)")
    await msg.answer("Люди рядом:\n\n" + ("\n".join(res) if res else "Никого нет поблизости."))
    conn.close()

# --- Создание события с FSM
@dp.message(Command("create_event"))
async def create_event(msg: types.Message, state: FSMContext):
    await msg.answer("Напиши описание события (до 100 символов):")
    await state.set_state(EventStates.description)

@dp.message(EventStates.description, F.text)
async def event_desc(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text[:100])
    await msg.answer("Отправь место встречи (геолокацию через скрепку):")
    await state.set_state(EventStates.location)

@dp.message(EventStates.location, F.location)
async def event_location(msg: types.Message, state: FSMContext):
    await state.update_data(lat=msg.location.latitude, lon=msg.location.longitude)
    await msg.answer("Укажи время начала (ДД.ММ.ГГГГ ЧЧ:ММ):")
    await state.set_state(EventStates.event_time)

@dp.message(EventStates.event_time, F.text)
async def event_time(msg: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(msg.text, "%d.%m.%Y %H:%M")
    except Exception:
        await msg.answer("Формат времени неверный! Пример: 31.05.2025 19:00")
        return
    data = await state.get_data()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO events
        (creator_id, description, lat, lon, event_time, max_participants, participants)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (msg.from_user.id, data['description'], data['lat'], data['lon'], dt, 20, str(msg.from_user.id))
    )
    conn.commit()
    conn.close()
    await msg.answer("Событие создано! Теперь оно видно всем пользователям рядом.")
    await state.clear()

@dp.message(Command("events"))
async def events(msg: types.Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lat, lon FROM users WHERE telegram_id=?", (msg.from_user.id,))
    user_loc = c.fetchone()
    if not user_loc or user_loc[0] is None or user_loc[1] is None:
        await msg.answer("Сначала отправь свою геолокацию!")
        conn.close()
        return
    my_lat, my_lon = user_loc
    now = datetime.now()
    c.execute("SELECT id, description, lat, lon, event_time FROM events WHERE event_time>?",(now,))
    events = c.fetchall()
    res = []
    for e in events:
        if e[2] is None or e[3] is None:
            continue
        dist = distance(my_lat, my_lon, e[2], e[3])
        try:
            dt_str = datetime.strptime(e[4], "%Y-%m-%d %H:%M:%S")
        except Exception:
            dt_str = e[4]
        if dist <= RADIUS_KM:
            res.append(f"ID: {e[0]}\n{e[1]}\nКогда: {dt_str if isinstance(dt_str, str) else dt_str.strftime('%d.%m.%Y %H:%M')}\nГде: {dist:.1f} км от тебя")
    await msg.answer("События рядом:\n\n" + ("\n\n".join(res) if res else "Нет событий рядом."))
    conn.close()

@dp.message(Command("join_event"))
async def join_event(msg: types.Message, state: FSMContext):
    await msg.answer("Напиши ID события, к которому хочешь присоединиться:")
    await state.set_state(JoinEventStates.event_id)

@dp.message(JoinEventStates.event_id, F.text)
async def handle_join(msg: types.Message, state: FSMContext):
    try:
        event_id = int(msg.text)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT participants FROM events WHERE id=?", (event_id,))
        row = c.fetchone()
        if not row:
            await msg.answer("Событие не найдено.")
            conn.close()
            await state.clear()
            return
        participants = row[0].split(",") if row[0] else []
        if str(msg.from_user.id) not in participants:
            participants.append(str(msg.from_user.id))
            c.execute("UPDATE events SET participants=? WHERE id=?", (",".join(participants), event_id))
            conn.commit()
        conn.close()
        await msg.answer("Ты присоединился к событию!")
    except Exception:
        await msg.answer("Ошибка. Проверь ID события.")
    finally:
        await state.clear()

# --- Запуск

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
