import asyncio
import aiohttp
import re
import urllib.parse
import logging
import random
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# คำที่ใช้ในการหลีกเลี่ยงการถูกตรวจจับว่าเป็นบอท
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
]

# ใช้ semaphore เพื่อจำกัดจำนวนการเชื่อมต่อพร้อมกัน
browser_semaphore = asyncio.Semaphore(5)  # จำกัดจำนวน browser instances

class SearchEngine:
    """คลาสพื้นฐานสำหรับเครื่องมือค้นหา"""
    
    def __init__(self, timeout: int = 25000):  # เพิ่มเวลา timeout ให้เหมาะสม
        self.timeout = timeout
        self.cache = {}  # แคชผลการค้นหาเพื่อหลีกเลี่ยงการค้นหาซ้ำ
        
    async def fetch_with_playwright(self, url: str) -> str:
        """ใช้ Playwright เพื่อดึงข้อมูลเว็บไซต์ โดยจำกัดจำนวนการเชื่อมต่อพร้อมกัน"""
        # ตรวจสอบแคชก่อน
        if url in self.cache:
            return self.cache[url]
            
        try:
            async with browser_semaphore:  # ใช้ semaphore เพื่อจำกัดจำนวนการเชื่อมต่อพร้อมกัน
                logger.info(f"Fetching: {url}")
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent=random.choice(USER_AGENTS)  # สุ่มเลือก User Agent
                    )
                    page = await context.new_page()
                    
                    # ตั้งค่า cookies เพื่อหลีกเลี่ยงการตรวจจับ bot
                    await page.context.add_cookies([{
                        "name": "CONSENT", 
                        "value": "YES+", 
                        "domain": ".google.com",
                        "path": "/"
                    }])
                    
                    # ใช้ networkidle เพื่อให้แน่ใจว่าหน้าเว็บโหลดสมบูรณ์
                    await page.goto(url, timeout=self.timeout, wait_until="networkidle")
                    
                    # รอให้ JavaScript ทำงานเพื่อให้แน่ใจว่าผลการค้นหาแสดงออกมาสมบูรณ์
                    await page.wait_for_timeout(3000)
                    
                    content = await page.content()
                    await browser.close()
                    
                    # แคชข้อมูล
                    self.cache[url] = content
                    return content
        except Exception as e:
            logger.error(f"Error with Playwright: {e}")
            return ""
            
    async def get_website_content(self, url: str) -> Optional[str]:
        """ดึงเนื้อหาเว็บไซต์เพื่อวิเคราะห์"""
        try:
            html = await self.fetch_with_playwright(url)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup(["script", "style", "meta", "link", "noscript"]):
                    tag.decompose()
                return soup.get_text(separator=" ", strip=True)
            return None
        except Exception as e:
            logger.error(f"Error fetching content: {e}")
            return None

    async def search(self, domain: str, keyword: str) -> List[Dict]:
        """วิธีการค้นหาจะถูกกำหนดในคลาสลูก"""
        raise NotImplementedError()


class GoogleSearch(SearchEngine):
    """ค้นหาโดยใช้ Google Search"""
    
    async def search(self, domain: str, keyword: str) -> List[Dict]:
        # สร้าง cache key
        cache_key = f"google_{domain}_{keyword}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        query = urllib.parse.quote(f'site:{domain} "{keyword}"')
        url = f"https://www.google.com/search?q={query}"
        
        logger.info(f"Searching Google: site:{domain} \"{keyword}\"")
        
        try:
            html = await self.fetch_with_playwright(url)
            soup = BeautifulSoup(html, "html.parser")
            
            search_results = []
            results = soup.select("div.g")
            
            for result in results:
                title_element = result.select_one("h3")
                link_element = result.select_one("a")
                snippet_element = result.select_one("div.VwiC3b") or result.select_one("span.st")
                
                if title_element and link_element and link_element.has_attr("href"):
                    title = title_element.get_text(strip=True)
                    link = link_element["href"]
                    
                    # ตรวจสอบว่าเป็น URL ที่ถูกต้องและมีโดเมนที่เราค้นหา
                    if link.startswith("http") and domain in link:
                        snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                        search_results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet
                        })
            
            # แคชผลลัพธ์
            self.cache[cache_key] = search_results
            return search_results
        except Exception as e:
            logger.error(f"Error with Google search: {e}")
            return []


class DuckDuckGoSearch(SearchEngine):
    """ค้นหาโดยใช้ DuckDuckGo"""
    
    async def search(self, domain: str, keyword: str) -> List[Dict]:
        # สร้าง cache key
        cache_key = f"ddg_{domain}_{keyword}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        query = urllib.parse.quote(f'site:{domain} "{keyword}"')
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        logger.info(f"Searching DuckDuckGo: site:{domain} \"{keyword}\"")
        
        try:
            html = await self.fetch_with_playwright(url)
            soup = BeautifulSoup(html, "html.parser")
            results = soup.find_all("div", class_="result")
            search_results = []
            
            for result in results:
                link_el = result.find("a", class_="result__a")
                if not link_el or not link_el.has_attr("href"):
                    continue
                    
                href = link_el["href"]
                title = link_el.get_text(strip=True)
                snippet = result.find("a", class_="result__snippet") or result.find("div", class_="result__snippet")
                snippet_text = snippet.get_text(strip=True) if snippet else ""
                
                # แยกโดเมนจาก href
                match = re.search(r"uddg=([^&]+)", href)
                if match:
                    decoded_url = urllib.parse.unquote(match.group(1))
                    if domain in decoded_url:
                        search_results.append({
                            "title": title,
                            "link": decoded_url,
                            "snippet": snippet_text
                        })
            
            # แคชผลลัพธ์
            self.cache[cache_key] = search_results
            return search_results
        except Exception as e:
            logger.error(f"Error with DuckDuckGo search: {e}")
            return []


