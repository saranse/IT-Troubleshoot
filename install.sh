#!/bin/bash

# ตรวจสอบว่ารันด้วย root หรือไม่
if [ "$EUID" -ne 0 ]; then 
    echo "กรุณารันสคริปต์ด้วย root (sudo)"
    exit 1
fi

# รับค่า username จาก argument
if [ -z "$1" ]; then
    echo "กรุณาระบุ username"
    echo "วิธีใช้: sudo ./install.sh USERNAME"
    exit 1
fi

USERNAME=$1
INSTALL_DIR="/opt/netguardian-pro"

echo "กำลังติดตั้ง NetGuardian Pro..."

# อัพเดทระบบ
dnf update -y

# ติดตั้ง Python และ dependencies
dnf install python39 python39-pip git -y

# สร้างโฟลเดอร์ติดตั้งและคัดลอกไฟล์
mkdir -p $INSTALL_DIR
cp -r ./* $INSTALL_DIR/
chown -R $USERNAME:$USERNAME $INSTALL_DIR

# สร้าง virtual environment
cd $INSTALL_DIR
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# สร้าง systemd service
cat > /etc/systemd/system/netguardian.service << EOL
[Unit]
Description=NetGuardian Pro Port Scanner
After=network.target

[Service]
User=$USERNAME
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
EOL

# เริ่มใช้งาน service
systemctl daemon-reload
systemctl start netguardian
systemctl enable netguardian

# ตั้งค่า firewall
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload

echo "ติดตั้งเสร็จสมบูรณ์!"
echo "เปิดเว็บบราวเซอร์ไปที่ http://SERVER_IP:8000" 