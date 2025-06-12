import asyncio
import logging
import time
import json
import os
from datetime import datetime
from typing import List, Dict
import requests

# นำเข้าโมดูลที่สร้างขึ้น
from search_engines import search_multiple_engines
from analyzer import ContentAnalyzer

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

def format_alert_message(domain: str, keyword: str, result: Dict) -> str:
    """สร้างข้อความแจ้งเตือน"""
    matches_text = ""
    for k, contexts in result.get("matches", {}).items():
        matches_text += f"\n🔍 พบคำว่า '{k}' {len(contexts)} ครั้ง\n"
        # แสดงบริบทไม่เกิน 3 รายการ
        for i, context in enumerate(contexts[:3]):
            if i >= 3:
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
        else:
            logger.info(f"No confirmed results with keyword '{keyword}' for domain: {domain}")
        
        return confirmed_results
    except Exception as e:
        logger.error(f"Error processing {domain} with keyword {keyword}: {e}")
        return []

async def main():
    """ฟังก์ชันหลัก"""
    try:
        # สร้างไดเร็กทอรีสำหรับเก็บผลลัพธ์
        ensure_directory("results")
        
        # อ่านไฟล์โดเมนและคำค้นหา
        with open("domains.txt", "r", encoding="utf-8-sig") as f:
            domains = [line.strip() for line in f if line.strip()]
        
        with open("keywords1.txt", "r", encoding="utf-8-sig") as f:
            keywords = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(domains)} domains and {len(keywords)} keywords")
        
        # ส่งข้อความเริ่มต้น
        start_message = f"🔍 <b>เริ่มการตรวจสอบ</b>\n📊 โดเมน: {len(domains)}\n🔑 คำค้นหา: {len(keywords)}\n⏰ เริ่มเวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_telegram_message(start_message)
        
        # สร้างตัววิเคราะห์เนื้อหา
        analyzer = ContentAnalyzer()
        
        # ประมวลผลแต่ละคู่โดเมนและคำค้นหา
        all_confirmed_results = []
        total_pairs = len(domains) * len(keywords)
        processed = 0
        
        for domain in domains:
            domain_results = []
            for keyword in keywords:
                processed += 1
                logger.info(f"Processing pair {processed}/{total_pairs}: {domain} with keyword '{keyword}'")
                
                # เว้นช่วงเพื่อป้องกันการถูกบล็อก
                if processed > 1:
                    delay = 3 + (processed % 3)  # ใช้เวลาหน่วงไม่คงที่
                    logger.info(f"Waiting for {delay} seconds before next request...")
                    await asyncio.sleep(delay)
                
                # ประมวลผลคู่โดเมนและคำค้นหา
                confirmed_results = await process_domain_keyword_pair(domain, keyword, analyzer)
                
                # ส่งการแจ้งเตือนสำหรับแต่ละผลลัพธ์ที่ยืนยันแล้ว
                for result in confirmed_results:
                    alert_message = format_alert_message(domain, keyword, result)
                    send_telegram_message(alert_message)
                    # เว้นช่วงระหว่างการส่งข้อความ
                    await asyncio.sleep(1)
                
                domain_results.extend(confirmed_results)
            
            if domain_results:
                all_confirmed_results.extend(domain_results)
                # ส่งสรุปสำหรับแต่ละโดเมน
                domain_summary = f"📊 <b>สรุปโดเมน:</b> {domain}\n🚨 พบคำต้องสงสัย {len(domain_results)} รายการ"
                send_telegram_message(domain_summary)
        
        # ส่งสรุปการตรวจสอบ
        end_message = f"""🏁 <b>สรุปการตรวจสอบ</b>
📊 ตรวจสอบ: {len(domains)} โดเมน × {len(keywords)} คำค้นหา = {total_pairs} คู่
🚨 พบคำต้องสงสัย: {len(all_confirmed_results)} รายการ
⏰ เสร็จสิ้นเวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        send_telegram_message(end_message)
        
        logger.info(f"Scan completed. Found {len(all_confirmed_results)} gambling-related matches.")
        
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        send_telegram_message(f"❌ <b>เกิดข้อผิดพลาด</b>\n{str(e)}")

if __name__ == "__main__":
    asyncio.run(main())