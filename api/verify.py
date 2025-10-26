"""
Vercel Serverless Function для проверки подписок и регистрации участников
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from typing import Dict, Any
import asyncio

try:
    import aiohttp
    from supabase import create_client
except ImportError:
    pass

class handler(BaseHTTPRequestHandler):
    """Handler для Vercel serverless function"""
    
    def do_POST(self):
        """Обработка POST запроса"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            result = asyncio.run(self.process_request(data))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def do_OPTIONS(self):
        """Обработка OPTIONS запроса для CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    async def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка запроса"""
        user_id = data.get('user_id')
        first_name = data.get('first_name')
        username = data.get('username')
        draw_id = data.get('draw_id')
        
        if not all([user_id, first_name, draw_id]):
            return {'success': False, 'message': 'Недостаточно данных'}
        
        bot_token = os.getenv('BOT_TOKEN')
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not all([bot_token, supabase_url, supabase_key]):
            return {'success': False, 'message': 'Ошибка конфигурации сервера'}
        
        supabase = create_client(supabase_url, supabase_key)
        
        draw_result = supabase.table("draws").select("*").eq("id", draw_id).execute()
        
        if not draw_result.data:
            return {'success': False, 'message': 'Розыгрыш не найден'}
        
        draw = draw_result.data[0]
        
        if draw['status'] != 'active':
            return {'success': False, 'message': 'Розыгрыш завершен'}
        
        channels = draw['channels']
        missing_channels = []
        
        async with aiohttp.ClientSession() as session:
            for channel_info in channels:
                channel_username = channel_info['username']
                is_subscribed = await self.check_subscription(
                    session, bot_token, user_id, channel_username
                )
                
                if not is_subscribed:
                    missing_channels.append(channel_username)
        
        if missing_channels:
            return {
                'success': False,
                'message': 'Вы не подписаны на все нужные каналы',
                'missing_channels': missing_channels
            }
        
        participant_result = supabase.table("participants").select("*").eq(
            "draw_id", draw_id
        ).eq("user_id", user_id).execute()
        
        if participant_result.data:
            return {
                'success': True,
                'message': 'Вы уже участвуете в розыгрыше!',
                'already_participating': True
            }
        
        try:
            supabase.table("participants").insert({
                "draw_id": draw_id,
                "user_id": user_id,
                "first_name": first_name,
                "username": username
            }).execute()
            
            return {
                'success': True,
                'message': 'Вы успешно зарегистрированы в розыгрыше!',
                'already_participating': False
            }
        except Exception as e:
            return {'success': False, 'message': f'Ошибка при регистрации: {str(e)}'}
    
    async def check_subscription(
        self,
        session: aiohttp.ClientSession,
        bot_token: str,
        user_id: int,
        channel_username: str
    ) -> bool:
        """Проверить подписку пользователя на канал"""
        url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
        params = {'chat_id': channel_username, 'user_id': user_id}
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        status = data['result']['status']
                        return status in ['creator', 'administrator', 'member']
                return False
        except Exception:
            return False
