import aiosqlite
from contextlib import asynccontextmanager
from ..config import config

CREATE_USERS = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    contacts TEXT,
    lat REAL,
    lon REAL,
    updated_at TEXT
);
'''

CREATE_EVENTS = '''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER,
    route TEXT,
    date TEXT,
    chat_link TEXT
);
'''

CREATE_PARTICIPANTS = '''
CREATE TABLE IF NOT EXISTS participants (
    event_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY(event_id, user_id)
);
'''

async def init_db():
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_EVENTS)
        await db.execute(CREATE_PARTICIPANTS)
        await db.commit()

@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(config.db_path)
    try:
        yield db
    finally:
        await db.close()
