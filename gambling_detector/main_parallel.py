import asyncio
import logging
import time
import json
import os
from datetime import datetime
from typing import List, Dict, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor

# นำเข้าโมดูลที่สร้างขึ้น
from analyzer_improved import ContentAnalyzer  # ใช้ตัววิเคราะห์ที่แก้ไขแล้ว
from search_engines_improved import search_multiple_engines  # ใช้การค้นหาที่ปรับปรุงแล้ว

# กำหนดค่า Telegram
TELEGRAM_BOT_TOKEN = "7513451139:AAH1PEHjQS4_y0N2YWCT4Lf0C9hVCybprO0"
TELEGRAM_CHAT_ID = "-1002605135756"

# กำหนดค่า Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"gambling_detector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# กำหนดค่าการทำงานแบบขนาน
MAX_CONCURRENT_DOMAINS = 2  # ลดลงจาก 3 เพื่อลดโอกาสถูกบล็อก
MAX_CONCURRENT_KEYWORDS = 1  # ลดลงจาก 2 เพื่อลดโอกาสถูกบล็อก
MAX_BROWSER_INSTANCES = 5   # ลดลงจาก 10 เพื่อประหยัดทรัพยากร

def ensure_directory(directory):
    """สร้างไดเร็กทอรีถ้ายังไม่มี"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def send_telegram_message(message: str) -> bool:
    """ส่งข้อความไปยัง Telegram"""
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        )
        if response.status_code == 200:
            logger.info("Successfully sent Telegram message")
            return True
        else:
            logger.error(f"Failed to send Telegram message: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

# ใช้ ThreadPoolExecutor เพื่อไม่ให้การส่ง Telegram รอการตอบกลับ
def send_telegram_async(message: str):
    """ส่งข้อความ Telegram แบบไม่รอการตอบกลับ"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(send_telegram_message, message)

