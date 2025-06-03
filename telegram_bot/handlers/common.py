from aiogram import Router, types
from ..utils.logger import logger

router = Router()

@router.message(commands=['start'])
async def cmd_start(message: types.Message):
    logger.info('User %s started', message.from_user.id)
    await message.answer('Привет! Используйте /profile чтобы заполнить анкету.')
