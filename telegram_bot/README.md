# Velosocial Telegram Bot

This bot provides a minimal social network for cyclists. Users can:

- Share their location and see nearby riders within 5 km.
- Create events with a route, date and optional group chat link.
- Maintain a short profile with a description and contacts.

Commands:

- `/start` – welcome message
- `/setprofile` – fill your description and contacts
- `/profile` – show your profile
- Send location – update coordinates
- `/nearby` – show riders near you
- `/create_event` – create a new ride
- `/events` – list upcoming events with join buttons
- `/myevents` – your joined rides

Store your bot token in the `BOT_TOKEN` environment variable or in `token.txt` next to `bot.py`.

Data is stored in a local JSON file (`data.json`). See `bot.py` for details.
