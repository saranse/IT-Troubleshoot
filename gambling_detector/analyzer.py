import re
import logging
import asyncio
from typing import List, Tuple, Dict, Set, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """คลาสสำหรับวิเคราะห์เนื้อหาเว็บไซต์เพื่อหาคำต้องสงสัย"""
    
    def __init__(self):
        self.cache = {}  # แคชข้อมูลเว็บไซต์เพื่อหลีกเลี่ยงการดึงข้อมูลซ้ำ
        
    async def fetch_website_content(self, url: str) -> Optional[str]:
        """ดึงเนื้อหาเว็บไซต์ด้วย Playwright"""
        if url in self.cache:
            return self.cache[url]
            
        try:
            logger.info(f"Fetching content from: {url}")
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = await context.new_page()
                
                # เพิ่มเวลาหน่วง
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)  # รอให้ JavaScript โหลดเสร็จ
                
                html = await page.content()
                await browser.close()
                
                # แคชข้อมูล
                self.cache[url] = html
                return html
        except Exception as e:
            logger.error(f"Error fetching content: {e}")
            return None
    
    def extract_text_from_html(self, html: str) -> str:
        """แยกข้อความจาก HTML"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # ลบส่วนที่ไม่เกี่ยวข้อง
            for tag in soup(["script", "style", "meta", "link", "noscript", "header", "footer", "nav"]):
                tag.decompose()
                
            # แยกข้อความ
            text = soup.get_text(separator=" ", strip=True)
            
            # ทำความสะอาดข้อความ
            text = re.sub(r'\s+', ' ', text)
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def normalize_text(self, text: str) -> str:
        """ทำให้ข้อความเป็นมาตรฐานเพื่อการเปรียบเทียบ"""
        # ลบอักขระพิเศษและช่องว่าง
        text = re.sub(r'[^\w\s]', '', text)
        # แปลงเป็นตัวพิมพ์เล็ก
        text = text.lower()
        # แทนที่ช่องว่างด้วยช่องว่างเดียว
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def prepare_keyword_patterns(self, keyword: str) -> Set[str]:
        """เตรียมรูปแบบต่างๆ ของคำต้องสงสัยสำหรับการค้นหา"""
        keyword_lower = keyword.lower()
        patterns = {
            keyword_lower,  # รูปแบบปกติ
            keyword_lower.replace(' ', ''),  # ไม่มีช่องว่าง
            re.sub(r'\s+', '', keyword_lower),  # ลบช่องว่างทั้งหมด
            self.normalize_text(keyword_lower)  # รูปแบบมาตรฐาน
        }
        return patterns
        
    def find_keywords_in_text(self, text: str, keywords: List[str]) -> Dict[str, List[Tuple[str, int]]]:
        """ค้นหาคำต้องสงสัยในข้อความและระบุตำแหน่ง"""
        results = {}
        normalized_text = self.normalize_text(text)
        
        for keyword in keywords:
            keyword_patterns = self.prepare_keyword_patterns(keyword)
            matches = []
            
            for pattern in keyword_patterns:
                # หาทุกตำแหน่งที่พบคำต้องสงสัย
                for match in re.finditer(r'\b' + re.escape(pattern) + r'\b', normalized_text):
                    start_pos = match.start()
                    # ดึงข้อความรอบๆ ตำแหน่งที่พบ (context)
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(normalized_text), start_pos + len(pattern) + 50)
                    context = normalized_text[context_start:context_end]
                    matches.append((context, start_pos))
                
                # ค้นหาแบบไม่สนใจขอบเขตคำ (fallback)
                if not matches:
                    if pattern in normalized_text:
                        start_pos = normalized_text.find(pattern)
                        context_start = max(0, start_pos - 50)
                        context_end = min(len(normalized_text), start_pos + len(pattern) + 50)
                        context = normalized_text[context_start:context_end]
                        matches.append((context, start_pos))
            
            if matches:
                results[keyword] = matches
                
        return results
    
    async def analyze_url(self, url: str, keywords: List[str]) -> Dict:
        """วิเคราะห์ URL เพื่อหาคำต้องสงสัย"""
        try:
            # ตรวจสอบว่า URL ถูกต้อง
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.error(f"Invalid URL: {url}")
                return {"status": "error", "message": "Invalid URL", "url": url}
            
            # ดึงเนื้อหาเว็บไซต์
            html = await self.fetch_website_content(url)
            if not html:
                return {"status": "error", "message": "Failed to fetch content", "url": url}
            
            # แยกข้อความจาก HTML
            text = self.extract_text_from_html(html)
            if not text:
                return {"status": "error", "message": "No text content found", "url": url}
            
            # หาคำต้องสงสัยในข้อความ
            keyword_matches = self.find_keywords_in_text(text, keywords)
            
            # ถ้าพบคำต้องสงสัย
            if keyword_matches:
                return {
                    "status": "found",
                    "url": url,
                    "matches": {k: [context for context, _ in v] for k, v in keyword_matches.items()},
                    "total_matches": sum(len(v) for v in keyword_matches.values())
                }
            else:
                return {"status": "not_found", "url": url}
                
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {e}")
            return {"status": "error", "message": str(e), "url": url}
    
    async def analyze_search_results(self, results: List[Dict], keywords: List[str]) -> List[Dict]:
        """วิเคราะห์ผลการค้นหาและยืนยันการพบคำต้องสงสัย"""
        confirmed_results = []
        tasks = []
        
        # สร้าง task สำหรับแต่ละผลลัพธ์
        for result in results:
            tasks.append(self.analyze_url(result["link"], keywords))
        
        # รันทุก task พร้อมกัน
        analyses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, analysis in enumerate(analyses):
            if isinstance(analysis, Exception):
                logger.error(f"Error during analysis: {analysis}")
                continue
                
            if analysis["status"] == "found":
                # รวมข้อมูลผลการค้นหากับผลการวิเคราะห์
                confirmed_result = {**results[i], **analysis}
                confirmed_results.append(confirmed_result)
        
        return confirmed_results