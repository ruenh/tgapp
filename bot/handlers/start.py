from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from bot.keyboards.inline import get_create_draw_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        f'👋 Привет, {message.from_user.first_name}!\n\n'
        'Я помогу тебе провести розыгрыш в Telegram.\n\n'
        '🎯 Что я умею:\n'
        '• Создавать розыгрыши с условиями\n'
        '• Проверять подписку на каналы\n'
        '• Автоматически выбирать победителей\n'
        '• Публиковать результаты\n\n'
        'Нажми на кнопку ниже, чтобы начать! 🚀'
    )
    await message.answer(text=welcome_text, reply_markup=get_create_draw_keyboard())
