import os
import sys
import pytest

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, BASE)
from telegram_bot.db.database import init_db
from telegram_bot.db import queries

async def setup_db(tmp_path):
    os.environ['DB_PATH'] = str(tmp_path / 'test.db')
    await init_db()

@pytest.mark.asyncio
async def test_user_crud(tmp_path):
    await setup_db(tmp_path)
    await queries.upsert_user(1, 'Ivan', 'desc', '@ivan')
    user = await queries.get_user(1)
    assert user.name == 'Ivan'
