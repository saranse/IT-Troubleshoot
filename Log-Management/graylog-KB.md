
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
  # MongoDB: https://hub.docker.com/_/mongo/
  mongodb:
    image: "mongo:6.0.18"
    ports:
      - "27017:27017"
    restart: "on-failure"
    networks:
      - graylog
    volumes:
      - "mongodb_data:/data/db"
      - "mongodb_config:/data/configdb"

  opensearch:
    image: "opensearchproject/opensearch:2.15.0"
    environment:
      - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
      - "bootstrap.memory_lock=true"
      - "discovery.type=single-node"
      - "action.auto_create_index=false"
      - "plugins.security.ssl.http.enabled=false"
      - "plugins.security.disabled=true"
      # Can generate a password for `OPENSEARCH_INITIAL_ADMIN_PASSWORD` using a linux device via:
      # tr -dc A-Z-a-z-0-9_@#%^-_=+ < /dev/urandom | head -c${1:-32}
      - "OPENSEARCH_INITIAL_ADMIN_PASSWORD=+_8r#wliY3Pv5-HMIf4qzXImYzZf-M=M"
    ulimits:
      memlock:
        hard: -1
        soft: -1
      nofile:
        soft: 65536
        hard: 65536
    ports:
      - "9203:9200"
      - "9303:9300"
    restart: "on-failure"
    networks:
      - graylog
    volumes:
      - "opensearch:/usr/share/opensearch/data"

  # Graylog: https://hub.docker.com/r/graylog/graylog/
  graylog:
    hostname: "server"
    image: "graylog/graylog:6.2.2"
    # To install Graylog Open: "graylog/graylog:6.1"
    depends_on:
      mongodb:
        condition: "service_started"
      opensearch:
        condition: "service_started"
    entrypoint: "/usr/bin/tini -- wait-for-it opensearch:9200 -- /docker-entrypoint.sh"
    environment:
      GRAYLOG_NODE_ID_FILE: "/usr/share/graylog/data/config/node-id"
      GRAYLOG_HTTP_BIND_ADDRESS: "0.0.0.0:9000"
      GRAYLOG_ELASTICSEARCH_HOSTS: "http://opensearch:9200"
      GRAYLOG_MONGODB_URI: "mongodb://mongodb:27017/graylog"
      # To make reporting (headless_shell) work inside a Docker container
      GRAYLOG_REPORT_DISABLE_SANDBOX: "true"
      # CHANGE ME (must be at least 16 characters)!
      GRAYLOG_PASSWORD_SECRET: "somepasswordpepper"
      # Password: "admin"
      GRAYLOG_ROOT_PASSWORD_SHA2: "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
      GRAYLOG_HTTP_EXTERNAL_URI: "http://127.0.0.1:9000/"
    ports:
      # Graylog web interface and REST API
      - "9000:9000/tcp"
      # Beats
      - "5044:5044/tcp"
      # Syslog TCP
      - "5140:5140/tcp"
      # Syslog UDP
      - "5140:5140/udp"
      # GELF TCP
      - "12201:12201/tcp"
      # GELF UDP
      - "12201:12201/udp"
      # Forwarder data
      - "13301:13301/tcp"
      # Forwarder config
      - "13302:13302/tcp"
      # UDP-514
      - "514:514/udp"
    restart: "on-failure"
    networks:
      - graylog
    volumes:
      - "graylog_data:/usr/share/graylog/data"

networks:
  graylog:
    driver: "bridge"

volumes:
  mongodb_data:
  mongodb_config:
  opensearch:
  graylog_data:

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
