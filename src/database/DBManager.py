import aiosqlite
import discord


class DBManager():
    def __init__(self, db_path: str):
        self.db = None
        self.db_path = db_path
    
    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS members (
                name TEXT PRIMARY KEY, 
                discord_handle_raw TEXT,
                discord_id INTEGER,
                grad_year INTEGER,
                school TEXT,
                college TEXT
            )
        """)
        await self.db.commit()

    async def add_member(self, name : str, discord_handle_raw : str, discord_id: int, grad_year: int, school: str, college: str):
        await self.db.execute("""
            INSERT OR REPLACE INTO members (name, discord_handle_raw, discord_id, grad_year, school, college)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, discord_handle_raw, discord_id, grad_year, school, college))
        await self.db.commit()

    async def get_member(self, discord_id: int):
        cursor = await self.db.execute("""
            SELECT grad_year, school, college FROM members WHERE discord_id = ?
        """, (discord_id,))
        row = await cursor.fetchall()
        print(row)
        return row

    async def get_member(self, name : str):
        cursor = await self.db.execute("""
            SELECT discord_id, grad_year, school, college FROM members WHERE name = ?
        """, (name,))
        row = await cursor.fetchall()
        print(row)
        return row

    async def check_member_exists(self, discord_id: int) -> bool:
        #TODO When user joins, only information we know is their discord ID
        cursor = await self.db.execute("""
            SELECT 1 FROM members WHERE discord_id = ?
        """, (discord_id,))
        row = await cursor.fetchone()
        return row is not None
    

