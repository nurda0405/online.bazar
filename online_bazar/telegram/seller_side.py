import logging
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
from aiogram.types import ContentType
from aiogram.fsm.storage.redis import RedisStorage
import shutil

sys.path.append('..')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_bazar.settings')
django.setup()
from telegram.models import Category, Product, Allowed_Seller

bot2 = Bot(token='')
storage2 = RedisStorage.from_url('redis://localhost:6379/1')
#storage1 = MemoryStorage()
dp2 = Dispatcher(storage = storage2)
caption = False
first_image = True
folder_path = 'not used yet'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

main_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Киім қосу')], [KeyboardButton(text='Менің киімдерім')]])
gender_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Ер адамға')], [KeyboardButton(text = 'Әйелге')], [KeyboardButton(text = 'Балаға')], [KeyboardButton(text = 'АРТҚА')]])
position_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Үсті')], [KeyboardButton(text = 'Асты')], [KeyboardButton(text = 'Аяқ киім')], [KeyboardButton(text = 'АРТҚА')]])
skip_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Келесі')], [KeyboardButton(text = 'АРТҚА')]])
new_product_added_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Тағы қосу')], [KeyboardButton(text = 'АРТҚА')], [KeyboardButton(text = 'БАСТЫ БЕТКЕ')]])
go_back_button = [KeyboardButton(text = 'АРТҚА')]
genders = ['Ер адамға', 'Әйелге', 'Балаға']
positions = ['Үсті', 'Асты', 'Аяқ киім']
categories_list = {}
global_products = {}

gender_ids = {}
gender_ids['Ер адамға'] = 0
gender_ids['Әйелге'] = 1
gender_ids['Балаға'] = 2

position_ids = {}
position_ids['Үсті'] = 0
position_ids['Асты'] = 1
position_ids['Аяқ киім'] = 2

class Form(StatesGroup):
    main_page = State()
    name = State()
    location = State()
    description = State()
    gender_id = State()
    position_id = State()
    clothing = State()
    images = State()
    cat_id = State()
    description = State()
    new_product_added = State()

    ask_position = State()
    ask_product = State()
    show_products = State()
    index = State()
    delete_message_id = State()
    delete_message = State()

#button with the id of the next seller
@dp2.message(Command('start'))
async def ask_name(message: types.Message, state: FSMContext):
    username = message.from_user.username
    allowed_user = await sync_to_async(Allowed_Seller.objects.filter(seller_username = username).first)()
    if allowed_user:
        await bot2.send_message(chat_id=message.from_user.id, text ="Сатушылар қатарына қош келдіңіз! Кімге киім қосасыз?", reply_markup=gender_markup)
        await state.set_state(Form.gender_id)
    else:
        await message.reply(text = 'Сізге ботпен қолдануға рұқсат берілмеген.')

@dp2.message(Form.gender_id)
async def ask_position(message: types.Message, state: FSMContext):
    text = message.text
    if text in genders:
        await message.reply(text = 'Киімнің категориясы?', reply_markup=position_markup)
        await state.update_data(gender_id = gender_ids[text])
        await state.set_state(Form.position_id)
    elif text == 'АРТҚА':
        await message.reply(text ='Сіз басты беттесіз', reply_markup=main_markup)
        await state.set_state(Form.main_page)

@dp2.message(Form.position_id)
async def ask_clothing(message: types.Message, state: FSMContext):
    text = message.text
    if text in positions:
        data = await state.get_data()
        gender_id = data.get('gender_id')
        clothes = [[KeyboardButton(text=category.cat_name)] for category in await sync_to_async(list)(Category.objects.filter(gender_id = gender_id, position_id = position_ids[text]))] + [go_back_button]
        await message.reply(text = 'Қандай киім қосасыз?', reply_markup = ReplyKeyboardMarkup(keyboard=clothes))
        await state.update_data(position_id = position_ids[text])
        await state.set_state(Form.clothing)
    elif text == 'АРТҚА':
        await bot2.send_message(chat_id=message.from_user.id, text ="Кімге киім қосасыз?", reply_markup=gender_markup)
        await state.set_state(Form.gender_id)
    
@dp2.message(Form.clothing)
async def ask_images(message: types.Message, state: FSMContext):
    global first_image
    data = await state.get_data()
    gender_id = data.get('gender_id')
    position_id = data.get('position_id')
    text = message.text
    categories = [category.cat_name for category in await sync_to_async(list)(Category.objects.filter(gender_id = gender_id, position_id = position_id))]
    if text in categories:
        cat_object = await sync_to_async(Category.objects.filter(cat_name = text, gender_id = gender_id, position_id = position_id).first)()
        cat_id = cat_object.cat_id
        await state.update_data(cat_id = cat_id)
        await message.reply(text = "Киіміңіздің суреттерін таңдап, маған жіберіңіз", reply_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='АРТҚА')]]))
        first_image = True
        await state.set_state(Form.images)
    elif message.text == 'АРТҚА':
        await message.reply(text = 'Киімнің категориясы?', reply_markup=position_markup)
        await state.set_state(Form.position_id)

