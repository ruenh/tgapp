from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client
from bot.config import SUPABASE_URL, SUPABASE_KEY

class Database:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def create_draw(self, owner_id: int, title: str, prizes: str, winners_count: int, channels: List[Dict[str, Any]], end_date: datetime, message_id: Optional[int] = None) -> str:
        result = self.client.table('draws').insert({'owner_id': owner_id, 'title': title, 'prizes': prizes, 'winners_count': winners_count, 'channels': channels, 'end_date': end_date.isoformat(), 'message_id': message_id, 'status': 'active'}).execute()
        return result.data[0]['id']
    
    async def get_draw(self, draw_id: str) -> Optional[Dict[str, Any]]:
        result = self.client.table('draws').select('*').eq('id', draw_id).execute()
        return result.data[0] if result.data else None
    
    async def get_active_draws(self) -> List[Dict[str, Any]]:
        result = self.client.table('draws').select('*').eq('status', 'active').execute()
        return result.data
    
    async def update_draw_status(self, draw_id: str, status: str):
        self.client.table('draws').update({'status': status}).eq('id', draw_id).execute()
    
    async def add_participant(self, draw_id: str, user_id: int, first_name: str, username: Optional[str] = None) -> bool:
        try:
            self.client.table('participants').insert({'draw_id': draw_id, 'user_id': user_id, 'first_name': first_name, 'username': username}).execute()
            return True
        except Exception as e:
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                return False
            raise
    
    async def get_participants(self, draw_id: str) -> List[Dict[str, Any]]:
        result = self.client.table('participants').select('*').eq('draw_id', draw_id).execute()
        return result.data
    
    async def add_winners(self, draw_id: str, winners: List[Dict[str, Any]]):
        winners_data = [{'draw_id': draw_id, 'user_id': w['user_id'], 'first_name': w['first_name'], 'username': w.get('username')} for w in winners]
        self.client.table('winners').insert(winners_data).execute()
    
    async def get_winners(self, draw_id: str) -> List[Dict[str, Any]]:
        result = self.client.table('winners').select('*').eq('draw_id', draw_id).execute()
        return result.data

db = Database()
