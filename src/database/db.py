import aiosqlite

async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_forms (
                msg_id INTEGER PRIMARY KEY,
                form_type TEXT NOT NULL,
                submiter TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_by TEXT,
            )
        """)
        await db.commit()

async def add_form(msg_id: int, form_type: str, submiter: str, status: str = "Pending"):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            INSERT INTO admin_forms (msg_id, form_type, submiter, status)
            VALUES (?, ?, ?, ?)
        """, (msg_id, form_type, submiter, status))
        await db.commit()