class BingSearch(SearchEngine):
    """ค้นหาโดยใช้ Bing Search"""
    
    async def search(self, domain: str, keyword: str) -> List[Dict]:
        # สร้าง cache key
        cache_key = f"bing_{domain}_{keyword}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        query = urllib.parse.quote(f'site:{domain} "{keyword}"')
        url = f"https://www.bing.com/search?q={query}"
        
        logger.info(f"Searching Bing: site:{domain} \"{keyword}\"")
        
        try:
            html = await self.fetch_with_playwright(url)
            soup = BeautifulSoup(html, "html.parser")
            search_results = []
            
            # Bing มีโครงสร้าง HTML แตกต่างจาก Google
            results = soup.select("li.b_algo")
            
            for result in results:
                title_element = result.select_one("h2")
                link_element = result.select_one("h2 a")
                snippet_element = result.select_one("div.b_caption p")
                
                if title_element and link_element and link_element.has_attr("href"):
                    title = title_element.get_text(strip=True)
                    link = link_element["href"]
                    
                    # ตรวจสอบว่าเป็น URL ที่ถูกต้องและมีโดเมนที่เราค้นหา
                    if link.startswith("http") and domain in link:
                        snippet = snippet_element.get_text(strip=True) if snippet_element else ""
                        search_results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet
                        })
            
            # แคชผลลัพธ์
            self.cache[cache_key] = search_results
            return search_results
        except Exception as e:
            logger.error(f"Error with Bing search: {e}")
            return []


# สร้าง semaphore สำหรับควบคุมการทำงานพร้อมกันของเครื่องมือค้นหา
search_semaphore = asyncio.Semaphore(2)  # ลดจำนวนการค้นหาพร้อมกันเพื่อลดโอกาสถูกบล็อก

async def search_engine_with_semaphore(engine, domain: str, keyword: str) -> List[Dict]:
    """ใช้ semaphore เพื่อจำกัดจำนวนการค้นหาที่ทำงานพร้อมกัน"""
    async with search_semaphore:
        # เว้นช่วงสุ่มเพื่อป้องกันการถูกบล็อกจากค้นหาพร้อมกัน
        delay = 0.5 + random.random()  # 0.5 ถึง 1.5 วินาที
        await asyncio.sleep(delay)
        return await engine.search(domain, keyword)

async def search_multiple_engines(domain: str, keyword: str) -> List[Dict]:
    """ค้นหาในหลายเครื่องมือค้นหาและรวมผลลัพธ์ โดยค้นหาพร้อมกัน"""
    engines = [
        GoogleSearch(timeout=25000),  # ใช้ timeout ที่เหมาะสม
        DuckDuckGoSearch(timeout=25000),
        BingSearch(timeout=25000)
    ]
    
    # สร้างชุดงานค้นหาเพื่อทำงานพร้อมกัน
    tasks = [search_engine_with_semaphore(engine, domain, keyword) for engine in engines]
    
    # ทำงานพร้อมกันแต่มีการควบคุมด้วย semaphore
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_results = []
    seen_urls = set()
    
    # รวมผลลัพธ์จากทุกเครื่องมือค้นหา
    for engine_results in results:
        if isinstance(engine_results, Exception):
            logger.error(f"Error with search engine: {engine_results}")
            continue
            
        # เพิ่มผลลัพธ์ที่ไม่ซ้ำกัน
        for result in engine_results:
            if result["link"] not in seen_urls:
                all_results.append(result)
                seen_urls.add(result["link"])
    
    # เพิ่ม logging เพื่อการดีบัก
    logger.info(f"Found {len(all_results)} unique results across all search engines for {domain} with keyword {keyword}")
    
    # ตรวจสอบถ้าไม่มีผลลัพธ์ ให้ลองเครื่องมือค้นหาแบบเดิมอีกครั้ง
    if not all_results:
        logger.warning(f"No results found in first pass for {domain} with keyword {keyword}, trying Google again with different settings")
        
        # ลองใช้ Google อีกครั้งแบบแยก
        try:
            google = GoogleSearch(timeout=30000)  # เพิ่ม timeout
            # หน่วงเวลาเล็กน้อยก่อนลองอีกครั้ง
            await asyncio.sleep(2)
            fallback_results = await google.search(domain, keyword)
            
            for result in fallback_results:
                if result["link"] not in seen_urls:
                    all_results.append(result)
                    seen_urls.add(result["link"])
                    
            logger.info(f"Fallback search added {len(fallback_results)} more results")
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
    
    return all_results