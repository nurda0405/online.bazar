import logging, random
import os, django, sys
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile, InputFile
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from asgiref.sync import sync_to_async
from aiogram.fsm.storage.redis import RedisStorage

sys.path.append('..')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_bazar.settings')
django.setup()
from telegram.models import Category, Product, User

bot1 = Bot(token='')
storage1 = RedisStorage.from_url('redis://localhost:6379/0')
#storage1 = MemoryStorage()
dp1 = Dispatcher(storage = storage1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

gender_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Ер адамға')], [KeyboardButton(text = 'Әйелге')], [KeyboardButton(text = 'Балаға')]])
position_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Үсті')], [KeyboardButton(text = 'Асты')], [KeyboardButton(text = 'Аяқ киім')], [KeyboardButton(text = 'АРТҚА')]])
skip_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Келесі')], [KeyboardButton(text = 'АРТҚА')]])
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

class Client(StatesGroup):
    main_page = State()
    gender_id = State()
    position_id = State()
    clothing = State()
    index = State()
    cat_id = State()

@dp1.message(Command('start'))
async def ask_gender(message: types.Message, state: FSMContext):
    new_user = User(id = message.chat.id)
    await sync_to_async(new_user.save)()
    await bot1.send_message(chat_id=message.from_user.id, text ="Кімге киім іздейсіз?", reply_markup=gender_markup)
    await state.set_state(Client.gender_id)

@dp1.message(Client.gender_id)
async def ask_position(message: types.Message, state: FSMContext):
    text = message.text
    if text in genders:
        await message.reply(text = 'Киімнің категориясы?', reply_markup=position_markup)
        await state.update_data(gender_id = gender_ids[text])
        await state.set_state(Client.position_id)

@dp1.message(Client.position_id)
async def ask_clothing(message: types.Message, state: FSMContext):
    text = message.text
    if text in positions:
        data = await state.get_data()
        gender_id = data.get('gender_id')
        clothes = [[KeyboardButton(text=category.cat_name)] for category in await sync_to_async(list)(Category.objects.filter(gender_id = gender_id, position_id = position_ids[text]))] + [go_back_button]
        await message.reply(text = 'Қандай киім іздейсіз?', reply_markup = ReplyKeyboardMarkup(keyboard=clothes))
        await state.update_data(position_id = position_ids[text])
        await state.set_state(Client.clothing)
    elif text == 'АРТҚА':
        await bot1.send_message(chat_id=message.from_user.id, text ="Кімге киім іздейсіз?", reply_markup=gender_markup)
        await state.set_state(Client.gender_id)

@dp1.message(Client.clothing)
async def show_products(message: types.Message, state = FSMContext):
    data = await state.get_data()
    gender_id = data.get('gender_id')
    position_id = data.get('position_id')
    text = message.text
    categories = [category.cat_name for category in await sync_to_async(list)(Category.objects.filter(gender_id = gender_id, position_id = position_id))]
    
    if text in categories:
        cat_object = await sync_to_async(Category.objects.filter(cat_name = text, gender_id = gender_id, position_id = position_id).first)()
        cat_id = cat_object.cat_id
        products = await sync_to_async(list)(Product.objects.filter(cat_id = cat_id))
        
        if products:
            await message.reply(text = 'Қазір!', reply_markup=skip_markup)
            #instead of making list all time, create initial list and change it while the seller adds a product

            await state.update_data(category = text)
            await state.update_data(index = 0)
            await state.update_data(cat_id = cat_id)
            await state.set_state(Client.index)

            #get the images from the image_path folder and then send them as a media group
            
            product = products[0]
            media = MediaGroupBuilder()
            images = [entry.name for entry in os.scandir(product.image_path) if entry.is_file()]
            if len(images) == 1:
                photo = InputFile(product.image_path + '/' + image)
                await bot1.send_photo(photo=photo, chat_id=message.chat.id, caption = product.description, reply_markup=InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text = 'Сатушы➡️', url = f'https://t.me/@{product.seller_username}')]]))
            else:
                for image in images:
                    media.add_photo(media=FSInputFile(product.image_path + '/' + image), type = "photo") 
                await bot1.send_media_group(chat_id=message.chat.id, media=media.build()) 
                await bot1.send_message(chat_id=message.chat.id, text = product.description, reply_markup=InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text = 'Сатушы➡️', url = f'https://t.me/@{product.seller_username}')]]))
            product.views += 1
            await sync_to_async(product.save)()
        else:
            await message.reply(text = 'Қазірше бұл категорияда киімдер енгізілмеген')
    elif text == 'АРТҚА':
        data = await state.get_data()
        await message.reply(text = 'Киімнің категориясы?', reply_markup=position_markup)
        await state.set_state(Client.position_id)


@dp1.message(Client.index)
async def skip(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get('cat_id')
    index = data.get('index')
    user_id = message.chat.id
    products = await sync_to_async(list)(Product.objects.filter(cat_id = cat_id))

    if message.text == 'Келесі':
        if index + 1 < len(products):
            product = products[index + 1]
            media = MediaGroupBuilder()
            images = [entry.name for entry in os.scandir(product.image_path) if entry.is_file()]
            if len(images) == 1:
                photo = InputFile(product.image_path + '/' + image)
                await bot1.send_photo(photo=photo, chat_id=message.chat.id, caption = product.description, reply_markup=InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text = 'Сатушы➡️', url = f'https://t.me/@{product.seller_username}')]]))
            else:
                for image in images:
                    media.add_photo(media=FSInputFile(product.image_path + '/' + image), type = "photo") 
                await bot1.send_media_group(chat_id=message.chat.id, media=media.build()) 
                await bot1.send_message(chat_id=message.chat.id, text = product.description, reply_markup=InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text = 'Сатушы➡️', url = f'https://t.me/@{product.seller_username}')]]))
            await state.update_data(index = index + 1)
            product.views += 1
            await sync_to_async(product.save)()
        else:
            await bot1.send_message(chat_id = user_id, text = 'Бұл соңғы киім болған, басқа киім таңдаңыз', reply_markup=ReplyKeyboardMarkup(keyboard=[go_back_button]))
    elif message.text == 'АРТҚА':
        data = await state.get_data()
        gender_id = data.get('gender_id')
        position_id = data.get('position_id')
        categories = [[KeyboardButton(text=category.cat_name)] for category in await sync_to_async(list)(Category.objects.filter(gender_id = gender_id, position_id = position_id))] + [go_back_button]
        await message.reply(text = 'Қандай киім іздейсіз?', reply_markup = ReplyKeyboardMarkup(keyboard=categories))
        await state.set_state(Client.clothing)
    else:
        await bot1.delete_message(chat_id=message.chat.id, message_id = message.message_id)


async def main():
    # Run both bots' polling concurrently using separate tasks
    await dp1.start_polling(bot1)

if __name__ == '__main__':
    asyncio.run(main())