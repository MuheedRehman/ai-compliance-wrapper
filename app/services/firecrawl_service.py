from typing import Dict, Any, List, Optional
from app.integrations.firecrawl_client import FirecrawlClient, FirecrawlClientError
from app.config import FIRECRAWL_ALLOWED_DOMAINS, FIRECRAWL_MAX_PAGES
import urllib.parse
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class FirecrawlServiceError(Exception):
    pass

class FirecrawlService:
    """Service layer for coordinating Firecrawl actions with application logic."""
    
    def __init__(self, client: Optional[FirecrawlClient] = None):
        self.client = client or FirecrawlClient()
        self.allowed_domains = self._parse_allowed_domains(FIRECRAWL_ALLOWED_DOMAINS)
        self.max_pages = FIRECRAWL_MAX_PAGES

    def _parse_allowed_domains(self, domains_str: str) -> List[str]:
        if not domains_str:
            return []
        return [d.strip().lower() for d in domains_str.split(",") if d.strip()]

    def _is_url_allowed(self, url: str) -> bool:
        if not url:
            return False
            
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            if not parsed.hostname:
                return False
            
            if not self.allowed_domains:
                return True # Allow all valid URLs if no domains configured
                
            domain = parsed.hostname.lower()
            return any(domain == allowed or domain.endswith("." + allowed) for allowed in self.allowed_domains)
        except Exception:
            return False

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape a single URL and return normalized artifact metadata."""
        if not self._is_url_allowed(url):
            raise FirecrawlServiceError(f"URL not valid or domain not allowed: {url}")

        try:
            response = await self.client.scrape(url)
            
            # Normalize response into an artifact-like structure
            return {
                "source_url": url,
                "source_type": "scrape",
                "status": "success" if response.get("success") else "failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": response.get("data", {}),
                "metadata": {
                    "title": response.get("data", {}).get("metadata", {}).get("title"),
                    "description": response.get("data", {}).get("metadata", {}).get("description"),
                }
            }
        except FirecrawlClientError as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
            raise FirecrawlServiceError(f"Scrape failed: {e}") from e

    async def crawl_site(self, url: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Initiate a crawl for a site or docs section."""
        if not self._is_url_allowed(url):
            raise FirecrawlServiceError(f"URL not valid or domain not allowed: {url}")

        if limit is not None:
            if limit <= 0:
                raise FirecrawlServiceError("Crawl limit must be a positive integer")
            actual_limit = min(limit, self.max_pages)
        else:
            actual_limit = self.max_pages
        
        try:
            params = {"limit": actual_limit}
            response = await self.client.crawl(url, params=params)
            
            return {
                "source_url": url,
                "source_type": "crawl_job",
                "job_id": response.get("id"),
                "status": "initiated",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except FirecrawlClientError as e:
            logger.error(f"Failed to initiate crawl for URL {url}: {e}")
            raise FirecrawlServiceError(f"Crawl initiation failed: {e}") from e

    async def check_crawl_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of an ongoing crawl job and return normalized results if done."""
        try:
            response = await self.client.check_crawl_status(job_id)
            
            status = response.get("status", "unknown")
            normalized = {
                "job_id": job_id,
                "source_type": "crawl_result",
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": [],
                "completed": response.get("completed", 0),
                "total": response.get("total", 0)
            }
            
            if status == "completed":
                normalized["data"] = response.get("data", [])
                
            return normalized
        except FirecrawlClientError as e:
            logger.error(f"Failed to check crawl status for job {job_id}: {e}")
            raise FirecrawlServiceError(f"Crawl status check failed: {e}") from e
