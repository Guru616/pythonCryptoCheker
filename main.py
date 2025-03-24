import logging
import json
from cryptography.fernet import Fernet
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from web3 import Web3
import requests
from typing import Dict, List
from pybit.unified_trading import HTTP
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token="7765227646:AAH0O5V3tg_Q3NbtBBxdm5F8W9oSjqIxc9o")
dp = Dispatcher()

# Конфигурация
WALLETS_FILE = "wallets.enc"
KEY_FILE = "secret.key"


# Генерация или загрузка ключа шифрования
def get_encryption_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key


# Шифрование данных
def encrypt_data(data: dict) -> bytes:
    f = Fernet(get_encryption_key())
    return f.encrypt(json.dumps(data).encode())


# Дешифровка данных
def decrypt_data(encrypted_data: bytes) -> dict:
    f = Fernet(get_encryption_key())
    try:
        return json.loads(f.decrypt(encrypted_data).decode())
    except:
        return {}


# Загрузка кошельков из файла
def load_wallets():
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, "rb") as f:
            encrypted_data = f.read()
            return decrypt_data(encrypted_data)
    return {}


# Сохранение кошельков в файл
def save_wallets(data: dict):
    with open(WALLETS_FILE, "wb") as f:
        f.write(encrypt_data(data))


# Инициализация хранилища
user_wallets = load_wallets()

# Подключение к узлам сетей
NETWORKS = {
    "Ethereum": "https://ethereum-rpc.publicnode.com",
    "Arbitrum": "https://arb1.arbitrum.io/rpc",
    "Base": "https://mainnet.base.org",
    "Polygon": "https://polygon-rpc.com",
    "BNB": "https://bsc-pokt.nodies.app",
    "OP": "https://optimism.llamarpc.com",
    "Abstract":"https://api.mainnet.abs.xyz",
    #"Monad Testnet":"https://testnet-rpc.monad.xyz"
}

# Инициализация Web3 для каждой сети
web3_clients = {name: Web3(Web3.HTTPProvider(url)) for name, url in NETWORKS.items()}


# Функция для расчета суммарного баланса
async def calculate_total_balance(user_id: str):
    wallets = user_wallets.get(user_id, [])
    if not wallets:
        return None

    total_eth = 0.0
    eth_price = get_eth_to_usdt()

    for wallet in wallets:
        for web3 in web3_clients.values():
            if web3.is_connected():
                try:
                    balance = get_balance(web3, wallet)
                    total_eth += balance
                except Exception as e:
                    logging.error(f"Error checking balance: {e}")

    return {"total_eth": total_eth, "eth_price": eth_price}


# Главное меню
async def get_main_menu(user_id: str):
    total_balance = await calculate_total_balance(user_id)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="add_wallet"),
        InlineKeyboardButton(text="🗑️ Удалить кошелек", callback_data="remove_wallet"),
        InlineKeyboardButton(text="ℹ️ Информация", callback_data="show_info")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Список кошельков", callback_data="list_wallets")
    )

    menu_text = "💰 <b>Менеджер крипто-кошельков</b>\n\n"

    if total_balance:
        menu_text += f"💵 <b>Суммарный баланс:</b> {total_balance['total_eth']:.6f} ETH"
        if total_balance['eth_price']:
            total_usdt = total_balance['total_eth'] * total_balance['eth_price']
            menu_text += f" (${total_usdt:.2f})"
        menu_text += "\n\n"

    menu_text += "Выберите действие:"

    return menu_text, builder.as_markup()


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in user_wallets:
        user_wallets[user_id] = []
        save_wallets(user_wallets)

    menu_text, menu_markup = await get_main_menu(user_id)
    await message.answer(menu_text, reply_markup=menu_markup, parse_mode="HTML")

# Обработчик кнопки информации
@dp.callback_query(lambda c: c.data == "show_info")
async def show_info(callback: CallbackQuery):
    info_text = (
        "ℹ️ <b>Подробная информация</b>\n\n"
        "Этот бот позволяет:\n"
        "• Отслеживать баланс в различных сетях (количество сетей дорабатывается)\n"
        "• Хранить неограниченное количество кошельков\n"
        "• Конвертировать баланс в USDT\n"
        "• Автоматически обновлять данные\n\n"
        "Данные хранятся в зашифрованном виде.\n"
        "Используются только открытые данные. Бот безопасен.\n"
        "Для добавления и просмотра баланса отдельного кошелька просто отправьте его адрес."

    )
    await callback.message.answer(info_text, parse_mode="HTML")
    await callback.answer()

