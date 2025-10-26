"""
Обработчик создания розыгрыша (FSM)
"""
import re
from datetime import datetime
from typing import Dict, Any
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.utils.db import db
from bot.utils.checks import check_channel_requirements
from bot.keyboards.inline import (
    get_conditions_keyboard,
    get_retry_keyboard,
    get_more_channels_keyboard,
    get_confirm_keyboard,
    get_participate_keyboard
)

router = Router()

class CreateDrawForm(StatesGroup):
    """Состояния FSM для создания розыгрыша"""
    waiting_for_title = State()
    waiting_for_prizes = State()
    waiting_for_winners_count = State()
    waiting_for_conditions = State()
    waiting_for_channel = State()
    checking_channel = State()
    waiting_for_more_channels = State()
    waiting_for_end_date = State()
    confirming = State()

@router.callback_query(F.data == "create_draw")
async def start_create_draw(callback: CallbackQuery, state: FSMContext):
    """Начало создания розыгрыша"""
    await callback.answer()
    await state.set_state(CreateDrawForm.waiting_for_title)
    
    await callback.message.answer(
        "📝 **Шаг 1/6: Название розыгрыша**\n\n"
        "Введите название розыгрыша:",
        parse_mode="Markdown"
    )

@router.message(CreateDrawForm.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обработка названия"""
    await state.update_data(title=message.text)
    await state.set_state(CreateDrawForm.waiting_for_prizes)
    
    await message.answer(
        "🎁 **Шаг 2/6: Призы**\n\n"
        "Введите список призов (по одному на строку):\n\n"
        "Пример:\n"
        "1. iPhone 15 Pro\n"
        "2. AirPods Pro\n"
        "3. Подписка Premium",
        parse_mode="Markdown"
    )

@router.message(CreateDrawForm.waiting_for_prizes)
async def process_prizes(message: Message, state: FSMContext):
    """Обработка списка призов"""
    await state.update_data(prizes=message.text)
    await state.set_state(CreateDrawForm.waiting_for_winners_count)
    
    await message.answer(
        "🏆 **Шаг 3/6: Количество победителей**\n\n"
        "Введите количество победителей (число):",
        parse_mode="Markdown"
    )

@router.message(CreateDrawForm.waiting_for_winners_count)
async def process_winners_count(message: Message, state: FSMContext):
    """Обработка количества победителей"""
    try:
        winners_count = int(message.text)
        if winners_count < 1:
            await message.answer("❌ Количество победителей должно быть больше 0!")
            return
        
        await state.update_data(winners_count=winners_count)
        await state.set_state(CreateDrawForm.waiting_for_conditions)
        
        await message.answer(
            "✅ **Шаг 4/6: Условия участия**\n\n"
            "Выберите условия для участия:",
            reply_markup=get_conditions_keyboard(),
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число!")

@router.callback_query(F.data == "condition_subscription", CreateDrawForm.waiting_for_conditions)
async def process_conditions(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора условий"""
    await callback.answer()
    await state.update_data(channels=[])
    await state.set_state(CreateDrawForm.waiting_for_channel)
    
    await callback.message.answer(
        "📢 **Шаг 5/6: Каналы для проверки**\n\n"
        "Введите username канала (формат: @channelname или https://t.me/channelname):",
        parse_mode="Markdown"
    )

@router.message(CreateDrawForm.waiting_for_channel)
async def process_channel(message: Message, state: FSMContext, bot: Bot):
    """Обработка ввода канала"""
    channel_input = message.text.strip()
    
    # Извлечь username из различных форматов
    if channel_input.startswith("@"):
        channel_username = channel_input
    elif "t.me/" in channel_input:
        channel_username = "@" + channel_input.split("t.me/")[-1].strip("/")
    else:
        channel_username = "@" + channel_input
    
    await state.update_data(current_channel=channel_username)
    await state.set_state(CreateDrawForm.checking_channel)
    
    # Проверка канала
    checking_msg = await message.answer("⏳ Проверяю канал...")
    
    user_subscribed, bot_is_admin = await check_channel_requirements(
        bot, message.from_user.id, channel_username
    )
    
    if not user_subscribed:
        await checking_msg.edit_text(
            f"❌ Вы не подписаны на канал {channel_username}\n\n"
            "Пожалуйста, подпишитесь и попробуйте снова.",
            reply_markup=get_retry_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    if not bot_is_admin:
        await checking_msg.edit_text(
            f"❌ Бот не является администратором канала {channel_username}\n\n"
            "Пожалуйста, добавьте бота в администраторы канала с правами:\n"
            "• Просмотр списка участников\n"
            "• Публикация сообщений\n\n"
            "После этого попробуйте снова.",
            reply_markup=get_retry_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Все проверки пройдены
    data = await state.get_data()
    channels = data.get("channels", [])
    channels.append({
        "username": channel_username,
        "is_verified": True
    })
    await state.update_data(channels=channels)
    
    await checking_msg.edit_text(
        f"✅ Канал {channel_username} успешно добавлен!\n\n"
        f"Всего каналов: {len(channels)}",
        parse_mode="Markdown"
    )
    
    await state.set_state(CreateDrawForm.waiting_for_more_channels)
    await message.answer(
        "Хотите добавить еще один канал?",
        reply_markup=get_more_channels_keyboard()
    )

@router.callback_query(F.data == "retry_check", CreateDrawForm.checking_channel)
async def retry_channel_check(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Повторная проверка канала"""
    await callback.answer()
    data = await state.get_data()
    channel_username = data.get("current_channel")
    
    checking_msg = await callback.message.edit_text("⏳ Проверяю канал снова...")
    
    user_subscribed, bot_is_admin = await check_channel_requirements(
        bot, callback.from_user.id, channel_username
    )
    
    if not user_subscribed:
        await checking_msg.edit_text(
            f"❌ Вы все еще не подписаны на канал {channel_username}",
            reply_markup=get_retry_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    if not bot_is_admin:
        await checking_msg.edit_text(
            f"❌ Бот все еще не является администратором канала {channel_username}",
            reply_markup=get_retry_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Все проверки пройдены
    data = await state.get_data()
    channels = data.get("channels", [])
    channels.append({
        "username": channel_username,
        "is_verified": True
    })
    await state.update_data(channels=channels)
    
    await checking_msg.edit_text(
        f"✅ Канал {channel_username} успешно добавлен!\n\n"
        f"Всего каналов: {len(channels)}",
        parse_mode="Markdown"
    )
    
    await state.set_state(CreateDrawForm.waiting_for_more_channels)
    await callback.message.answer(
        "Хотите добавить еще один канал?",
        reply_markup=get_more_channels_keyboard()
    )

@router.callback_query(F.data == "add_channel", CreateDrawForm.waiting_for_more_channels)
async def add_another_channel(callback: CallbackQuery, state: FSMContext):
    """Добавить еще один канал"""
    await callback.answer()
    await state.set_state(CreateDrawForm.waiting_for_channel)
    
    await callback.message.answer(
        "📢 Введите username следующего канала:",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "finish_channels", CreateDrawForm.waiting_for_more_channels)
async def finish_channels(callback: CallbackQuery, state: FSMContext):
    """Завершить добавление каналов"""
    await callback.answer()
    await state.set_state(CreateDrawForm.waiting_for_end_date)
    
    await callback.message.answer(
        "📅 **Шаг 6/6: Дата окончания**\n\n"
        "Введите дату и время окончания розыгрыша\n"
        "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
        "Пример: 31.12.2025 23:59",
        parse_mode="Markdown"
    )

@router.message(CreateDrawForm.waiting_for_end_date)
async def process_end_date(message: Message, state: FSMContext):
    """Обработка даты окончания"""
    try:
        # Попытка распарсить дату
        end_date = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        
        # Проверка что дата в будущем
        if end_date <= datetime.now():
            await message.answer(
                "❌ Дата окончания должна быть в будущем!\n"
                "Попробуйте еще раз.",
                parse_mode="Markdown"
            )
            return
        
        await state.update_data(end_date=end_date)
        await state.set_state(CreateDrawForm.confirming)
        
        # Показать итоговое сообщение
        data = await state.get_data()
        preview_text = format_draw_message(data)
        
        await message.answer(
            "✅ **Предпросмотр розыгрыша:**\n\n" + preview_text,
            reply_markup=get_confirm_keyboard(),
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты!\n\n"
            "Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 31.12.2025 23:59",
            parse_mode="Markdown"
        )

def format_draw_message(data: Dict[str, Any]) -> str:
    """Форматировать сообщение о розыгрыше"""
    title = data["title"]
    prizes = data["prizes"]
    winners_count = data["winners_count"]
    channels = data["channels"]
    end_date = data["end_date"]
    
    text = f"🎉 **{title}**\n\n"
    text += f"🎁 **Призы:**\n{prizes}\n\n"
    text += f"✅ **Условия:**\n"
    
    for channel in channels:
        text += f"• Подписаться на {channel['username']}\n"
    
    text += f"\n📅 **Итоги:** {end_date.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"🏆 **Победителей:** {winners_count}"
    
    return text

@router.callback_query(F.data == "confirm_create", CreateDrawForm.confirming)
async def confirm_create(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Подтверждение создания розыгрыша"""
    await callback.answer()
    
    data = await state.get_data()
    
    # Создать розыгрыш в БД
    draw_id = await db.create_draw(
        owner_id=callback.from_user.id,
        title=data["title"],
        prizes=data["prizes"],
        winners_count=data["winners_count"],
        channels=data["channels"],
        end_date=data["end_date"]
    )
    
    # Отправить сообщение в первый канал
    first_channel = data["channels"][0]["username"]
    draw_text = format_draw_message(data) + "\n\n👇 Нажмите кнопку ниже чтобы участвовать"
    
    try:
        sent_message = await bot.send_message(
            chat_id=first_channel,
            text=draw_text,
            reply_markup=get_participate_keyboard(draw_id),
            parse_mode="Markdown"
        )
        
        await callback.message.answer(
            f"✅ **Розыгрыш успешно создан!**\n\n"
            f"ID розыгрыша: `{draw_id}`\n"
            f"Опубликовано в: {first_channel}\n\n"
            f"Розыгрыш завершится автоматически {data['end_date'].strftime('%d.%m.%Y в %H:%M')}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка при публикации в канал:\n{str(e)}\n\n"
            "Проверьте права бота в канале."
        )
    
    await state.clear()

@router.callback_query(F.data == "cancel_create", CreateDrawForm.confirming)
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    """Отмена создания розыгрыша"""
    await callback.answer()
    await state.clear()
    
    await callback.message.answer(
        "❌ Создание розыгрыша отменено.",
        parse_mode="Markdown"
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отменить текущее действие"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.")
        return
    
    await state.clear()
    await message.answer(
        "❌ Действие отменено.\n"
        "Используйте /start для начала.",
        parse_mode="Markdown"
    )
