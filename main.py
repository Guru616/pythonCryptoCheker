import datetime
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from web3 import Web3

from config import BOT_TOKEN, NETWORKS, ADMIN_TG_ID, TOKENS, NATIVE_TOKENS
from Service.cryptoOperation import get_eth_to_usdt, get_balance, get_btc_to_usdt, get_token_balance, get_token_price
from Service.operationData import load_wallets, save_wallets
from Users.usersCheker import update_user, load_users, get_user_wallets_count
from Users.feedback import load_feedback, add_feedback
from Users.broadcast import broadcast_message

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Инициализация хранилища
user_wallets = load_wallets()

# Инициализация Web3 для каждой сети
web3_clients = {name: Web3(Web3.HTTPProvider(url)) for name, url in NETWORKS.items()}


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
        eth_price = total_balance['eth_price']
        total_eth = total_balance['total_eth']
        total_usdt = total_eth * eth_price if eth_price else 0

        # Форматируем числа с разделителями тысяч
        formatted_usdt = f"{total_usdt:,.2f}".replace(",", " ").replace(".", ",")
        formatted_eth = f"{total_eth:,.6f}".replace(",", " ").replace(".", ",")

        menu_text += f"💵 <b>Суммарный баланс:</b> ${formatted_usdt} USDT\n\n"# ({formatted_eth} ETH)\n\n"

        # Форматируем курсы
        eth_price_formatted = f"{get_eth_to_usdt():,.2f}".replace(",", " ").replace(".", ",")
        btc_price_formatted = f"{get_btc_to_usdt():,.2f}".replace(",", " ").replace(".", ",")

        menu_text += f"<i>Курс ETH: ${eth_price_formatted}\n"
        menu_text += f"Курс BTC: ${btc_price_formatted}</i>"

    menu_text += "\n\nВыберите действие:"
    menu_text += "\n\n💡 <i>Вы можете отправить отзыв/ошибку, ответом на это сообщение</i>"

    return menu_text, builder.as_markup()


async def get_single_balance(message: Message, wallet_address: str):
    if not Web3.is_address(wallet_address):
        await message.answer("❌ Неправильный формат адреса кошелька.")
        return

    # Минимальные суммы для отображения (в USD)
    MIN_NATIVE_BALANCE = 0.10  # $0.10 для нативных токенов
    MIN_TOKEN_BALANCE = 0.10  # $0.10 для ERC20 токенов

    loading_msg = await message.answer("🔄 Проверяю балансы...")
    results = []

    for name, web3 in web3_clients.items():
        network_name = name.lower()
        if web3.is_connected():
            try:
                network_results = []
                native_symbol = NATIVE_TOKENS.get(network_name, 'ETH')
                has_balances = False

                # 1. Проверяем нативный токен
                native_balance = get_balance(web3, wallet_address)
                native_price = await get_token_price(native_symbol)
                native_usd = native_balance * native_price if native_price else 0

                if native_usd >= MIN_NATIVE_BALANCE:
                    network_results.append(
                        f"▪️ <b>{native_symbol}</b>: {native_balance:.6f} (${native_usd:.2f})"
                    )
                    has_balances = True

                # 2. Проверяем ERC20 токены
                if network_name in TOKENS:
                    for token_name, token_address in TOKENS[network_name].items():
                        token_balance = await get_token_balance(web3, wallet_address, token_address)
                        token_price = await get_token_price(token_name)
                        token_usd = token_balance * token_price if token_price else 0

                        if token_usd >= MIN_TOKEN_BALANCE:
                            network_results.append(
                                f"▪️ <b>{token_name}</b>: {token_balance:.3f} (${token_usd:.2f})"
                            )
                            has_balances = True

                # 3. Добавляем результат только если есть значительные балансы
                if has_balances:
                    results.append(f"\n<b>🔹 {name.upper()}</b>:\n" + "\n".join(network_results))

            except Exception as e:
                logging.error(f"Error in {name}: {str(e)}")
                # Не показываем сети с ошибками, если нет значительных балансов

    # Формируем итоговый ответ
    if results:
        response = f"💰 <b>Балансы кошелька</b> <code>{wallet_address}</code>:\n" + "\n".join(results)
    else:
        response = "🔍 На этом кошельке не найдено значительных балансов (мин. $0.10 для отображения)"

    try:
        await loading_msg.delete()
    except:
        pass

    await message.answer(response, parse_mode="HTML")

