from http.server import BaseHTTPRequestHandler
import os
import json
import asyncio

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        data = self.rfile.read(length)
        try:
            req = json.loads(data)
            user_id = int(req.get('user_id'))
        except Exception:
            user_id = None

        bot_token = os.getenv('BOT_TOKEN')
        status = False
        try:
            if bot_token and user_id:
                import requests
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {"chat_id": user_id, "text": "Проверка связи мини-приложения и бота!"}
                resp = requests.post(url, data=payload, timeout=10)
                status = resp.ok
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"bot error: {str(e)}".encode())
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': status}).encode())
