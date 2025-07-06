from fastapi import FastAPI, Request, Form, Response, BackgroundTasks, Cookie
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import urllib.parse
import socket, asyncio, csv, io, time
import ipaddress
import psutil
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from database import init_db, add_log, get_logs, delete_old_logs

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Register Noto Sans Thai font for PDF export
pdfmetrics.registerFont(TTFont('NotoSansThai', 'static/NotoSansThai-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSansThai-Bold', 'static/NotoSansThai-Bold.ttf'))


RISK_PORTS = {7, 19, 20, 21, 22, 23, 25, 37, 53, 69, 79, 80, 110, 111, 135, 137, 138, 139, 445, 161, 443,
              512, 513, 514, 1433, 1434, 1723, 3389, 8080, 3306, 5432}

@app.on_event("startup")
async def startup():
    await init_db()
    asyncio.create_task(cleanup_task())

async def cleanup_task():
    while True:
        await delete_old_logs()
        await asyncio.sleep(3600)

@app.post("/api/set-username")
async def set_username(response: Response, username: str = Form(...)):
    encoded_username = urllib.parse.quote(username)
    response.set_cookie(key="username", value=encoded_username, httponly=True)
    return {"message": "Username set successfully!"}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = Cookie(None)):
    if username:
        username = urllib.parse.unquote(username)
    return templates.TemplateResponse("index.html", {"request": request, "username": username, "RISK_PORTS": list(RISK_PORTS)})

@app.post("/api/scan")
async def scan(
    request: Request,
    background_tasks: BackgroundTasks,
    target: str = Form(...),
    scan_type: str = Form(...), # Added this parameter
    custom_ports: str = Form(None), # Added this parameter (optional)
    username: str = Cookie(None)
):
    client_ip = request.client.host if request.client else "unknown"

    # Generate list of IPs to scan
    targets_to_scan = []
    try:
        if '/' in target: # Check if it's a CIDR notation (subnet)
            network = ipaddress.ip_network(target, strict=False)
            # Limit subnet size to prevent extremely long scans
            # For example, limit to /24 for now, you can adjust this.
            if network.num_addresses > 256: # Limit to /24 (256 hosts including network and broadcast)
                return JSONResponse({"error": "Subnet size is too large. Max /24 allowed for subnet scans for performance."}, status_code=400)
            for ip in network.hosts():
                targets_to_scan.append(str(ip))
        else:
            targets_to_scan.append(target)
    except ValueError:
        return JSONResponse({"error": "Invalid IP address or subnet format."}, status_code=400)

    # Generate list of ports to scan
    ports_to_scan = []
    if scan_type == "risk_ports":
        ports_to_scan = list(RISK_PORTS)
    elif scan_type == "custom_range":
        try:
            if not custom_ports:
                return JSONResponse({"error": "Custom ports must be specified for 'Custom Range' scan type."}, status_code=400)
            for part in custom_ports.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    ports_to_scan.extend(range(start, end + 1))
                else:
                    ports_to_scan.append(int(part))
            ports_to_scan = sorted(list(set(p for p in ports_to_scan if 1 <= p <= 65535)))
        except ValueError:
            return JSONResponse({"error": "Invalid custom port format. Use comma-separated numbers or ranges (e.g., 80-90,22,443)."}, status_code=400)

    if not ports_to_scan:
        return JSONResponse({"error": "No ports specified for scanning."}, status_code=400)

    all_results = []
    start_time = time.time()

    async def scan_single_target(ip_target):
        target_results = []
        scan_tasks = []

        for port in ports_to_scan:
            scan_tasks.append(scan_port_tcp(ip_target, port)) # Currently only TCP is implemented

        scanned_ports_results = await asyncio.gather(*scan_tasks)

        for i, (status, service) in enumerate(scanned_ports_results):
            port = ports_to_scan[i]
            # Ensure IP is passed to add_log
            background_tasks.add_task(add_log, username or "unknown", target, port, status, service, ip_target)
            target_results.append({
                "port": port,
                "ip_address": ip_target, # Changed from "ip" to "ip_address" for consistency with history
                "state": status,
                "service": service,
                "risk": port in RISK_PORTS
            })
        return target_results

    # Execute scans for all targets concurrently
    target_scan_tasks = [scan_single_target(ip_target) for ip_target in targets_to_scan]
    results_from_all_targets = await asyncio.gather(*target_scan_tasks)

    for res_list in results_from_all_targets:
        all_results.extend(res_list)

    elapsed = round(time.time() - start_time, 2)
    return {"results": all_results, "elapsed": elapsed}

