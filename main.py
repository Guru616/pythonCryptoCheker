import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from web3 import Web3
import requests
from typing import Dict, List

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token="7765227646:AAH0O5V3tg_Q3NbtBBxdm5F8W9oSjqIxc9o")
dp = Dispatcher()

# Хранение данных пользователей: {user_id: {'wallets': [address1, address2], 'selected_wallet': address}}
user_data: Dict[int, Dict] = {}

# Подключение к узлам сетей
NETWORKS = {
    "Arbitrum": "https://arb1.arbitrum.io/rpc",
    "Base": "https://mainnet.base.org",
    "Ethereum": "https://ethereum-rpc.publicnode.com",
    "Polygon": "https://polygon-rpc.com",
    "BNB": "https://bsc-pokt.nodies.app"
}

# Инициализация Web3 для каждой сети
web3_clients = {name: Web3(Web3.HTTPProvider(url)) for name, url in NETWORKS.items()}


# Главное меню
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="add_wallet"),
        InlineKeyboardButton(text="📋 Список кошельков", callback_data="list_wallets")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Суммарный баланс", callback_data="total_balance"),
        InlineKeyboardButton(text="🔍 Проверить баланс", callback_data="check_balance")
    )
    return builder.as_markup()


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'wallets': []}

    await message.answer(
        "💰 <b>Менеджер крипто-кошельков</b>\n\n"
        "Я могу проверить баланс в 5 сетях:\n"
        "- Ethereum\n- BSC\n- Polygon\n- Arbitrum\n- Base\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


# Обработчики кнопок
@dp.callback_query(lambda c: c.data in ["add_wallet", "list_wallets", "total_balance", "check_balance"])
async def process_buttons(callback: CallbackQuery):
    user_id = callback.from_user.id

    if callback.data == "add_wallet":
        await callback.message.answer("Введите адрес кошелька:")
    elif callback.data == "list_wallets":
        wallets = user_data.get(user_id, {}).get('wallets', [])
        if wallets:
            response = "📋 <b>Ваши кошельки:</b>\n\n" + "\n".join(
                [f"{i + 1}. <code>{wallet}</code>" for i, wallet in enumerate(wallets)])
        else:
            response = "У вас пока нет добавленных кошельков."
        await callback.message.answer(response, parse_mode="HTML")
    elif callback.data == "total_balance":
        await get_total_balance(callback.message, user_id)
    elif callback.data == "check_balance":
        await callback.message.answer("Введите адрес кошелька или выберите из списка:")

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


# Получение суммарного баланса
async def get_total_balance(message: Message, user_id: int):
    wallets = user_data.get(user_id, {}).get('wallets', [])
    if not wallets:
        await message.answer("У вас нет добавленных кошельков.")
        return

    eth_price = get_eth_to_usdt()
    total_balances = {network: 0.0 for network in NETWORKS}

    await message.answer("🔍 Считаю суммарный баланс... Это может занять время.")

    for wallet in wallets:
        for name, web3 in web3_clients.items():
            if web3.is_connected():
                try:
                    balance = get_balance(web3, wallet)
                    total_balances[name] += balance
                except Exception as e:
                    logging.error(f"Error checking balance for {wallet} in {name}: {e}")

    response = "📊 <b>Суммарный баланс по всем кошелькам:</b>\n\n"
    has_balance = False

    for name, balance in total_balances.items():
        if balance > 0:
            has_balance = True
            if eth_price:
                usdt_balance = balance * eth_price
                response += f"▪️ <b>{name}</b>: {balance:.6f} ETH (${usdt_balance:.2f})\n"
            else:
                response += f"▪️ <b>{name}</b>: {balance:.6f} ETH\n"

    if not has_balance:
        response += "На всех кошельках нулевой баланс."
    elif eth_price:
        response += f"\n📊 <i>Курс ETH: ${eth_price:.2f}</i>"

    await message.answer(response, parse_mode="HTML")


# Обработчик сообщений с адресами кошельков
@dp.message()
async def process_message(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if not Web3.is_address(text):
        await message.answer("❌ Это не похоже на адрес кошелька. Попробуйте еще раз.")
        return

    if user_id not in user_data:
        user_data[user_id] = {'wallets': []}

    # Добавляем кошелек если его нет в списке
    if text not in user_data[user_id]['wallets']:
        user_data[user_id]['wallets'].append(text)
        await message.answer(f"✅ Кошелек <code>{text}</code> добавлен.", parse_mode="HTML")
    else:
        await message.answer("Этот кошелек уже есть в вашем списке.")

    # Проверяем баланс для нового кошелька
    await get_single_balance(message, text)
    await message.answer("Выберите действие:", reply_markup=get_main_menu())


# Функции для работы с блокчейном (остаются без изменений)
def get_balance(web3, wallet_address):
    balance_wei = web3.eth.get_balance(wallet_address)
    balance_eth = web3.from_wei(balance_wei, "ether")
    return float(balance_eth)


def get_eth_to_usdt():
    try:
        url = "https://api.bybit.com/v2/public/tickers"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        for ticker in data['result']:
            if ticker['symbol'] == "ETHUSDT":
                return float(ticker['last_price'])
        return None
    except Exception as e:
        logging.error(f"Ошибка при получении курса: {e}")
        return None


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