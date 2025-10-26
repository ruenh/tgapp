"""
Планировщик для автоматического завершения розыгрышей
"""
import random
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot

from bot.utils.db import db
from bot.config import TIMEZONE

logger = logging.getLogger(__name__)

class DrawScheduler:
    """Планировщик завершения розыгрышей"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    def start(self):
        """Запустить планировщик"""
        # Проверять каждую минуту
        self.scheduler.add_job(
            self.check_draws,
            trigger=IntervalTrigger(minutes=1),
            id="check_draws",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Планировщик запущен")
    
    def stop(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
        logger.info("Планировщик остановлен")
    
    async def check_draws(self):
        """Проверить активные розыгрыши"""
        try:
            active_draws = await db.get_active_draws()
            now = datetime.now()
            
            for draw in active_draws:
                end_date = datetime.fromisoformat(draw["end_date"])
                
                if now >= end_date:
                    logger.info(f"Завершаем розыгрыш {draw['id']}")
                    await self.complete_draw(draw)
        
        except Exception as e:
            logger.error(f"Ошибка при проверке розыгрышей: {e}")
    
    async def complete_draw(self, draw: Dict[str, Any]):
        """Завершить розыгрыш и выбрать победителей"""
        draw_id = draw["id"]
        
        try:
            # Получить всех участников
            participants = await db.get_participants(draw_id)
            
            if not participants:
                logger.warning(f"Розыгрыш {draw_id} не имеет участников")
                await db.update_draw_status(draw_id, "completed")
                
                # Отправить сообщение в канал
                first_channel = draw["channels"][0]["username"]
                await self.bot.send_message(
                    chat_id=first_channel,
                    text=f"🎉 Розыгрыш \"{draw['title']}\" завершен!\n\n"
                         f"❌ К сожалению, не было участников.",
                    parse_mode="Markdown"
                )
                return
            
            # Выбрать победителей
            winners_count = min(draw["winners_count"], len(participants))
            winners = random.sample(participants, winners_count)
            
            # Сохранить победителей в БД
            await db.add_winners(draw_id, winners)
            
            # Обновить статус розыгрыша
            await db.update_draw_status(draw_id, "completed")
            
            # Сформировать сообщение с победителями
            winners_text = self.format_winners_message(draw, winners)
            
            # Отправить в канал
            first_channel = draw["channels"][0]["username"]
            await self.bot.send_message(
                chat_id=first_channel,
                text=winners_text,
                parse_mode="Markdown"
            )
            
            logger.info(f"Розыгрыш {draw_id} успешно завершен. Победителей: {len(winners)}")
        
        except Exception as e:
            logger.error(f"Ошибка при завершении розыгрыша {draw_id}: {e}")
    
    def format_winners_message(self, draw: Dict[str, Any], winners: List[Dict[str, Any]]) -> str:
        """Форматировать сообщение с победителями"""
        text = f"🏆 **Розыгрыш \"{draw['title']}\" завершен!**\n\n"
        text += f"🎁 **Призы:**\n{draw['prizes']}\n\n"
        text += f"🎉 **Победители:**\n\n"
        
        for i, winner in enumerate(winners, 1):
            name = winner["first_name"]
            username = winner.get("username")
            
            if username:
                # Кликабельная ссылка на пользователя
                text += f"{i}. [{name}](https://t.me/{username})\n"
            else:
                # Просто имя без ссылки
                text += f"{i}. {name}\n"
        
        text += "\n🎊 Поздравляем победителей!"
        
        return text

# Глобальный экземпляр (будет инициализирован в main.py)
scheduler: DrawScheduler = None

def init_scheduler(bot: Bot):
    """Инициализировать планировщик"""
    global scheduler
    scheduler = DrawScheduler(bot)
    return scheduler
