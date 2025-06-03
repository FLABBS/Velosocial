from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from ..db import queries
from ..utils import validators

router = Router()

class ProfileForm(StatesGroup):
    description = State()
    contacts = State()

@router.message(commands=['profile'])
async def show_profile(message: types.Message):
    user = await queries.get_user(message.from_user.id)
    if not user:
        await message.answer('Профиль не найден. Используйте /profile_edit')
        return
    text = f"{user.name}\n{user.description}\nКонтакты: {user.contacts}"
    await message.answer(text)

@router.message(commands=['profile_edit'])
async def edit_profile(message: types.Message, state: FSMContext):
    await message.answer('Напишите пару слов о себе:')
    await state.set_state(ProfileForm.description)

@router.message(ProfileForm.description, F.text)
async def process_desc(message: types.Message, state: FSMContext):
    if not await validators.validate_description(message):
        await message.answer('Слишком длинно, попробуйте короче')
        return
    await state.update_data(description=message.text)
    await message.answer('Оставьте контакт для связи:')
    await state.set_state(ProfileForm.contacts)

@router.message(ProfileForm.contacts, F.text)
async def process_contacts(message: types.Message, state: FSMContext):
    if not await validators.validate_contact(message):
        await message.answer('Некорректный контакт')
        return
    data = await state.get_data()
    await queries.upsert_user(
        user_id=message.from_user.id,
        name=message.from_user.full_name,
        description=data['description'],
        contacts=message.text,
    )
    await state.clear()
    await message.answer('Профиль сохранён')
