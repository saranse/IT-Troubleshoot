import aiosqlite
import time

DB_PATH = "scanlog.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # เพิ่มคอลัมน์ ip_address ถ้ายังไม่มี
        await db.execute("""
        CREATE TABLE IF NOT EXISTS scanlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            timestamp INTEGER,
            ip_address TEXT  -- เพิ่มคอลัมน์ IP สำหรับ Subnet Scan
        )
        """)
        # ตรวจสอบว่าคอลัมน์ ip_address มีอยู่แล้วหรือไม่
        cursor = await db.execute("PRAGMA table_info(scanlog)")
        columns = [column[1] for column in await cursor.fetchall()]
        if 'ip_address' not in columns:
            await db.execute("ALTER TABLE scanlog ADD COLUMN ip_address TEXT")
        await db.commit()

async def add_log(username, target, port, status, service, ip_address): # เพิ่ม ip_address
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO scanlog (username, target, port, status, service, timestamp, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, target, port, status, service, int(time.time()), ip_address)
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
    expire = int(time.time()) - 86400  # 24 ชั่วโมง
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scanlog WHERE timestamp < ?", (expire,))
        await db.commit()
