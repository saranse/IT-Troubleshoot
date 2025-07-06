import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import json
import logging
from urllib.parse import urlparse

from . import models
from .database import SessionLocal, get_redis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_domain_keywords(db: SessionLocal) -> List[str]:
    """Get active keywords from database"""
    with db() as session:
        keywords = session.query(models.Keyword).filter(models.Keyword.is_active == True).all()
        return [k.word for k in keywords]

def get_whitelist(db: SessionLocal) -> List[str]:
    """Get whitelisted domains from database"""
    with db() as session:
        whitelist = session.query(models.Whitelist).all()
        return [w.url for w in whitelist]

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def scan_url(url: str, keywords: List[str]) -> Dict[str, Any]:
    """Scan a single URL for keywords"""
    if not is_valid_url(url):
        return {
            "status": "error",
            "error_message": "Invalid URL format",
            "matches": {}
        }

    try:
        # Add http:// if no scheme specified
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        
        # Find matches
        matches = {}
        for keyword in keywords:
            if keyword.lower() in text.lower():
                # Get context around match
                start = max(0, text.lower().find(keyword.lower()) - 50)
                end = min(len(text), text.lower().find(keyword.lower()) + len(keyword) + 50)
                context = text[start:end].strip()
                matches[keyword] = context
        
        return {
            "status": "success",
            "matches": matches
        }
        
    except requests.RequestException as e:
        return {
            "status": "error",
            "error_message": str(e),
            "matches": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}",
            "matches": {}
        }

def scan_domain_task(url: str, keywords: List[str] = None) -> Dict[str, Any]:
    """Background task to scan a domain"""
    db = SessionLocal()
    try:
        # Get domain from database
        domain = db.query(models.Domain).filter(models.Domain.url == url).first()
        if not domain:
            return {
                "status": "error",
                "error_message": "Domain not found in database",
                "matches": {}
            }

        # Get keywords if not provided
        if keywords is None:
            keywords = get_domain_keywords(SessionLocal)

        # Get whitelist
        whitelist = get_whitelist(SessionLocal)
        if url in whitelist:
            return {
                "status": "skipped",
                "error_message": "Domain is whitelisted",
                "matches": {}
            }

        # Scan the domain
        result = scan_url(url, keywords)

        # Update scan result in database
        scan_result = models.ScanResult(
            domain_id=domain.id,
            status=result["status"],
            matches=result["matches"],
            error_message=result.get("error_message"),
            scan_date=datetime.utcnow()
        )
        db.add(scan_result)
        
        # Update domain last_scanned timestamp
        domain.last_scanned = datetime.utcnow()
        
        db.commit()
        return result

    except Exception as e:
        logger.error(f"Error scanning domain {url}: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Worker error: {str(e)}",
            "matches": {}
        }
    finally:
        db.close()