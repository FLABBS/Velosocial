import json
import os
import datetime
from math import radians, cos, sin, sqrt, atan2

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


class DataStore:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {"users": {}, "events": {}}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def update_user(self, user_id: str, **kwargs):
        self.data["users"].setdefault(user_id, {}).update(kwargs)
        self.save()

    def get_user(self, user_id: str):
        return self.data["users"].get(user_id)

    def add_event(self, event: dict) -> str:
        event_id = str(len(self.data["events"]) + 1)
        self.data["events"][event_id] = event
        self.save()
        return event_id

    def get_events(self):
        return self.data["events"]

data_store = DataStore()

# ---- Helpers ----
DESC, CONTACTS = range(2)
EVENT_ROUTE, EVENT_DATETIME, EVENT_CHATLINK = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    data_store.update_user(str(user.id), name=user.first_name)
    await update.message.reply_text(
        "Привет! Используйте /setprofile для заполнения анкеты и отправьте свою геопозицию, чтобы увидеть других велолюбителей."
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = data_store.get_user(str(update.effective_user.id))
    if not user_data:
        await update.message.reply_text("Профиль не найден. Используйте /setprofile.")
        return
    text = f"{user_data.get('name','')}\n{user_data.get('desc','')}"
    contacts = user_data.get("contacts")
    if contacts:
        text += f"\nКонтакты: {contacts}"
    await update.message.reply_text(text)


async def setprofile_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Кратко расскажите о себе:")
    return DESC


async def setprofile_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["desc"] = update.message.text
    await update.message.reply_text("Оставьте контакт для связи (например, @username):")
    return CONTACTS


async def setprofile_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    desc = context.user_data.pop("desc", "")
    contacts = update.message.text
    data_store.update_user(
        str(update.effective_user.id),
        name=update.effective_user.first_name,
        desc=desc,
        contacts=contacts,
    )
    await update.message.reply_text("Профиль обновлен.")
    return ConversationHandler.END


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    loc = update.message.location
    if loc:
        data_store.update_user(
            str(update.effective_user.id),
            location={"lat": loc.latitude, "lon": loc.longitude},
        )
        await update.message.reply_text("Локация сохранена.")


def _distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


async def nearby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    me = data_store.get_user(str(update.effective_user.id))
    if not me or "location" not in me:
        await update.message.reply_text("Сначала отправьте свою геопозицию.")
        return
    lat1 = me["location"]["lat"]
    lon1 = me["location"]["lon"]
    riders = []
    for uid, info in data_store.data["users"].items():
        if uid == str(update.effective_user.id):
            continue
        loc = info.get("location")
        if not loc:
            continue
        if _distance(lat1, lon1, loc["lat"], loc["lon"]) <= 5000:
            riders.append(f"{info.get('name', 'Райдер')} ({info.get('contacts', '-')})")
    if riders:
        await update.message.reply_text("Рядом находятся:\n" + "\n".join(riders))
    else:
        await update.message.reply_text("Поблизости никого нет.")


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    events_data = data_store.get_events()
    if not events_data:
        await update.message.reply_text("Событий пока нет.")
        return
    lines = []
    for eid, ev in events_data.items():
        line = f"{eid}) {ev['route']} — {ev['date']}"
        if ev.get('chat_link'):
            line += f"\nЧат: {ev['chat_link']}"
        lines.append(line)
    await update.message.reply_text("\n\n".join(lines))


async def create_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Опишите маршрут (например, Город А → Город Б):")
    return EVENT_ROUTE


async def create_event_route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["route"] = update.message.text
    await update.message.reply_text("Укажите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ):")
    return EVENT_DATETIME


async def create_event_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    try:
        dt = datetime.datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text("Неверный формат. Попробуйте ещё раз:")
        return EVENT_DATETIME
    context.user_data["date"] = dt.strftime("%Y-%m-%d %H:%M")
    await update.message.reply_text("Ссылка на чат (можно пропустить, отправьте -):")
    return EVENT_CHATLINK


async def create_event_chatlink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_link = update.message.text
    event = {
        "creator": str(update.effective_user.id),
        "route": context.user_data.pop("route"),
        "date": context.user_data.pop("date"),
        "chat_link": chat_link if chat_link != "-" else "",
        "participants": [str(update.effective_user.id)],
    }
    event_id = data_store.add_event(event)
    await update.message.reply_text(f"Событие создано с ID {event_id}.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("Set BOT_TOKEN environment variable")
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("nearby", nearby))
    application.add_handler(CommandHandler("events", events))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    profile_conv = ConversationHandler(
        entry_points=[CommandHandler("setprofile", setprofile_start)],
        states={
            DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, setprofile_desc)],
            CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, setprofile_contacts)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(profile_conv)

    event_conv = ConversationHandler(
        entry_points=[CommandHandler("create_event", create_event_start)],
        states={
            EVENT_ROUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_event_route)],
            EVENT_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_event_datetime)],
            EVENT_CHATLINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_event_chatlink)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(event_conv)

    application.run_polling()


if __name__ == "__main__":
    main()
