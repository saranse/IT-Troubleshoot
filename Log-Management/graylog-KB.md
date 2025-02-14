
# วิธี install Graylog บน ubuntu for Docker
![image](https://github.com/user-attachments/assets/e411fb28-40f3-422a-ac02-b43b12130deb)

Graylog แนะนำ **พื้นที่เก็บข้อมูลขั้นต่ำ** ตามนี้

📌 **ขั้นต่ำ (Minimum Requirements)**

* **CPU**: 2 vCPUs
* **RAM**: 4 GB
* **Storage**: **20 GB** (ขึ้นอยู่กับปริมาณ log)

📌 **แนะนำสำหรับ Production**

* **CPU**: 4+ vCPUs
* **RAM**: 8-16 GB
* **Storage**: **200 GB+** (หรือมากกว่าตามปริมาณ log)

### **พื้นที่เก็บข้อมูล (Storage)**

* MongoDB ใช้พื้นที่เล็กน้อย (2-5GB)
* OpenSearch ใช้พื้นที่หลักในการเก็บ log
* พื้นที่ที่ต้องใช้จริงขึ้นอยู่กับจำนวน log ที่รับเข้าและระยะเวลาที่ต้องการเก็บ
  
![image](https://github.com/user-attachments/assets/63b1e2e6-bc5c-4b96-bf0b-31f3d43298d1)

ℹ️ **Graylog มีระบบหมุนเวียน log (Retention Policy)** เพื่อลบ log เก่าอัตโนมัติ ช่วยลดการใช้พื้นที่จัดเก็บ.

#### ติดตั้ง Docker และ Docker Compose

##### เปลี่ยน Time Zone ตามที่อยากจะให้เป็น เช่น ต้องการเปลี่ยนจาก `UTC` ไปเป็น `Asia/Bangkok` (ใช้ Time Zone ประเทศไทย)

```
timedatectl set-timezone Asia/Bangkok
timedatectl
```

##### 1.ติดตั้ง Docker และ Docker Compose

```
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
```

##### 2.ตรวจสอบการติดตั้ง Docker

```
docker --version
docker-compose --version
```

##### 3.สร้าง Docker Compose ไฟล์สำหรับ Graylog
3.1 สร้างไดเรกทอรีสำหรับ Graylog**

```
mkdir graylog
cd graylog
nano docker-compose.yml
```
3.2 สร้างไฟล์ `docker-compose.yml`

```
version: '3'

services:
  mongo:
    image: mongo:4.2
    networks:
      - graylog

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.10.2
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    networks:
      - graylog

  graylog:
    image: graylog/graylog:4.2
    environment:
      - GRAYLOG_PASSWORD_SECRET=verylongandsecurepassword
      - GRAYLOG_ROOT_PASSWORD_SHA2=8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918
      - GRAYLOG_HTTP_EXTERNAL_URI=http://192.168.200.253:9000/
    entrypoint: /usr/bin/tini -- wait-for-it elasticsearch:9200 -- /docker-entrypoint.sh
    depends_on:
      - mongo
      - elasticsearch
    networks:
      - graylog
    ports:
      - "9000:9000"
      - "12201:12201/udp"
      - "514:514/udp" #syslog

networks:
  graylog:
```

> **หมายเหตุ**  

GRAYLOG_ROOT_PASSWORD_SHA2 = admin เป็นรหัสผ่านที่เอาไปเข้ารหัส sha256sum

GRAYLOG_HTTP_EXTERNAL_URI=http:// ใส่ IP ของเครื่องที่ติดตั้ง :9000/



4.เริ่มต้นใช้งาน สำหรับ Graylog

```
docker-compose up -d
```

เช็คสถานะ

```
docker ps
```

รอสัก 45 วิ แล้วเข้า url ดู

เปิดเว็บเบราว์เซอร์แล้วไปที่ `http://`ใส่ IP ของเครื่องที่ติดตั้ง`:9000`

* **Username:** `admin`
* **Password:** `admin`

---

### ขั้นตอนการตรวจสอบ

##### รีสตาร์ท Docker Compose

ลองรีสตาร์ท Docker Compose อีกครั้งเพื่อให้แน่ใจว่า container ทั้งหมดเริ่มต้นใหม่อย่างถูกต้อง

```
sudo docker-compose down
sudo docker-compose up -d
```

##### ตรวจสอบว่า Port 9000 เปิดอยู่หรือไม่

```
sudo netstat -tuln | grep 9000
```

อ้างอิงการ Config
https://www.virtualizationhowto.com/2023/09/graylog-docker-compose-setup-an-open-source-syslog-server-for-home-labs/

##### ตรวจสอบว่า Graylog ได้ รับ Log แล้วหรือไม่

```
curl -X GET "http:// IP เครื่ิองที่ติดตั้ง :9000/api/search/universal/relative?query=*&range=300" -u admin:admin
```
