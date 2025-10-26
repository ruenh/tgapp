from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import WEBAPP_URL

def get_create_draw_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🎉 Создать розыгрыш', callback_data='create_draw')]])

def get_conditions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ По подписке', callback_data='condition_subscription')]])

def get_retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔄 Попробовать снова', callback_data='retry_check')]])

def get_more_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='➕ Добавить еще канал', callback_data='add_channel')], [InlineKeyboardButton(text='✅ Продолжить', callback_data='finish_channels')]])

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Создать розыгрыш', callback_data='confirm_create')], [InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_create')]])

def get_participate_keyboard(draw_id: str) -> InlineKeyboardMarkup:
    # Для каналов используем обычную URL кнопку вместо WebApp
    webapp_url = f'{WEBAPP_URL}/index.html?draw_id={draw_id}'
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🎁 Участвовать', url=webapp_url)]])