#Админ команты
@dp.message(Command("broadcast"))
async def broadcast_command(message: Message):
    """Обработчик команды /broadcast"""
    if str(message.from_user.id) != ADMIN_TG_ID:
        await message.answer("❌ Доступ запрещён")
        return

    # Проверяем, есть ли reply
    if not message.reply_to_message:
        await message.answer(
            "ℹ️ Для рассылки сообщения ответьте (reply) на него командой /broadcast\n"
            "Поддерживаются текстовые сообщения, фото и документы"
        )
        return

    # Запускаем рассылку
    await broadcast_message(bot, message.reply_to_message)
@dp.message(Command("users"))
async def show_users(message: Message):
    if str(message.from_user.id) != ADMIN_TG_ID:
        await message.answer("Доступ запрещён")
        return

    users = load_users()
    response = "👥 <b>Список пользователей и их кошельков:</b>\n\n"

    for user_id, user_data in users.items():
        wallets_count = get_user_wallets_count(user_id, user_wallets)
        response += (
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👤 Имя: {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
            f"📛 Username: @{user_data.get('username', 'нет')}\n"
            f"📅 Первый вход: {user_data.get('first_seen', '')}\n"
            f"🔄 Последний вход: {user_data.get('last_seen', '')}\n"
            f"💰 Количество кошельков: {wallets_count}\n\n"
        )

    await message.answer(response, parse_mode="HTML")
@dp.message(Command("feedback"))
async def show_feedback(message: Message):
    if str(message.from_user.id) != ADMIN_TG_ID:
        await message.answer("❌ Доступ запрещён")
        return

    feedback_data = load_feedback()

    if not feedback_data:
        await message.answer("📭 Пожеланий от пользователей пока нет.")
        return

    response = "📝 <b>Пожелания от пользователей:</b>\n\n"

    for user_id, user_data in feedback_data.items():
        response += (
            f"👤 <b>Пользователь:</b> {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📛 @{user_data.get('username', 'нет')}\n"
            f"📩 <b>Пожелания:</b> ({len(user_data['feedback'])})\n"
        )

        for i, feedback in enumerate(user_data['feedback'], 1):
            response += (
                f"  {i}. [{feedback['timestamp']}]\n"
                f"  {feedback['message']}\n\n"
            )

        response += "\n"

    # Разбиваем на части, если сообщение слишком длинное
    if len(response) > 4000:
        parts = [response[i:i + 4000] for i in range(0, len(response), 4000)]
        for part in parts:
            await message.answer(part, parse_mode="HTML")
    else:
        await message.answer(response, parse_mode="HTML")
@dp.message(Command("diagnose"))
async def diagnose_networks(message: Message):
    # Проверяем, что это админ
    if str(message.from_user.id) != ADMIN_TG_ID:
        await message.answer("❌ Доступ запрещён")
        return

    # Создаем сообщение с прогрессом
    status_msg = await message.answer("🔄 Проверяю подключение к сетям...")

    results = []
    total_time = 0

    # Проверяем каждую сеть
    for name, web3 in web3_clients.items():
        try:
            start_time = datetime.datetime.now()

            # Проверяем подключение
            is_connected = web3.is_connected()

            # Проверяем последний блок
            latest_block = web3.eth.block_number if is_connected else None

            end_time = datetime.datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000  # в мс
            total_time += response_time

            status = "✅ Работает" if is_connected else "❌ Не отвечает"
            results.append(
                f"▪ <b>{name}</b>: {status}\n"
                f"   Последний блок: {latest_block or 'N/A'}\n"
                f"   Время ответа: {response_time:.2f} мс\n"
            )

        except Exception as e:
            results.append(f"▪ <b>{name}</b>: ❌ Ошибка проверки ({str(e)})\n")
            continue

    # Формируем итоговый отчет
    report = (
            "📊 <b>Диагностика сетей</b>\n\n"
            + "\n".join(results)
            + f"\n⏱ <b>Общее время проверки:</b> {total_time:.2f} мс"
    )

    # Обновляем первоначальное сообщение с результатами
    await status_msg.edit_text(report, parse_mode="HTML")
@dp.message(Command("help"))
async def show_help(message: Message):
    user_id = str(message.from_user.id)

    # Общие команды для всех пользователей
    help_text = "📋 <b>Список команд:</b>\n\n" \
                "/start - Начать работу с ботом\n" \
                "Отправьте адрес кошелька - добавить его в отслеживание\n" \
                "Ответьте на главное меню - отправить ошибку/отзыв/пожелания\n\n"

    # Команды только для администратора
    if user_id == ADMIN_TG_ID:
        help_text += "👑 <b>Команды администратора:</b>\n" \
                     "/users - Просмотр списка пользователей\n" \
                     "/feedback - Просмотр пожеланий пользователей\n" \
                     "/diagnose - Диагностика подключения к сетям\n" \
                     "/broadcast - Рассылка сообщения всем пользователям (reply)\n" \
                     "/help - Список всех команд"

    await message.answer(help_text, parse_mode="HTML")
# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    user_id = str(user.id)

    # Отправляем сообщение о загрузке
    loading_msg = await message.answer("🔄 Загружаю главное меню...")

    # Сохраняем информацию о пользователе
    update_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    if user_id not in user_wallets:
        user_wallets[user_id] = []
        save_wallets(user_wallets)

    menu_text, menu_markup = await get_main_menu(user_id)

    # Редактируем сообщение о загрузке вместо отправки нового
    await loading_msg.edit_text(menu_text, reply_markup=menu_markup, parse_mode="HTML")


def get_back_button():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_menu"
    ))
    return builder.as_markup()
