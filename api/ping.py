from http.server import BaseHTTPRequestHandler
import os
import json
import asyncio

try:
    from aiogram import Bot
except ImportError:
    Bot = None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        data = self.rfile.read(length)
        try:
            req = json.loads(data)
            user_id = req.get('user_id')
        except Exception:
            user_id = None

        bot_token = os.getenv('BOT_TOKEN')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        status = False
        if bot_token and user_id and Bot is not None:
            try:
                bot = Bot(token=bot_token)
                loop.run_until_complete(bot.send_message(chat_id=user_id, text='Тест: mini app отправила pинг!'))
                status = True
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"bot error: {str(e)}".encode())
                return
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': status}).encode())
