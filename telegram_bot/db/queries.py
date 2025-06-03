import datetime
from typing import Optional, List
from .database import get_db
from .models import User, Event

async def upsert_user(user_id: int, name: str, description: str, contacts: str):
    async with get_db() as db:
        await db.execute(
            'INSERT INTO users (id, name, description, contacts, updated_at) VALUES (?, ?, ?, ?, ?)'
            ' ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description, contacts=excluded.contacts, updated_at=excluded.updated_at',
            (user_id, name, description, contacts, datetime.datetime.utcnow().isoformat())
        )
        await db.commit()

async def update_location(user_id: int, lat: float, lon: float):
    async with get_db() as db:
        await db.execute(
            'UPDATE users SET lat=?, lon=?, updated_at=? WHERE id=?',
            (lat, lon, datetime.datetime.utcnow().isoformat(), user_id)
        )
        await db.commit()

async def get_user(user_id: int) -> Optional[User]:
    async with get_db() as db:
        cur = await db.execute(
            'SELECT id,name,description,contacts,lat,lon FROM users WHERE id=?',
            (user_id,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        return User(*row)

async def create_event(creator_id: int, route: str, date: str, chat_link: str) -> int:
    async with get_db() as db:
        cur = await db.execute(
            'INSERT INTO events (creator_id, route, date, chat_link) VALUES (?, ?, ?, ?)',
            (creator_id, route, date, chat_link)
        )
        event_id = cur.lastrowid
        await db.execute('INSERT INTO participants (event_id, user_id) VALUES (?, ?)', (event_id, creator_id))
        await db.commit()
        return event_id

async def get_events() -> List[Event]:
    async with get_db() as db:
        cur = await db.execute('SELECT id,creator_id,route,date,chat_link FROM events')
        rows = await cur.fetchall()
        return [Event(*row) for row in rows]

async def join_event(event_id: int, user_id: int):
    async with get_db() as db:
        await db.execute('INSERT OR IGNORE INTO participants (event_id, user_id) VALUES (?, ?)', (event_id, user_id))
        await db.commit()

async def leave_event(event_id: int, user_id: int):
    async with get_db() as db:
        await db.execute('DELETE FROM participants WHERE event_id=? AND user_id=?', (event_id, user_id))
        await db.commit()

async def get_event_participants(event_id: int) -> List[int]:
    async with get_db() as db:
        cur = await db.execute('SELECT user_id FROM participants WHERE event_id=?', (event_id,))
        rows = await cur.fetchall()
        return [r[0] for r in rows]
