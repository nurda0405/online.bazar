import logging, random
import os, django, sys
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from asgiref.sync import sync_to_async

sys.path.append('..')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_bazar.settings')
django.setup()
from telegram.models import Category, Allowed_Seller, User

bot3 = Bot(token = '')
storage3 = MemoryStorage()
dp3 = Dispatcher(storage = storage3)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

admins = [888363480, 5091145450]

operations_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Қосу')], [KeyboardButton(text ='Өшіру')]])
things_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text ='Категория қосу')], [KeyboardButton(text ='Категория өшіру')],[KeyboardButton(text = 'Қанша юзер')]])
gender_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Ер адамға')], [KeyboardButton(text = 'Әйелге')], [KeyboardButton(text = 'Балаға')], [KeyboardButton(text = 'АРТҚА')]])
position_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Үсті')], [KeyboardButton(text = 'Асты')], [KeyboardButton(text = 'Аяқ киім')], [KeyboardButton(text = 'АРТҚА')]])
go_back_button = [KeyboardButton(text = 'АРТҚА')]
genders = ['Ер адамға', 'Әйелге', 'Балаға']
positions = ['Үсті', 'Асты', 'Аяқ киім']

gender_ids = {}
gender_ids['Ер адамға'] = 0
gender_ids['Әйелге'] = 1
gender_ids['Балаға'] = 2

position_ids = {}
position_ids['Үсті'] = 0
position_ids['Асты'] = 1
position_ids['Аяқ киім'] = 2

class Admin(StatesGroup):
    what = State()
    gender_id = State()
    cat_id = State()
    position_id = State()
    clothing = State()
    add_category = State()
    add_seller = State()
    operation = State()

async def check_for_new_seller(message: types.Message):
    if message.forward_from:
        username = message.forward_from.username
        isExists = await sync_to_async(Allowed_Seller.objects.filter(seller_username = username).first)()
        if isExists:
            await message.reply(text = 'Бұл сатушы бұрын қосылған')
        else:
            new_seller = Allowed_Seller(seller_username = username)
            await sync_to_async(new_seller.save)()
            await message.reply(text = 'Жаңа сатушы сәтті қосылды')

@dp3.message(Command('start'))
async def ask_what(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    if user_id in admins:
        await bot3.send_message(chat_id=user_id, text = 'Не істеу керек?', reply_markup=things_markup)
        await state.set_state(Admin.what)

@dp3.message(Admin.what)
async def ask_what(message: types.Message, state: FSMContext):
    await check_for_new_seller(message = message)
    if message.text == 'Категория қосу':
        await state.update_data(operation = 'Қосу')
        await message.reply(text = 'Жыныс?', reply_markup=gender_markup)
        await state.set_state(Admin.gender_id)
    elif message.text == 'Категория өшіру':
        await state.update_data(operation = 'Өшіру')
        await message.reply(text = 'Жыныс?', reply_markup=gender_markup)
        await state.set_state(Admin.gender_id)
    elif message.text == 'Қанша юзер':
        users = await sync_to_async(list)(User.objects.all())
        await message.reply(text = str(len(users)))
    


@dp3.message(Admin.gender_id)
async def ask_position(message: types.Message, state: FSMContext):
    await check_for_new_seller(message = message)
    text = message.text
    if text in genders:
        await message.reply(text = 'Киімнің категориясы?', reply_markup=position_markup)
        await state.update_data(gender_id = gender_ids[text])
        await state.set_state(Admin.position_id)
    elif text == 'АРТҚА':
        await message.reply(text = 'Не істеу керек?', reply_markup=things_markup)
        await state.set_state(Admin.what)

@dp3.message(Admin.position_id)
async def ask_clothing(message: types.Message, state: FSMContext):
    await check_for_new_seller(message = message)
    text = message.text
    data = await state.get_data()
    operation = data.get('operation')
    if text in positions:
        if operation == 'Қосу':
            await message.reply(text = 'Қандай киім қосасыз?', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text ='АРТҚА')]]))
            await state.update_data(position_id = position_ids[text])
            await state.set_state(Admin.clothing)
        elif operation == 'Өшіру':
            previous_message_id = message.message_id
            position_id = position_ids[text]
            gender_id = data.get('gender_id')
            categories = await sync_to_async(list)(Category.objects.filter(position_id = position_id, gender_id = gender_id))
            if categories:
                for category in categories:
                    await message.reply(text = category.cat_name, reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text = 'Өшіру', callback_data=f'delete#{category.cat_id}#{previous_message_id+1}')]]))
                    previous_message_id += 1
            else:
                await message.reply(text = 'Ешқандай киім табылмады')
    elif text == 'АРТҚА':
        await bot3.send_message(chat_id=message.from_user.id, text ="Жыныс?", reply_markup=gender_markup)
        await state.set_state(Admin.gender_id)
    
@dp3.callback_query(lambda c: c.data.startswith('delete#'))
async def handle_delete_product(callback_query: types.CallbackQuery):
    action, cat_id, message_id = callback_query.data.split('#')
    category = await sync_to_async(Category.objects.filter(cat_id = cat_id).first)()
    await sync_to_async(category.delete)()
    await bot3.delete_message(chat_id=callback_query.from_user.id, message_id=message_id)
    await bot3.send_message(chat_id=callback_query.from_user.id, text = 'Сәтті өшірілді')

@dp3.message(Admin.clothing)
async def ask_images(message: types.Message, state: FSMContext):
    await check_for_new_seller(message = message)
    data = await state.get_data()
    gender_id = data.get('gender_id')
    position_id = data.get('position_id')
    text = message.text
    if text == 'АРТҚА':
        await message.reply(text = 'Киімнің категориясы?', reply_markup=position_markup)
        await state.set_state(Admin.position_id)
    else:
        exists = await sync_to_async(Category.objects.filter(gender_id = gender_id, position_id = position_id, cat_name = text).first)()
        if not exists:
            new_clothing = Category(gender_id = gender_id, position_id = position_id, cat_name = text)
            await sync_to_async(new_clothing.save)()
            await message.reply(text = 'Сәтті қосылды')
        else:
            await message.reply(text = 'Бұндай киім бар')
        
@dp3.message(Admin.add_category)
async def add_seller(message: types.Message, state: FSMContext):
    await check_for_new_seller(message = message)
    new_category = Category(cat_name = message.text)
    await sync_to_async(new_category.save)()
    await message.reply(text = 'Сәтті қосылды')


async def main():
    # Run both bots' polling concurrently using separate tasks
    await dp3.start_polling(bot3)

if __name__ == '__main__':
    asyncio.run(main())