import re
import logging
import asyncio
import aiohttp
from typing import List, Tuple, Dict, Set, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """คลาสสำหรับวิเคราะห์เนื้อหาเว็บไซต์เพื่อหาคำต้องสงสัย"""
    
    def __init__(self, max_concurrent=5):
        self.cache = {}  # แคชข้อมูลเว็บไซต์เพื่อหลีกเลี่ยงการดึงข้อมูลซ้ำ
        self.semaphore = asyncio.Semaphore(max_concurrent)  # จำกัดจำนวนการเชื่อมต่อพร้อมกัน
        
    async def fetch_website_content(self, url: str) -> Optional[str]:
        """ดึงเนื้อหาเว็บไซต์ด้วย Playwright"""
        if url in self.cache:
            return self.cache[url]
            
        try:
            async with self.semaphore:  # ใช้ semaphore เพื่อจำกัดการเชื่อมต่อพร้อมกัน
                logger.info(f"Fetching content from: {url}")
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    )
                    page = await context.new_page()
                    
                    # ตั้งค่า timeout ที่เหมาะสม
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        # รอให้ JavaScript ทำงาน
                        await page.wait_for_timeout(3000)
                    except Exception as e:
                        logger.warning(f"Timeout error, trying again with 'domcontentloaded': {e}")
                        # ถ้าเกิด timeout ให้ลองอีกครั้งด้วย domcontentloaded
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        await page.wait_for_timeout(2000)
                    
                    # บันทึกหน้าเว็บเพื่อการดีบัก (เฉพาะเมื่อมีปัญหา)
                    # html_debug = await page.content()
                    # with open(f"debug_content_{url.replace('://', '_').replace('/', '_')}.html", "w", encoding="utf-8") as f:
                    #     f.write(html_debug)
                    
                    # ดึงเนื้อหา
                    html = await page.content()
                    await browser.close()
                    
                    # ถ้าได้เนื้อหาแล้วให้แคช
                    if html:
                        self.cache[url] = html
                        return html
                    return None
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None
    
    def extract_text_from_html(self, html: str) -> str:
        """แยกข้อความจาก HTML"""
        if not html:
            return ""
            
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # ลบส่วนที่ไม่เกี่ยวข้อง
            for tag in soup(["script", "style", "meta", "link", "noscript", "header", "footer", "nav"]):
                tag.decompose()
                
            # แยกข้อความ
            text = soup.get_text(separator=" ", strip=True)
            
            # ทำความสะอาดข้อความ
            text = re.sub(r'\s+', ' ', text)
            
            # บันทึกข้อความที่แยกได้เพื่อการดีบัก (เฉพาะเมื่อมีปัญหา)
            # with open(f"debug_text_{hash(html)}.txt", "w", encoding="utf-8") as f:
            #     f.write(text)
                
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
        
        # เพิ่มแพทเทิร์นที่ไม่มีเครื่องหมายวรรคตอน
        no_punct = re.sub(r'[^\w\s]', '', keyword_lower)
        if no_punct:
            patterns.add(no_punct)
        
        # เพิ่มแพทเทิร์นที่ไม่มีช่องว่างและเครื่องหมายวรรคตอน
        no_space_no_punct = re.sub(r'[^\w]', '', keyword_lower)
        if no_space_no_punct:
            patterns.add(no_space_no_punct)
            
        return patterns
        
    def find_keywords_in_text(self, text: str, keywords: List[str]) -> Dict[str, List[Tuple[str, int]]]:
        """ค้นหาคำต้องสงสัยในข้อความและระบุตำแหน่ง"""
        if not text:
            return {}
            
        results = {}
        normalized_text = self.normalize_text(text)
        
        # บันทึกข้อความที่ทำเป็นมาตรฐานเพื่อการดีบัก (เฉพาะเมื่อมีปัญหา)
        # with open(f"debug_normalized_{hash(text)}.txt", "w", encoding="utf-8") as f:
        #     f.write(normalized_text)
            
        for keyword in keywords:
            keyword_patterns = self.prepare_keyword_patterns(keyword)
            matches = []
            
            for pattern in keyword_patterns:
                if not pattern:  # ตรวจสอบว่าแพทเทิร์นว่างหรือไม่
                    continue
                    
                # หาทุกตำแหน่งที่พบคำต้องสงสัย
                try:
                    # ค้นหาแบบไม่สนใจขอบเขตคำ (สำหรับภาษาไทยและเอเชีย)
                    if pattern in normalized_text:
                        # ค้นหาทุกตำแหน่ง
                        start_pos = 0
                        while True:
                            start_pos = normalized_text.find(pattern, start_pos)
                            if start_pos == -1:
                                break
                                
                            context_start = max(0, start_pos - 30)
                            context_end = min(len(normalized_text), start_pos + len(pattern) + 30)
                            context = normalized_text[context_start:context_end]
                            matches.append((context, start_pos))
                            
                            # เลื่อนไปยังตำแหน่งถัดไป
                            start_pos += 1
                    
                    # หากเป็นตัวอักษรละติน ให้ค้นหาแบบขอบเขตคำด้วย
                    if any(c.isascii() for c in pattern):
                        for match in re.finditer(r'\b' + re.escape(pattern) + r'\b', normalized_text):
                            start_pos = match.start()
                            context_start = max(0, start_pos - 30)
                            context_end = min(len(normalized_text), start_pos + len(pattern) + 30)
                            context = normalized_text[context_start:context_end]
                            matches.append((context, start_pos))
                            
                except Exception as e:
                    logger.error(f"Error in regex matching for pattern '{pattern}': {e}")
                    
                # เพิ่มการค้นหาในข้อความดิบด้วย (ไม่ต้องทำเป็นมาตรฐาน)
                if not matches and pattern in text.lower():
                    start_pos = text.lower().find(pattern)
                    context_start = max(0, start_pos - 30)
                    context_end = min(len(text), start_pos + len(pattern) + 30)
                    context = text[context_start:context_end]
                    matches.append((context, start_pos))
            
            if matches:
                # เพิ่ม logging สำหรับการดีบัก
                logger.info(f"Found keyword '{keyword}' with {len(matches)} matches")
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
                # ไม่พบคำต้องสงสัยในข้อความที่แยกมา ให้ลองค้นหาใน HTML อีกครั้ง
                logger.info(f"No matches in extracted text, trying direct HTML search for {url}")
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in html.lower():
                        # หากพบคำในเนื้อหา HTML โดยตรง
                        return {
                            "status": "found",
                            "url": url,
                            "matches": {keyword: [f"...found in HTML content but not in extracted text..."]},
                            "total_matches": 1
                        }
                
                return {"status": "not_found", "url": url}
                
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {e}")
            return {"status": "error", "message": str(e), "url": url}
    
    async def analyze_search_results(self, results: List[Dict], keywords: List[str]) -> List[Dict]:
        """วิเคราะห์ผลการค้นหาและยืนยันการพบคำต้องสงสัย"""
        if not results:
            return []
            
        confirmed_results = []
        tasks = []
        
        # สร้างและรันงานทั้งหมดพร้อมกัน แต่มีการควบคุมด้วย semaphore
        tasks = [self.analyze_url(result["link"], keywords) for result in results]
        
        # รันทุก task พร้อมกัน แต่จำกัดจำนวนด้วย semaphore
        analyses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, analysis in enumerate(analyses):
            if isinstance(analysis, Exception):
                logger.error(f"Error during analysis: {analysis}")
                continue
                
            if analysis["status"] == "found":
                # รวมข้อมูลผลการค้นหากับผลการวิเคราะห์
                confirmed_result = {**results[i], **analysis}
                confirmed_results.append(confirmed_result)
                
                # เพิ่ม logging สำหรับการดีบัก
                logger.info(f"Confirmed result for URL: {results[i]['link']} with keywords: {list(analysis['matches'].keys())}")
        
        # ถ้าไม่พบผลลัพธ์ที่ยืนยันแล้ว แต่มีผลการค้นหา ให้ลองใช้ snippet เป็นตัวยืนยัน
        if not confirmed_results and results:
            logger.info("No confirmed results with content analysis, trying snippet confirmation")
            for result in results:
                snippet = result.get("snippet", "").lower()
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    keyword_patterns = self.prepare_keyword_patterns(keyword)
                    
                    for pattern in keyword_patterns:
                        if pattern and pattern in snippet:
                            logger.info(f"Found keyword '{keyword}' in snippet: {snippet}")
                            confirmed_result = {
                                **result,
                                "status": "found",
                                "url": result["link"],
                                "matches": {keyword: [f"...found in search result snippet: {snippet}..."]},
                                "total_matches": 1
                            }
                            confirmed_results.append(confirmed_result)
                            break
                    
                    if confirmed_results:  # หากพบแล้ว ไม่ต้องตรวจสอบคำค้นหาอื่นอีก
                        break
        
        return confirmed_results