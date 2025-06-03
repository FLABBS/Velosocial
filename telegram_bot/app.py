import asyncio
from aiogram import Bot, Dispatcher
from .config import config
from .db.database import init_db
from .handlers import common, profiles, events
from .utils.rate_limit import RateLimiter
from .utils.logger import logger

rate_limiter = RateLimiter(period=1.0)

async def main():
    if not config.bot_token:
        raise RuntimeError('BOT_TOKEN not set')
    await init_db()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    dp.include_router(common.router)
    dp.include_router(profiles.router)
    dp.include_router(events.router)

    @dp.message()
    async def limit_all(message):
        if not rate_limiter.check(message.from_user.id):
            await message.answer('Слишком часто. Подождите.')
            return False
        return True

    logger.info('Bot starting')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
