import asyncio
from aiogram.exceptions import TelegramBadRequest
from Users.usersCheker import get_all_users
from config import ADMIN_TG_ID

class BroadcastStatus:
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0

async def send_broadcast_message(bot, message, user_id):
    try:
        # Пытаемся отправить копию оригинального сообщения
        if message.text:
            await bot.send_message(user_id, message.text, parse_mode="HTML")
        elif message.photo:
            await bot.send_photo(
                user_id,
                message.photo[-1].file_id,
                caption=message.caption,
                parse_mode="HTML"
            )
        elif message.document:
            await bot.send_document(
                user_id,
                message.document.file_id,
                caption=message.caption,
                parse_mode="HTML"
            )
        return True
    except TelegramBadRequest as e:
        if "bot was blocked" in str(e).lower():
            return False
    except Exception as e:
        print(f"Error sending to {user_id}: {e}")
        return False

async def broadcast_message(bot, message):
    """Рассылает сообщение всем пользователям"""
    if str(message.from_user.id) != ADMIN_TG_ID:
        await message.answer("❌ Доступ запрещён")
        return

    users = get_all_users()
    if not users:
        await message.answer("❌ Нет пользователей для рассылки")
        return

    status = BroadcastStatus()
    status.total = len(users)

    # Отправляем подтверждение
    confirm_msg = await message.answer(
        f"⏳ Начинаю рассылку для {status.total} пользователей...\n"
        f"✅ Успешно: {status.success}\n"
        f"❌ Ошибки: {status.failed}"
    )

    # Рассылаем сообщения
    for user_id in users:
        success = await send_broadcast_message(bot, message, user_id)
        if success:
            status.success += 1
        else:
            status.failed += 1

        # Обновляем статус каждые 10 отправок
        if status.success % 10 == 0 or status.failed % 10 == 0:
            try:
                await confirm_msg.edit_text(
                    f"⏳ Рассылка для {status.total} пользователей...\n"
                    f"✅ Успешно: {status.success}\n"
                    f"❌ Ошибки: {status.failed}"
                )
            except:
                pass

        # Небольшая задержка, чтобы не получить ограничение от Telegram
        await asyncio.sleep(0.1)

    # Финальное сообщение
    await confirm_msg.edit_text(
        f"🎉 Рассылка завершена!\n"
        f"Всего: {status.total} пользователей\n"
        f"✅ Успешно: {status.success}\n"
        f"❌ Ошибки: {status.failed}"
    )