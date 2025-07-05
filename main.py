from fastapi import FastAPI, Request, Form, Response, BackgroundTasks, Cookie
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import socket, asyncio, csv, io, time
from database import init_db, add_log, get_logs, delete_old_logs

app = FastAPI()
templates = Jinja2Templates(directory="templates")

RISK_PORTS = {7,19,20,21,22,23,25,37,53,69,79,80,110,111,135,137,138,139,445,161,443,
              512,513,514,1433,1434,1723,3389,8080,3306,5432}

@app.on_event("startup")
async def startup():
    await init_db()
    asyncio.create_task(cleanup_task())

async def cleanup_task():
    while True:
        await delete_old_logs()
        await asyncio.sleep(3600)  # ทำงานทุก 1 ชั่วโมง

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, username: str = Cookie(None)):
    return templates.TemplateResponse("index.html", {"request": request, "username": username})

@app.post("/api/set-username")
async def set_username(response: Response, username: str = Form(...)):
    response.set_cookie(key="username", value=username, max_age=86400)
    return {"ok": True}

@app.post("/api/scan")
async def scan(
    request: Request,
    target: str = Form(...),
    username: str = Cookie(None)
):
    # พอร์ตที่ต้องการสแกน
    ports = list(RISK_PORTS)
    results = []
    start = time.time()
    
    for port in ports:
        status, service = await scan_port(target, port)
        await add_log(username or "unknown", target, port, status, service)
        results.append({
            "port": port,
            "state": status,
            "service": service,
            "risk": port in RISK_PORTS
        })
    
    elapsed = round(time.time() - start, 2)
    return {"results": results, "elapsed": elapsed}

async def scan_port(target, port):
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(0.5)
        result = conn.connect_ex((target, port))
        service = ""
        try:
            service = socket.getservbyport(port)
        except:
            service = "-"
        if result == 0:
            status = "open"
        else:
            status = "closed"
        conn.close()
    except Exception:
        status = "filtered"
        service = "-"
    return status, service

@app.get("/api/history")
async def history(username: str = Cookie(None)):
    logs = await get_logs(username)
    return {"logs": logs}

@app.get("/api/export")
async def export(username: str = Cookie(None)):
    logs = await get_logs(username)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "username", "target", "port", "status", "service", "timestamp"])
    for row in logs:
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scan_history.csv"}
    ) 