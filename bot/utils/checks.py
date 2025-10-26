from typing import List, Tuple
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

async def check_user_subscription(bot: Bot, user_id: int, channel_username: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except TelegramAPIError:
        return False

async def check_bot_admin(bot: Bot, channel_username: str) -> bool:
    try:
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id=channel_username, user_id=bot_info.id)
        return member.status in ['creator', 'administrator']
    except TelegramAPIError:
        return False

async def check_channel_requirements(bot: Bot, user_id: int, channel_username: str) -> Tuple[bool, bool]:
    user_subscribed = await check_user_subscription(bot, user_id, channel_username)
    bot_is_admin = await check_bot_admin(bot, channel_username)
    return user_subscribed, bot_is_admin

async def check_all_channels(bot: Bot, user_id: int, channels: List[str]) -> Tuple[bool, List[str]]:
    missing_channels = []
    for channel in channels:
        subscribed = await check_user_subscription(bot, user_id, channel)
        if not subscribed:
            missing_channels.append(channel)
    return len(missing_channels) == 0, missing_channels
