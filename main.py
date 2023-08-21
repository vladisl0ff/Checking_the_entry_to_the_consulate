import logging
import validators
import easyocr
import io

import config as cfg
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from PIL import Image
from datetime import datetime

from database import UserDatabase

logging.basicConfig(level=logging.INFO)

bot = Bot(token=cfg.TG_API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
user_browsers = {}  # Будет хранить объект WebDriver
db = UserDatabase()

tasks = {}  # Словарь для хранения запущенных задач для каждого пользователя


class RegistrationStatesFSM(FSMContext):
    WAITING_FOR_URL = 'waiting_for_url'
    WAITING_FOR_TIME = 'waiting_for_time'


async def start_check(chat_id, user):
    user_id = chat_id
    if user_id not in tasks or tasks[user_id] is None:
        tasks[user_id] = asyncio.create_task(check_and_send_periodically(chat_id, user))
        await bot.send_message(chat_id, f"Запущена автоматическая проверка раз в {user[1]} минут.", reply_markup=get_keyboard())
    else:
        await bot.send_message(chat_id, "Автоматическая проверка уже запущена.", reply_markup=get_keyboard())


async def stop_check(chat_id):
    user_id = chat_id
    if user_id in tasks and tasks[user_id] is not None:
        tasks[user_id].cancel()
        tasks[user_id] = None
        await bot.send_message(chat_id, "Автоматическая проверка остановлена.", reply_markup=get_keyboard_set())
    else:
        await bot.send_message(chat_id, "Автоматическая проверка не была запущена.", reply_markup=get_keyboard_set())


def get_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    stop_button = KeyboardButton("Остановить автоматическую проверку")
    keyboard.add(stop_button)
    return keyboard


def get_keyboard_set():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = KeyboardButton("Запустить автоматическую проверку")
    stop_button = KeyboardButton("Остановить автоматическую проверку")
    set_button = KeyboardButton("Изменить URL и интервал проверки")
    keyboard.add(start_button, stop_button)
    keyboard.add(set_button)
    return keyboard


@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_data = db.get_user_data(message.from_user.id)
        if user_data:
            await message.reply(cfg.text['start']['old'], reply_markup=get_keyboard_set())
        else:
            await message.reply(cfg.text['start']['new'])
            await state.set_state(RegistrationStatesFSM.WAITING_FOR_URL)


@dp.message_handler(state=RegistrationStatesFSM.WAITING_FOR_URL)
async def process_url(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        url = message.text.strip()  # Убираем лишние пробелы
        if not validators.url(url):
            await message.reply("Введенный URL некорректен. Пожалуйста, введите корректный URL.")
            return
        data['url'] = url
        id_value, cd_value = extract_parameters_from_url(url)
        data['id_value'] = id_value
        data['cd_value'] = cd_value
        await message.reply(f"Вы установили URL: {url}\nТеперь введите интервал проверки в минутах.")
        await state.set_state(RegistrationStatesFSM.WAITING_FOR_TIME)


@dp.message_handler(lambda message: not message.text.isdigit(), state=RegistrationStatesFSM.WAITING_FOR_TIME)
async def process_age_invalid(message: types.Message):
    await message.reply("Интервал должен быть числом, введите интервал проверки.")


@dp.message_handler(lambda message: message.text.isdigit(), state=RegistrationStatesFSM.WAITING_FOR_TIME)
async def process_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = int(message.text)
        user_id = message.from_user.id
        try:
            db.save_user_data(user_id, data)
        except:
            db.update_user_data(user_id, data)
        await state.finish()
        await message.reply("Спасибо!\nТеперь мы можем начать проверку.", reply_markup=get_keyboard_set())


def extract_parameters_from_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    id_param = query_params.get('id')
    cd_param = query_params.get('cd')

    if id_param and cd_param:
        id_value = id_param[0]
        cd_value = cd_param[0]
        return id_value, cd_value
    else:
        return None, None


@dp.message_handler(lambda message: message.text == "Изменить URL и интервал проверки")
async def set_url_and_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user = db.get_user_data(message.from_user.id)
        await message.reply(f'Введите URL\nВаш текуший URL:\n{user[0]}')
        await state.set_state(RegistrationStatesFSM.WAITING_FOR_URL)


@dp.message_handler(lambda message: message.text == "Запустить автоматическую проверку")
async def start_check_message(message: types.Message):
    user = db.get_user_data(message.from_user.id)
    await start_check(message.chat.id, user)


@dp.message_handler(lambda message: message.text == "Остановить автоматическую проверку")
async def stop_check_message(message: types.Message):
    await message.delete()
    await stop_check(message.chat.id)


async def check_and_send_periodically(chat_id, user):
    while True:
        await check_and_send(chat_id, user[0])
        await asyncio.sleep(int(user[1])*60)


def recognize_captcha():
    reader = easyocr.Reader(['ru'])  # Указываем список поддерживаемых языков
    image = Image.open('object_screenshot.png')
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes = image_bytes.getvalue()
    results = reader.readtext(image_bytes, detail=0, allowlist='0123456789')
    return int(''.join(results))


def screenshot(browser):
    # Делаем скриншот капчи и сохраняем в файл
    object_element = browser.find_element("xpath", '//*[@id="ctl00_MainContent_imgSecNum"]')
    object_screenshot = object_element.screenshot_as_png
    with open("object_screenshot.png", "wb") as screenshot_file:
        screenshot_file.write(object_screenshot)


async def check_and_send(chat_id, url):
    global user_browsers
    if chat_id not in user_browsers or user_browsers[chat_id] is None:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Включение headless режима
        chrome_options.add_argument('--disable-gpu')  # Отключение GPU для headless режима
        user_browsers[chat_id] = webdriver.Chrome(options=chrome_options)  # Инициализация WebDriver options=chrome_options
        browser = user_browsers[chat_id]
    try:
        browser.get(url)
        await asyncio.sleep(1)
        screenshot(browser)
        verification_code = recognize_captcha()

        input_element = browser.find_element("xpath", '//*[@id="ctl00_MainContent_txtCode"]')
        input_element.send_keys(verification_code)
        await asyncio.sleep(1)
        button_element = browser.find_element("xpath", '//*[@id="ctl00_MainContent_ButtonA"]')
        button_element.click()
        await asyncio.sleep(1)
        button_element = browser.find_element("xpath", '//*[@id="ctl00_MainContent_ButtonB"]')
        button_element.click()
        await asyncio.sleep(1)
        try:
            info_text = browser.find_element("xpath", '//*[@id="center-panel"]/p[1]').text
            if info_text == 'Извините, но в настоящий момент на интересующее Вас консульское действие в системе предварительной записи нет свободного времени.':
                print(f'Нет слотов\nid: {chat_id}\nВремя: {datetime.now().strftime("%H:%M %d %B %Y")}')
        except:
            first_checkbox = browser.find_element(By.ID, "ctl00_MainContent_RadioButtonList1_0")
            first_checkbox.click()
            button_element = browser.find_element("xpath", '//*[@id="ctl00_MainContent_Button1"]')
            button_element.click()
            await asyncio.sleep(1)
            info_text = browser.find_element("xpath", '//*[@id="center-panel"]/h1').text
            if info_text == 'ПОДТВЕРЖДЕНИЕ О ЗАПИСИ НА ПРИЕМ':
                text_info = browser.find_element("xpath", '//*[@id="ctl00_MainContent_Label_Message"]').text
                await bot.send_message(chat_id, f'Поздравляю, запись прошла успешно!\n{text_info}')
        browser.quit()
        user_browsers[chat_id] = None
    except:
        browser.quit()
        user_browsers[chat_id] = None
        await check_and_send(chat_id, url)


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