# Обработчики кнопок
@dp.callback_query(lambda c: c.data in ["add_wallet", "list_wallets", "remove_wallet"])
async def process_buttons(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    if callback.data == "add_wallet":
        await callback.message.answer("Введите адрес кошелька:")
    elif callback.data == "list_wallets":
        wallets = user_wallets.get(user_id, [])
        if wallets:
            response = "📋 <b>Ваши кошельки:</b>\n\n" + "\n".join(
                [f"{i + 1}. <code>{wallet}</code>" for i, wallet in enumerate(wallets)]
            )
        else:
            response = "У вас пока нет добавленных кошельков."
        await callback.message.answer(response, parse_mode="HTML")
    elif callback.data == "remove_wallet":
        await show_remove_menu(callback.message, user_id)

    await callback.answer()


# Меню удаления кошельков
async def show_remove_menu(message: Message, user_id: str):
    wallets = user_wallets.get(user_id, [])
    if not wallets:
        await message.answer("У вас нет кошельков для удаления.")
        return

    builder = InlineKeyboardBuilder()
    for i, wallet in enumerate(wallets, start=1):
        builder.add(InlineKeyboardButton(
            text=f"Удалить {i}. {wallet[:6]}...{wallet[-4:]}",
            callback_data=f"remove_{i - 1}"
        ))
    builder.adjust(1)
    await message.answer("Выберите кошелек для удаления:", reply_markup=builder.as_markup())


# Обработчик удаления кошелька
@dp.callback_query(lambda c: c.data.startswith("remove_"))
async def process_remove_wallet(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    index = int(callback.data.split("_")[1])

    try:
        removed_wallet = user_wallets[user_id].pop(index)
        save_wallets(user_wallets)
        await callback.message.answer(f"✅ Кошелек <code>{removed_wallet}</code> удален.", parse_mode="HTML")

        # Обновляем главное меню
        menu_text, menu_markup = await get_main_menu(user_id)
        await callback.message.answer(menu_text, reply_markup=menu_markup, parse_mode="HTML")
    except (IndexError, KeyError):
        await callback.message.answer("❌ Ошибка при удалении кошелька.")

    await callback.answer()


# Получение баланса для одного кошелька
async def get_single_balance(message: Message, wallet_address: str):
    if not Web3.is_address(wallet_address):
        await message.answer("❌ Неправильный формат адреса кошелька.")
        return

    eth_price = get_eth_to_usdt()
    results = []

    for name, web3 in web3_clients.items():
        if web3.is_connected():
            try:
                balance = get_balance(web3, wallet_address)
                if balance > 0:
                    if eth_price:
                        usdt_balance = balance * eth_price
                        results.append(f"▪️ <b>{name}</b>: {balance:.6f} ETH (${usdt_balance:.2f})")
                    else:
                        results.append(f"▪️ <b>{name}</b>: {balance:.6f} ETH")
            except Exception as e:
                logging.error(f"Error checking balance in {name}: {e}")

    response = f"💰 <b>Баланс кошелька</b> <code>{wallet_address}</code>:\n\n"
    if results:
        response += "\n".join(results)
    else:
        response += "На этом кошельке не найдено средств."

    if eth_price:
        response += f"\n\n📊 <i>Курс ETH: ${eth_price:.2f}</i>"

    await message.answer(response, parse_mode="HTML")


# Обработчик сообщений с адресами кошельков
@dp.message()
async def process_message(message: Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    if not Web3.is_address(text):
        await message.answer("❌ Это не похоже на адрес кошелька. Попробуйте еще раз.")
        return

    if user_id not in user_wallets:
        user_wallets[user_id] = []

    # Добавляем кошелек если его нет в списке
    if text not in user_wallets[user_id]:
        user_wallets[user_id].append(text)
        save_wallets(user_wallets)
        await message.answer(f"✅ Кошелек <code>{text}</code> добавлен.", parse_mode="HTML")
    else:
        await message.answer("Этот кошелек уже есть в вашем списке.")

    # Проверяем баланс для нового кошелька
    await get_single_balance(message, text)

    # Обновляем главное меню
    menu_text, menu_markup = await get_main_menu(user_id)
    await message.answer(menu_text, reply_markup=menu_markup, parse_mode="HTML")


# Функции для работы с блокчейном
def get_balance(web3, wallet_address):
    balance_wei = web3.eth.get_balance(wallet_address)
    balance_eth = web3.from_wei(balance_wei, "ether")
    return float(balance_eth)


# Функция для получения курса ETH/USDT через Bybit API с pybit
def get_eth_to_usdt():
    session = None
    try:
        # Инициализация клиента Bybit
        session = HTTP()

        # Получаем текущую цену ETH/USDT
        ticker = session.get_tickers(category="spot", symbol="ETHUSDT")

        if ticker['retCode'] == 0 and len(ticker['result']['list']) > 0:
            return float(ticker['result']['list'][0]['lastPrice'])
        else:
            logging.error("Не удалось получить курс ETH/USDT от Bybit")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении курса через pybit: {e}")
        return None
    finally:
        # Правильное завершение сессии
        if session:
            try:
                # Для pybit нет метода close, используем del для очистки
                del session
            except Exception as e:
                logging.error(f"Ошибка при закрытии сессии: {e}")

# Запуск бота
async def main():
    # Проверка подключения к сетям
    for name, web3 in web3_clients.items():
        if web3.is_connected():
            logging.info(f"Успешно подключено к сети {name}")
        else:
            logging.warning(f"Не удалось подключиться к сети {name}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())