@dp2.message(Form.images)
async def store_images(message: types.Message, state: FSMContext):
    global folder_path, clothes
    data = await state.get_data()
    cat_id = data.get('cat_id')
    products = await sync_to_async(list)(Product.objects.filter(cat_id = cat_id))
    max_index = 0
    for product in products:
        max_index = max(max_index, int(product.image_path.split('/')[-1]))

    if message.content_type == "photo":
        folder_path = f'../images/{cat_id}/{max_index + 1}'
        os.makedirs(folder_path, exist_ok= True)
        
        photo = message.photo[-1]
        file_info = await bot2.get_file(photo.file_id)
        file_path = file_info.file_path
        await bot2.download_file(file_path, folder_path + f'/{photo.file_id}.jpg')        
        await message.reply(text = 'Енді киіміңізді жарнамалаңыз. Жарнама кем дегенде 5 сөзден тұруы қажет')
        await state.set_state(Form.description)

@dp2.message(Form.description)
async def store_description(message: types.Message, state: FSMContext):
    global folder_path
    data = await state.get_data()
    cat_id = data.get('cat_id')
    username = message.from_user.username
    
    if message.content_type == "photo":        
        photo = message.photo[-1]
        file_info = await bot2.get_file(photo.file_id)
        file_path = file_info.file_path
        await bot2.download_file(file_path, folder_path + f'/{photo.file_id}.jpg')
    elif message.content_type == 'text':
        text = message.text
        if len(text.split(' ')) >= 5:
            new_product = Product(seller_username = username, cat_id = cat_id, image_path = folder_path, description = text, views = 0)
            await sync_to_async(new_product.save)()
            await message.reply(text = 'Сіздің киіміңіз сәтті қосылды!', reply_markup=new_product_added_markup)
            await state.set_state(Form.new_product_added)
        else:
            await message.reply(text = 'Жарнамаңыз кем дегенде 5 сөз болуы керек. Өтінемін, маған жарнамаңызды қайта жазып жіберіңіз...')

@dp2.message(Form.new_product_added)
async def ask_what_to_do_next(message: types.Message, state: FSMContext):
    if message.text == 'БАСТЫ БЕТКЕ':
        await message.reply(text ='Сіз басты беттесіз', reply_markup=main_markup)
        await state.set_state(Form.main_page)
    elif message.text == 'АРТҚА':
        data = await state.get_data()
        gender_id = data.get('gender_id')
        position_id = data.get('position_id')
        categories = [[KeyboardButton(text=category.cat_name)] for category in await sync_to_async(list)(Category.objects.filter(gender_id = gender_id, position_id = position_id))] + [go_back_button]
        await message.reply(text ='Қандай киім қосайын деп едіңіз?', reply_markup=ReplyKeyboardMarkup(keyboard=categories))
        await state.set_state(Form.clothing)
    elif message.text == 'Тағы қосу':
        await message.reply(text = "Киіміңіздің суреттерін таңдап, маған жіберіңіз", reply_markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='БАСТЫ БЕТКЕ')]])) # handle this text
        await state.set_state(Form.images)


@dp2.message(Form.main_page)
async def main_page(message: types.Message, state: FSMContext):
    global genders
    text = message.text
    if text == 'Киім қосу':
        await bot2.send_message(chat_id=message.from_user.id, text ="Кімге киім қосасыз?", reply_markup=gender_markup)
        await state.set_state(Form.gender_id)
    elif text == 'Менің киімдерім':
        seller_username = message.from_user.username
        categories_list[seller_username] = await sync_to_async(lambda: list(Product.objects.filter(seller_username = seller_username).values_list('cat_id', flat=True).distinct()))()
        gender_list = set()
        for category in categories_list[seller_username]:
            gender = await sync_to_async(Category.objects.filter(cat_id = category).first)()
            gender_list.add(gender.gender_id)
        markup = [[KeyboardButton(text = genders[gen])] for gen in list(gender_list)]
        markup.append([KeyboardButton(text = 'АРТҚА')])
        await message.reply(text='Кімге киім қарайсыз?', reply_markup=ReplyKeyboardMarkup(keyboard=markup))
        await state.set_state(Form.ask_position)

