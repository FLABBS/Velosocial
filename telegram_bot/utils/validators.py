from aiogram import types

MAX_DESC = 200
MAX_CONTACT = 100

async def validate_description(message: types.Message) -> bool:
    return len(message.text) <= MAX_DESC

async def validate_contact(message: types.Message) -> bool:
    return len(message.text) <= MAX_CONTACT
