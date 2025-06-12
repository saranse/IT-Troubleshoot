import asyncio
import aiohttp
import re
import urllib.parse
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class SearchEngine:
    """คลาสพื้นฐานสำหรับเครื่องมือค้นหา"""
    
    def __init__(self, timeout: int = 30000):
        self.timeout = timeout
        
    async def fetch_with_playwright(self, url: str) -> str:
        """ใช้ Playwright เพื่อดึงข้อมูลเว็บไซต์"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = await context.new_page()
                
                # ตั้งค่า cookies เพื่อหลีกเลี่ยงการตรวจจับ bot
                await page.context.add_cookies([{
                    "name": "CONSENT", 
                    "value": "YES+", 
                    "domain": ".google.com",
                    "path": "/"
                }])
                
                await page.goto(url, timeout=self.timeout, wait_until="networkidle")
                content = await page.content()
                await browser.close()
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
        query = urllib.parse.quote(f'site:{domain} "{keyword}"')
        url = f"https://www.google.com/search?q={query}"
        
        logger.info(f"Searching Google: site:{domain} \"{keyword}\"")
        
        try:
            html = await self.fetch_with_playwright(url)
            soup = BeautifulSoup(html, "html.parser")
            
            # บันทึกหน้าเว็บเพื่อการดีบัก
  #          with open(f"debug_google_{domain}_{keyword}.html", "w", encoding="utf-8") as f:
 #               f.write(html)
            
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
            
            return search_results
        except Exception as e:
            logger.error(f"Error with Google search: {e}")
            return []


class DuckDuckGoSearch(SearchEngine):
    """ค้นหาโดยใช้ DuckDuckGo"""
    
    async def search(self, domain: str, keyword: str) -> List[Dict]:
        query = urllib.parse.quote(f'site:{domain} "{keyword}"')
        url = f"https://html.duckduckgo.com/html/?q={query}"
        
        logger.info(f"Searching DuckDuckGo: site:{domain} \"{keyword}\"")
        
        try:
            html = await self.fetch_with_playwright(url)
            
            # บันทึกหน้าเว็บเพื่อการดีบัก
 #           with open(f"debug_ddg_{domain}_{keyword}.html", "w", encoding="utf-8") as f:
 #               f.write(html)
            
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
            
            return search_results
        except Exception as e:
            logger.error(f"Error with DuckDuckGo search: {e}")
            return []


class BingSearch(SearchEngine):
    """ค้นหาโดยใช้ Bing Search"""
    
    async def search(self, domain: str, keyword: str) -> List[Dict]:
        query = urllib.parse.quote(f'site:{domain} "{keyword}"')
        url = f"https://www.bing.com/search?q={query}"
        
        logger.info(f"Searching Bing: site:{domain} \"{keyword}\"")
        
        try:
            html = await self.fetch_with_playwright(url)
            
            # บันทึกหน้าเว็บเพื่อการดีบัก
#            with open(f"debug_bing_{domain}_{keyword}.html", "w", encoding="utf-8") as f:
#                f.write(html)
                
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
            
            return search_results
        except Exception as e:
            logger.error(f"Error with Bing search: {e}")
            return []


async def search_multiple_engines(domain: str, keyword: str) -> List[Dict]:
    """ค้นหาในหลายเครื่องมือค้นหาและรวมผลลัพธ์"""
    engines = [
        GoogleSearch(),
        DuckDuckGoSearch(),
        BingSearch()
    ]
    
    all_results = []
    seen_urls = set()
    
    for engine in engines:
        try:
            results = await engine.search(domain, keyword)
            
            # เพิ่มผลลัพธ์ที่ไม่ซ้ำกัน
            for result in results:
                if result["link"] not in seen_urls:
                    all_results.append(result)
                    seen_urls.add(result["link"])
            
            # หากพบผลลัพธ์แล้ว อาจไม่จำเป็นต้องค้นหาด้วยเครื่องมืออื่นอีก
            if len(all_results) > 0:
                break
                
        except Exception as e:
            logger.error(f"Error with search engine {engine.__class__.__name__}: {e}")
    
    return all_results