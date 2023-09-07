from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.utils.markdown import *
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import pandas as pd

storage = MemoryStorage()

bot = Bot(token="5644768745:AAGOrfSr-ZI62Dylu6PXVgp4IBXBDFEf70U")
dp = Dispatcher(bot, storage=storage)

class FSMAdmin(StatesGroup):
    title = State()
    description = State()
    photo = State()

kb_main = ReplyKeyboardMarkup()
kb_main.insert(KeyboardButton("/пост")).insert(KeyboardButton("/лента")).insert(KeyboardButton("/моялента"))

async def start(message: types.Message):
    await message.answer("Привет! Это бот - соцсеть! "
                         "Нажми на /пост, чтобы добавить новый пост!"
                         "На /лента, чтобы вывести все посты"
                         "Или /моялента, чтобы посмотреть ваши посты", reply_markup=kb_main)

async def load(message: types.Message):
    await message.reply("Напишите название поста")
    await FSMAdmin.title.set()

async def load_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["title"] = message.text
    await FSMAdmin.next()
    await message.reply("Отправьте описание поста")

async def load_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["description"] = message.text
    await FSMAdmin.next()
    await message.reply("Отправьте фото для поста")

async def load_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["photo"] = message.photo[0].file_id
    await message.reply(str(data))
    save_data(message.chat.id, data)
    await state.finish()

def save_data(id, data):
    df = pd.read_csv("Posts.csv")
    data_to_file = {"data": [id, data["title"], data["description"], data["photo"]]}
    data_to_file = pd.DataFrame(data_to_file.values(), columns=df.columns)
    result = pd.concat([df, data_to_file], ignore_index=True)
    result.to_csv("Posts.csv", index=False)

async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == None:
        return
    await state.finish()
    await message.reply("Ок")

async def send_posts(id, df):
    for post in df["title"]:
        text = f"<b>{df['title'][post]}</b>\n\n" \
               f"<i>{df['description'][post]}</i>"
        await bot.send_photo(id, caption=text,
                             photo=df['photo'][post], reply_markup=kb_main, parse_mode="HTML")


async def get_posts(message: types.Message):
    df = pd.read_csv("Posts.csv").to_dict()
    await send_posts(message.chat.id, df)

async def my_posts(message: types.Message):
    df = pd.read_csv("Posts.csv")
    df = df.loc[df["id"] == message.chat.id].to_dict()
    await send_posts(message.chat.id, df)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cancel, commands="отмена", state="*")
    dp.register_message_handler(start, commands="start", state=None)
    dp.register_message_handler(load, commands="пост", state=None)
    dp.register_message_handler(load_title, state=FSMAdmin.title)
    dp.register_message_handler(load_description, state=FSMAdmin.description)
    dp.register_message_handler(load_photo, content_types=["photo"], state=FSMAdmin.photo)
    dp.register_message_handler(get_posts, commands="лента", state=None)
    dp.register_message_handler(my_posts, commands="моялента", state=None)

register_handlers(dp)

executor.start_polling(dp, skip_updates=True)
