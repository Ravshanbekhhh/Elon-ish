import os
import json
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(dsn=DATABASE_URL)
            await self.create_tables()

    async def create_tables(self):
        async with self.pool.acquire() as connection:
            # 1. Adminlar
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id BIGINT PRIMARY KEY
                );
            """)
            # 2. Kanallar
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_type VARCHAR(50) PRIMARY KEY,
                    channel_id BIGINT
                );
            """)
            # 3. E'lonlar
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS ads (
                    code VARCHAR(50) PRIMARY KEY,
                    data JSONB
                );
            """)
            # 4. SOZLAMALAR (Yangi: To'lov ma'lumotlari uchun)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT
                );
            """)

    async def close(self):
        if self.pool:
            await self.pool.close()

    # --- ADMINLAR ---
    async def add_admin(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO admins (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

    async def remove_admin(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM admins WHERE user_id = $1", user_id)

    async def get_admins(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id FROM admins")
            return [row['user_id'] for row in rows]

    # --- KANALLAR ---
    async def set_channel(self, channel_type: str, channel_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO channels (channel_type, channel_id) 
                VALUES ($1, $2) 
                ON CONFLICT (channel_type) 
                DO UPDATE SET channel_id = $2
            """, channel_type, channel_id)

    async def get_channels(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT channel_type, channel_id FROM channels")
            return {row['channel_type']: row['channel_id'] for row in rows}

    # --- SOZLAMALAR (PAYMENT) ---
    async def set_setting(self, key: str, value: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO settings (key, value) 
                VALUES ($1, $2) 
                ON CONFLICT (key) 
                DO UPDATE SET value = $2
            """, key, value)

    async def get_settings(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT key, value FROM settings")
            return {row['key']: row['value'] for row in rows}

    # --- E'LONLAR ---
    async def save_ad(self, code: str, data: dict):
        data_json = json.dumps(data, ensure_ascii=False)
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO ads (code, data) VALUES ($1, $2)", code, data_json)

    async def get_ad(self, code: str):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT data FROM ads WHERE code = $1", code)
            if row:
                return json.loads(row['data'])
            return None

db = Database()