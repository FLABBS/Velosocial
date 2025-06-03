# Velosocial Telegram Bot

This is a modular Telegram bot for cyclists built with **aiogram** and `aiosqlite`.
It lets riders create short profiles, share locations and organize group rides.

## Features
- Profile management with FSM
- Nearby events list, creation and participation with inline buttons
- Simple rate limiting and input validation
- Async SQLite database

## Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file with `BOT_TOKEN=...` (and optionally `DB_PATH`)
3. Run the bot from the repository root. Because the sources are now inside the
   `Go.Active` directory, add it to `PYTHONPATH` when launching:
   ```bash
   PYTHONPATH=Go.Active python -m telegram_bot.app
   ```

## Project Structure
- `app.py` – bot startup script
- `config.py` – environment configuration
- `db/` – async database layer
- `handlers/` – command handlers and FSM scenes
- `utils/` – logger, rate limit and validators
- `tests/` – example tests

## Running tests
```
pytest -q
```