def format_alert_message(domain: str, keyword: str, result: Dict) -> str:
    """สร้างข้อความแจ้งเตือน"""
    matches_text = ""
    for k, contexts in result.get("matches", {}).items():
        matches_text += f"\n🔍 พบคำว่า '{k}' {len(contexts)} ครั้ง\n"
        # แสดงบริบทไม่เกิน 2 รายการ (ลดลงจาก 3 เพื่อทำให้ข้อความสั้นลง)
        for i, context in enumerate(contexts[:2]):
            if i >= 2:
                matches_text += "...\n"
                break
            matches_text += f"  {i+1}. ...{context}...\n"
    
    return f"""🚨 <b>พบคำต้องสงสัย</b> 🚨
🌐 <b>โดเมน:</b> {domain}
🔑 <b>คำที่พบ:</b> {keyword}
🔗 <b>URL:</b> <a href="{result['url']}">{result.get('title', result['url'])}</a>
{matches_text}
⏰ <b>เวลาตรวจพบ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

async def process_domain_keyword_pair(domain: str, keyword: str, analyzer: ContentAnalyzer) -> List[Dict]:
    """ประมวลผลคู่โดเมนและคำค้นหา"""
    try:
        logger.info(f"Processing domain: {domain} with keyword: {keyword}")
        
        # ค้นหาด้วยเครื่องมือค้นหาหลายตัว
        search_results = await search_multiple_engines(domain, keyword)
        
        if not search_results:
            logger.info(f"No search results found for domain: {domain} with keyword: {keyword}")
            return []
        
        logger.info(f"Found {len(search_results)} preliminary results for {domain} with keyword: {keyword}")
        
        # วิเคราะห์ผลการค้นหาเพื่อยืนยันว่าพบคำต้องสงสัยจริงๆ
        confirmed_results = await analyzer.analyze_search_results(search_results, [keyword])
        
        if confirmed_results:
            logger.info(f"Confirmed {len(confirmed_results)} results with keyword '{keyword}' for domain: {domain}")
            # บันทึกผลลัพธ์
            ensure_directory("results")
            with open(f"results/{domain}_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
                json.dump(confirmed_results, f, ensure_ascii=False, indent=2)
                
            # ส่งการแจ้งเตือนสำหรับแต่ละผลลัพธ์ที่ยืนยันแล้ว
            for result in confirmed_results:
                alert_message = format_alert_message(domain, keyword, result)
                send_telegram_async(alert_message)  # ส่งแบบไม่รอการตอบกลับ
        else:
            logger.info(f"No confirmed results with keyword '{keyword}' for domain: {domain}")
        
        return confirmed_results
    except Exception as e:
        logger.error(f"Error processing {domain} with keyword {keyword}: {e}")
        return []

async def process_domain(domain: str, keywords: List[str], analyzer: ContentAnalyzer, domain_semaphore, keyword_semaphore) -> List[Dict]:
    """ประมวลผลโดเมนหนึ่งกับคำค้นหาหลายคำ"""
    async with domain_semaphore:  # จำกัดจำนวนโดเมนที่ทำงานพร้อมกัน
        all_results = []
        tasks = []
        
        # สร้าง task สำหรับแต่ละคำค้นหา
        for keyword in keywords:
            # สร้าง task ที่ทำงานพร้อมกับการจำกัดจำนวน
            task = asyncio.create_task(
                process_keyword(domain, keyword, analyzer, keyword_semaphore)
            )
            tasks.append(task)
        
        # รันทุก task และรอให้เสร็จสิ้น
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # รวมผลลัพธ์และจัดการข้อผิดพลาด
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing keyword for domain {domain}: {result}")
            elif result:
                all_results.extend(result)
        
        # ส่งสรุปสำหรับโดเมน
        if all_results:
            domain_summary = f"📊 <b>สรุปโดเมน:</b> {domain}\n🚨 พบคำต้องสงสัย {len(all_results)} รายการ"
            send_telegram_async(domain_summary)
            
        return all_results

async def process_keyword(domain: str, keyword: str, analyzer: ContentAnalyzer, keyword_semaphore) -> List[Dict]:
    """ประมวลผลคำค้นหาสำหรับโดเมนที่กำหนด พร้อมกับการควบคุมการทำงานพร้อมกัน"""
    async with keyword_semaphore:  # จำกัดจำนวนคำค้นหาที่ทำงานพร้อมกัน
        # เว้นช่วงเพื่อป้องกันการถูกบล็อก (ใช้เวลาหน่วงแบบสุ่ม)
        delay = 1 + (hash(domain + keyword) % 3)  # ใช้เวลาหน่วงแบบอิงกับโดเมนและคำค้นหา
        await asyncio.sleep(delay)
        
        return await process_domain_keyword_pair(domain, keyword, analyzer)

async def main():
    """ฟังก์ชันหลัก"""
    try:
        start_time = time.time()
        # สร้างไดเร็กทอรีสำหรับเก็บผลลัพธ์
        ensure_directory("results")
        
        # อ่านไฟล์โดเมนและคำค้นหา
        with open("domains.txt", "r", encoding="utf-8-sig") as f:
            domains = [line.strip() for line in f if line.strip()]
        
        with open("keywords1.txt", "r", encoding="utf-8-sig") as f:
            keywords = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(domains)} domains and {len(keywords)} keywords")
        
        # ส่งข้อความเริ่มต้น
        start_message = f"🔍 <b>เริ่มการตรวจสอบแบบขนาน</b>\n📊 โดเมน: {len(domains)}\n🔑 คำค้นหา: {len(keywords)}\n⏰ เริ่มเวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_telegram_message(start_message)
        
        # สร้าง semaphores สำหรับควบคุมการทำงานแบบขนาน
        domain_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOMAINS)
        keyword_semaphore = asyncio.Semaphore(MAX_CONCURRENT_KEYWORDS)
        
        # สร้างตัววิเคราะห์เนื้อหาแบบขนาน
        analyzer = ContentAnalyzer(max_concurrent=MAX_BROWSER_INSTANCES)
        
        # สร้างและรันงานสำหรับแต่ละโดเมน
        tasks = []
        for domain in domains:
            task = asyncio.create_task(
                process_domain(domain, keywords, analyzer, domain_semaphore, keyword_semaphore)
            )
            tasks.append(task)
        
        # รอให้ทุกงานเสร็จสิ้น
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # รวมผลลัพธ์และจัดการกับข้อผิดพลาด
        all_confirmed_results = []
        for domain_index, domain_result in enumerate(results):
            if isinstance(domain_result, Exception):
                logger.error(f"Error processing domain {domains[domain_index]}: {domain_result}")
            elif domain_result:
                all_confirmed_results.extend(domain_result)
        
        # ส่งสรุปการตรวจสอบ
        end_time = time.time()
        execution_time = end_time - start_time
        
        end_message = f"""🏁 <b>สรุปการตรวจสอบ</b>
📊 ตรวจสอบ: {len(domains)} โดเมน × {len(keywords)} คำค้นหา = {len(domains) * len(keywords)} คู่
🚨 พบคำต้องสงสัย: {len(all_confirmed_results)} รายการ
⏱️ เวลาที่ใช้: {execution_time:.2f} วินาที
⏰ เสร็จสิ้นเวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        send_telegram_message(end_message)
        
        logger.info(f"Scan completed in {execution_time:.2f} seconds. Found {len(all_confirmed_results)} gambling-related matches.")
        
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        send_telegram_message(f"❌ <b>เกิดข้อผิดพลาด</b>\n{str(e)}")

if __name__ == "__main__":
    asyncio.run(main())