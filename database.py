import aiosqlite
import time

DB_PATH = "scanlog.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS scanlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            timestamp INTEGER
        )
        """)
        await db.commit()

async def add_log(username, target, port, status, service):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO scanlog (username, target, port, status, service, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (username, target, port, status, service, int(time.time()))
        )
        await db.commit()

async def get_logs(username=None):
    async with aiosqlite.connect(DB_PATH) as db:
        if username:
            cursor = await db.execute("SELECT * FROM scanlog WHERE username=? ORDER BY timestamp DESC", (username,))
        else:
            cursor = await db.execute("SELECT * FROM scanlog ORDER BY timestamp DESC")
        rows = await cursor.fetchall()
        return rows

async def delete_old_logs():
    expire = int(time.time()) - 86400  # 24 hours
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scanlog WHERE timestamp < ?", (expire,))
        await db.commit() 