@dp2.message(Form.ask_position)
async def ask_position(message: types.Message, state: FSMContext):
    global categories_list
    text = message.text
    if text in genders:
        gender_id = gender_ids[text]
        seller_username = message.from_user.username
        position_list = set()
        for category in categories_list[seller_username]:
            position = await sync_to_async(Category.objects.filter(cat_id = category, gender_id = gender_id).first)()
            if position:
                position_list.add(position.position_id)
        markup = [[KeyboardButton(text = positions[position])] for position in list(position_list)] + [go_back_button]

        await message.reply(text = 'Киімнің категориясы?', reply_markup=ReplyKeyboardMarkup(keyboard = markup))
        await state.update_data(gender_id = gender_ids[text])
        await state.set_state(Form.ask_product)
    elif text == 'АРТҚА':
        await message.reply(text ='Сіз басты беттесіз', reply_markup=main_markup)
        await state.set_state(Form.main_page)

@dp2.message(Form.ask_product)
async def ask_product(message: types.Message, state: FSMContext):
    text = message.text
    if text in positions:
        seller_username = message.from_user.username
        data = await state.get_data()
        gender_id = data.get('gender_id')
        clothes = set()
        for category in categories_list[seller_username]:
            product = await sync_to_async(Category.objects.filter(cat_id = category, gender_id = gender_id, position_id = position_ids[text]).first)()
            if product:
                clothes.add(product.cat_name)
        markup = [[KeyboardButton(text=category)] for category in clothes] + [go_back_button]
        await message.reply(text = 'Қандай киім қарайсыз?', reply_markup = ReplyKeyboardMarkup(keyboard=markup))
        await state.update_data(position_id = position_ids[text])
        await state.set_state(Form.show_products)
    elif text == 'АРТҚА':
        seller_username = message.from_user.username
        gender_list = set()
        for category in categories_list[seller_username]:
            gender = await sync_to_async(Category.objects.filter(cat_id = category).first)()
            gender_list.add(gender.gender_id)
        markup = [[KeyboardButton(text = genders[gen])] for gen in list(gender_list)]
        markup.append([KeyboardButton(text = 'АРТҚА')])
        await message.reply(text='Кімге киім қарайсыз?', reply_markup=ReplyKeyboardMarkup(keyboard=markup))
        await state.set_state(Form.ask_position)        

@dp2.message(Form.show_products)
async def show_products(message: types.Message, state: FSMContext):
    global global_products
    seller_username = message.from_user.username
    data = await state.get_data()
    gender_id = data.get('gender_id')
    position_id = data.get('position_id')
    text = message.text
    categories = [category.cat_name for category in await sync_to_async(list)(Category.objects.filter(gender_id = gender_id, position_id = position_id))]
    if text in categories:
        cat_object = await sync_to_async(Category.objects.filter(cat_name = text, gender_id = gender_id, position_id = position_id).first)()
        cat_id = cat_object.cat_id
        global_products[seller_username] = await sync_to_async(list)(Product.objects.filter(seller_username = seller_username, cat_id = cat_id))
        
        await state.update_data(index = 0)
        await state.set_state(Form.index)
        

        product = global_products[seller_username][0]
        media = MediaGroupBuilder()
        images = [entry.name for entry in os.scandir(product.image_path) if entry.is_file()]
        for image in images:
            media.add_photo(media=FSInputFile(product.image_path + '/' + image), type = "photo")
        await bot2.send_media_group(chat_id=message.chat.id, media=media.build()) 
        message = await bot2.send_message(chat_id=message.chat.id, text = product.description + '\n \n' + f'Қаралым саны: {product.views}', reply_markup=ReplyKeyboardMarkup(keyboard=[ [KeyboardButton(text = 'Келесі')], [KeyboardButton(text = 'Өшіру')], [KeyboardButton(text = 'АРТҚА')]]))
        await state.update_data(delete_message_id = message.message_id)
    elif message.text == 'АРТҚА':
        data = await state.get_data()
        gender_id = data.get('gender_id')
        seller_username = message.from_user.username
        position_list = set()
        for category in categories_list[seller_username]:
            position = await sync_to_async(Category.objects.filter(cat_id = category, gender_id = gender_id).first)()
            if position:
                position_list.add(position.position_id)
        markup = [[KeyboardButton(text = positions[position])] for position in list(position_list)] + [go_back_button]

        await message.reply(text = 'Киімнің категориясы?', reply_markup=ReplyKeyboardMarkup(keyboard = markup))
        await state.update_data(gender_id = gender_id)
        await state.set_state(Form.ask_product)

