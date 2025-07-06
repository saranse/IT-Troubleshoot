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