@dp.callback_query(lambda c: c.data == "list_wallets")
async def list_wallets_handler(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    wallets = user_wallets.get(user_id, [])

    if wallets:
        response = "📋 <b>Ваши кошельки:</b>\n\n" + "\n".join(
            [f"{i + 1}. <code>{wallet}</code>" for i, wallet in enumerate(wallets)]
        )
    else:
        response = "У вас пока нет добавленных кошельков."

    await callback.message.edit_text(
        response,
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()
@dp.callback_query(lambda c: c.data == "show_info")
async def show_info(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu"),
    )

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

    # Редактируем текущее сообщение вместо создания нового
    await callback.message.edit_text(
        info_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    await callback.message.edit_text(
        text="🔄 Загружаю главное меню...",
        reply_markup=None
    )
    menu_text, menu_markup = await get_main_menu(user_id)
    await callback.message.edit_text(
        text=menu_text,
        reply_markup=menu_markup,
        parse_mode="HTML"
    )
    await callback.answer()
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
        await show_remove_menu(callback, user_id)

    await callback.answer()
@dp.callback_query(lambda c: c.data == "remove_wallet")
async def process_remove_button(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    await show_remove_menu(callback, user_id)
async def show_remove_menu(callback: CallbackQuery, user_id: str):
    wallets = user_wallets.get(user_id, [])
    if not wallets:
        await callback.answer("У вас нет кошельков для удаления.")
        return

    builder = InlineKeyboardBuilder()
    for i, wallet in enumerate(wallets, start=1):
        builder.add(InlineKeyboardButton(
            text=f"Удалить {i}. {wallet[:6]}...{wallet[-4:]}",
            callback_data=f"remove_{i - 1}"
        ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_menu"
    ))
    builder.adjust(1)

    await callback.message.edit_text(
        text="Выберите кошелек для удаления:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
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

@dp.message()
async def process_message(message: Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()
    # Проверяем, является ли сообщение ответом на главное меню
    if message.reply_to_message and "Менеджер крипто-кошельков" in message.reply_to_message.text:
        # Сохраняем пожелание
        add_feedback(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            message=text
        )

        # Отправляем временное сообщение
        temp_msg = await message.answer("✅ Спасибо за ваше пожелание! Мы обязательно его рассмотрим.")

        # Через 30 секунд меняем его
        await asyncio.sleep(30)
        try:
            await temp_msg.edit_text("Для начала работы напишите /start")
        except TelegramBadRequest:
            # Если сообщение уже было изменено или удалено
            pass
        return

    # Остальная логика обработки сообщений (кошельки и т.д.)
    if not Web3.is_address(text):
        # Отправляем первоначальное сообщение
        error_msg = await message.answer("❌ Это не похоже на адрес кошелька. Попробуйте еще раз")

        # Через 30 секунд меняем его
        await asyncio.sleep(30)
        try:
            await error_msg.edit_text("Для начала работы напишите /start")
        except TelegramBadRequest:
            # Если сообщение уже было изменено или удалено
            pass
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