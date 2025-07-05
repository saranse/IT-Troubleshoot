# NetGuardian Pro - เครื่องมือสแกนเครือข่ายขั้นสูง

ระบบสแกนพอร์ตความเสี่ยงพร้อมไฮไลต์และแจ้งเตือน สร้างด้วย FastAPI

## ฟีเจอร์
- ✅ สแกนพอร์ตความเสี่ยงแบบ Real-time
- 🔔 ไฮไลต์พอร์ตเสี่ยงด้วยสีแดงกระพริบ
- 📊 บันทึกประวัติการสแกนลง SQLite
- 👤 ระบบจัดการผู้ใช้ผ่าน Cookie
- 📥 Export ประวัติเป็น CSV
- 🔄 ลบ log อัตโนมัติหลัง 24 ชั่วโมง
- 🎨 UI สวยงามด้วย Material Design

## การติดตั้งบน AlmaLinux

1. ติดตั้ง Python และ pip:
```bash
sudo dnf update -y
sudo dnf install python39 python39-pip git -y
```

2. Clone repository:
```bash
git clone https://github.com/YOUR_USERNAME/netguardian-pro.git
cd netguardian-pro
```

3. สร้าง Virtual Environment:
```bash
python3.9 -m venv venv
source venv/bin/activate
```

4. ติดตั้ง Dependencies:
```bash
pip install -r requirements.txt
```

5. รันเซิร์ฟเวอร์:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## การติดตั้งเป็น Service

1. สร้างไฟล์ service:
```bash
sudo nano /etc/systemd/system/netguardian.service
```

ใส่เนื้อหาต่อไปนี้:
```ini
[Unit]
Description=NetGuardian Pro Port Scanner
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/path/to/netguardian-pro
Environment="PATH=/path/to/netguardian-pro/venv/bin"
ExecStart=/path/to/netguardian-pro/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

2. เริ่มใช้งาน Service:
```bash
sudo systemctl daemon-reload
sudo systemctl start netguardian
sudo systemctl enable netguardian
```

3. ตรวจสอบสถานะ:
```bash
sudo systemctl status netguardian
```

## การใช้งาน Firewall

เปิดพอร์ต 8000 สำหรับ FastAPI:
```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## วิธีใช้งาน

1. เปิดเว็บบราวเซอร์ไปที่ `http://YOUR_SERVER_IP:8000`
2. กรอกชื่อผู้ใช้เมื่อเข้าใช้งานครั้งแรก
3. ใส่ IP หรือ Domain ที่ต้องการสแกน
4. กดปุ่ม "เริ่มสแกน"
5. ดูผลการสแกนและประวัติย้อนหลังได้ที่แท็บ "ประวัติการสแกน"

## พอร์ตความเสี่ยงที่ตรวจสอบ

- SSH (22)
- FTP (20, 21)
- Telnet (23)
- SMTP (25)
- DNS (53)
- HTTP/HTTPS (80, 443)
- NetBIOS (137, 138, 139)
- SMB (445)
- MSSQL (1433, 1434)
- MySQL (3306)
- PostgreSQL (5432)
- RDP (3389)
- และอื่นๆ

## การอัพเดท

```bash
cd /path/to/netguardian-pro
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart netguardian
```

## ความปลอดภัย

⚠️ **คำเตือน**: ใช้เครื่องมือนี้กับระบบที่คุณได้รับอนุญาตเท่านั้น การสแกนพอร์ตโดยไม่ได้รับอนุญาตอาจผิดกฎหมาย 