async def scan_port_tcp(target, port):
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(0.2) # Reduced timeout for faster scans, adjust if too many false negatives
        result = conn.connect_ex((target, port))

        service = "Unknown"
        try:
            service = socket.getservbyport(port, "tcp")
        except OSError:
            pass # Service name not found

        if result == 0:
            status = "open"
        elif result == 111: # Connection refused
            status = "closed"
        else: # Other errors, often indicates firewall blocking
            status = "filtered"
        conn.close()
    except socket.gaierror:
        status = "error"
        service = "Hostname resolution failed"
    except Exception as e:
        status = "error"
        service = str(e)
    return status, service

# Currently UDP scan is not fully implemented in the frontend. 
# If you need UDP scans, you'll need to expand the frontend logic for scan_type.
async def scan_port_udp(target, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.5)

        # Sending a dummy packet, no guarantee of response for UDP
        sock.sendto(b'dummy_data', (target, port))

        # Wait for a response (might not get one even if open)
        data, addr = sock.recvfrom(1024)
        status = "open" # If we get a response, it's open
        service = "Unknown"
        try:
            service = socket.getservbyport(port, "udp")
        except OSError:
            pass

    except socket.timeout:
        # UDP timeout usually means no response, could be open or filtered
        status = "open/filtered" 
        service = "No response"
    except ConnectionRefusedError:
        status = "closed"
        service = "Connection refused"
    except Exception as e:
        status = "error"
        service = str(e)
    finally:
        if 'sock' in locals():
            sock.close()
    return status, service

@app.get("/api/history")
async def history(username: str = Cookie(None)):
    logs = await get_logs(username)
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            "id": log[0],
            "username": log[1],
            "target": log[2],
            "port": log[3],
            "status": log[4],
            "service": log[5],
            "timestamp": log[6],
            "ip_address": log[7] # Ensure ip_address is returned
        })
    return {"logs": formatted_logs}

@app.get("/api/export")
async def export_csv(username: str = Cookie(None)):
    logs = await get_logs(username)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "username", "target", "port", "status", "service", "timestamp", "ip_address"])
    for row in logs:
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scan_history.csv"}
    )

@app.get("/api/export-pdf")
async def export_pdf(username: str = Cookie(None)):
    logs = await get_logs(username)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ThaiHeading', fontName='NotoSansThai-Bold', fontSize=18, leading=22, alignment=1))
    styles.add(ParagraphStyle(name='ThaiNormal', fontName='NotoSansThai', fontSize=10, leading=12))

    elements = []

    elements.append(Paragraph(f"ประวัติการสแกนสำหรับ: {username or 'ผู้ใช้ทั้งหมด'}", styles['ThaiHeading']))
    elements.append(Paragraph("<br/>", styles['ThaiNormal']))

    data = [["ID", "ผู้ใช้", "เป้าหมายที่ระบุ", "IP ที่สแกน", "พอร์ต", "สถานะ", "บริการ", "เวลา"]] # Updated headers
    for log in logs:
        data.append([
            str(log[0]),
            log[1] or "Unknown",
            log[2], # Original target (e.g., subnet)
            log[7] if log[7] else "N/A", # Actual IP address scanned
            str(log[3]),
            log[4],
            log[5],
            datetime.fromtimestamp(log[6]).strftime('%Y-%m-%d %H:%M:%S')
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'NotoSansThai-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'NotoSansThai'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=scan_history.pdf"}
    )

@app.get("/api/performance")
async def get_performance():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_info.percent,
        "disk_percent": disk_usage.percent,
        "timestamp": int(time.time())
    }
