from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from ..db import queries

router = Router()

class EventForm(StatesGroup):
    route = State()
    date = State()
    chat = State()

@router.message(commands=['events'])
async def list_events(message: types.Message):
    events = await queries.get_events()
    if not events:
        await message.answer('Событий нет')
        return
    for ev in events:
        participants = await queries.get_event_participants(ev.id)
        text = f"{ev.route}\nДата: {ev.date}\nУчастники: {len(participants)}"
        kb = [[types.InlineKeyboardButton(text='Вступить', callback_data=f'join:{ev.id}')]]
        if message.from_user.id in participants:
            kb = [[types.InlineKeyboardButton(text='Выйти', callback_data=f'leave:{ev.id}')]]
        if ev.chat_link:
            kb.append([types.InlineKeyboardButton(text='Чат', url=ev.chat_link)])
        await message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))

@router.callback_query(lambda c: c.data and c.data.startswith(('join','leave')))
async def callbacks(call: types.CallbackQuery):
    action, eid = call.data.split(':', 1)
    if action == 'join':
        await queries.join_event(int(eid), call.from_user.id)
        await call.answer('Вы записаны')
    else:
        await queries.leave_event(int(eid), call.from_user.id)
        await call.answer('Вы вышли')
    await call.message.delete_reply_markup()

@router.message(commands=['event_create'])
async def event_create(message: types.Message, state: FSMContext):
    await message.answer('Опишите маршрут')
    await state.set_state(EventForm.route)

@router.message(EventForm.route, F.text)
async def event_route(message: types.Message, state: FSMContext):
    await state.update_data(route=message.text)
    await message.answer('Дата и время (ГГГГ-ММ-ДД ЧЧ:ММ)')
    await state.set_state(EventForm.date)

@router.message(EventForm.date, F.text)
async def event_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer('Ссылка на чат, если есть, иначе -')
    await state.set_state(EventForm.chat)

@router.message(EventForm.chat, F.text)
async def event_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = await queries.create_event(
        creator_id=message.from_user.id,
        route=data['route'],
        date=data['date'],
        chat_link='' if message.text == '-' else message.text,
    )
    await state.clear()
    await message.answer(f'Событие создано ({event_id})')
