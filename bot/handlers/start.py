from aiogram import Router, F
from aiogram.filters import Command, CommandStart
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

@router.message(Command('test'))
async def cmd_test(message: Message):
    import requests
    try:
        resp = requests.post(
            'https://tgappka-pi.vercel.app/api/ping',
            json={'user_id': message.from_user.id},
            timeout=7
        )
        if resp.ok:
            await message.answer('✅ Тестовый ping отправлен!', parse_mode=None)
        else:
            await message.answer(f'❌ Ошибка API: {resp.status_code}', parse_mode=None)
    except Exception as e:
        await message.answer(f'❌ Ошибка запроса: {str(e)[:100]}', parse_mode=None)