@dp2.message(Form.index)
async def skip(message: types.Message, state: FSMContext):
    seller_username = message.from_user.username
    data = await state.get_data()
    cat_id = data.get('cat_id')
    index = data.get('index')
    user_id = message.chat.id

    if message.text == 'Келесі':
        if index + 1 < len(global_products[seller_username]):
            product = global_products[seller_username][index + 1]
            media = MediaGroupBuilder()
            images = [entry.name for entry in os.scandir(product.image_path) if entry.is_file()]
            for image in images:
                media.add_photo(media=FSInputFile(product.image_path + '/' + image), type = "photo") 
            await bot2.send_media_group(chat_id=message.chat.id, media=media.build())
            message = await bot2.send_message(chat_id=message.chat.id, text = product.description + '\n \n' + f'Қаралым саны: {product.views}', reply_markup=ReplyKeyboardMarkup(keyboard=[ [KeyboardButton(text = 'Келесі')], [KeyboardButton(text = 'Өшіру')], [KeyboardButton(text = 'АРТҚА')]]))
            await state.update_data(index = index + 1)
            await state.update_data(delete_message_id = message.message_id)
        else:
            await bot2.send_message(chat_id = user_id, text = 'Бұл соңғы киім болған, басқа киім таңдаңыз', reply_markup=ReplyKeyboardMarkup(keyboard=[go_back_button]))
    elif message.text == 'АРТҚА':
        seller_username = message.from_user.username
        data = await state.get_data()
        gender_id = data.get('gender_id')
        position_id = data.get('position_id')
        clothes = set()
        for category in categories_list[seller_username]:
            product = await sync_to_async(Category.objects.filter(cat_id = category, gender_id = gender_id, position_id = position_id).first)()
            if product:
                clothes.add(product.cat_name)
        markup = [[KeyboardButton(text=category)] for category in clothes] + [go_back_button]
        await message.reply(text = 'Қандай киім қарайсыз?', reply_markup = ReplyKeyboardMarkup(keyboard=markup))
        await state.update_data(position_id = position_id)
        await state.set_state(Form.show_products)
    elif message.text == 'Өшіру':
        data = await state.get_data()
        message_id = data.get('delete_message_id')
        await bot2.send_message(chat_id=message.chat.id, text = 'Сіз шынымен де осы киімді өшіруді қалайсызба?', reply_to_message_id=message_id, reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text ='Жоқ')], [KeyboardButton(text ='Ия')]]))
        await state.set_state(Form.delete_message)

@dp2.message(Form.delete_message)
async def delete_message(message: types.Message, state: FSMContext):
    seller_username = message.from_user.username
    text = message.text
    data = await state.get_data()
    index = data.get('index')
    if text == 'Ия':
        product = global_products[seller_username][index]
        shutil.rmtree(product.image_path)
        await sync_to_async(product.delete)()
        await message.reply(text = 'Сәтті өшірілді')

        if index + 1 < len(global_products[seller_username]):
            product = global_products[seller_username][index + 1]
            media = MediaGroupBuilder()
            images = [entry.name for entry in os.scandir(product.image_path) if entry.is_file()]
            for image in images:
                media.add_photo(media=FSInputFile(product.image_path + '/' + image), type = "photo") 
            await bot2.send_media_group(chat_id=message.chat.id, media=media.build())
            message = await bot2.send_message(chat_id=message.chat.id, text = product.description + '\n \n' + f'Қаралым саны: {product.views}', reply_markup=ReplyKeyboardMarkup(keyboard=[ [KeyboardButton(text = 'Келесі')], [KeyboardButton(text = 'Өшіру')], [KeyboardButton(text = 'АРТҚА')]]))
            await state.update_data(index = index + 1)
            await state.update_data(delete_message_id = message.message_id)
        else:
            await bot2.send_message(chat_id = message.chat.id, text = 'Бұл соңғы киім болған, басқа киім таңдаңыз', reply_markup=ReplyKeyboardMarkup(keyboard=[go_back_button]))

    elif text == 'Жоқ':
        if index + 1 < len(global_products[seller_username]):
            product = global_products[seller_username][index + 1]
            media = MediaGroupBuilder()
            images = [entry.name for entry in os.scandir(product.image_path) if entry.is_file()]
            for image in images:
                media.add_photo(media=FSInputFile(product.image_path + '/' + image), type = "photo") 
            await bot2.send_media_group(chat_id=message.chat.id, media=media.build())
            message = await bot2.send_message(chat_id=message.chat.id, text = product.description + '\n \n' + f'Қаралым саны: {product.views}', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Келесі')], [KeyboardButton(text = 'Өшіру')], [KeyboardButton(text = 'АРТҚА')]]))
            await state.update_data(index = index + 1)
            await state.update_data(delete_message_id = message.message_id)
        else:
            await bot2.send_message(chat_id = message.chat.id, text = 'Бұл соңғы киім болған, басқа киім таңдаңыз', reply_markup=ReplyKeyboardMarkup(keyboard=[go_back_button]))
    await state.set_state(Form.index)


async def main():
    # Run both bots' polling concurrently using separate tasks
    await dp2.start_polling(bot2)

if __name__ == '__main__':
    asyncio.run(main())