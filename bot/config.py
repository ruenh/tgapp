from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен")

SUPABASE_URL = getenv("SUPABASE_URL")
SUPABASE_KEY = getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL или SUPABASE_KEY не установлены")

WEBAPP_URL = getenv("WEBAPP_URL", "https://your-project.vercel.app/webapp")
TIMEZONE = getenv("TIMEZONE", "Europe/Moscow")
DATE_FORMAT = "%d.%m.%Y %H:%M"
