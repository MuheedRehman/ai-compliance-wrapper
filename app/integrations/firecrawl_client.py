import httpx
import logging
import asyncio

from typing import Dict, Any, Optional
from app.config import FIRECRAWL_API_KEY, FIRECRAWL_API_URL, FIRECRAWL_TIMEOUT

logger = logging.getLogger(__name__)

class FirecrawlClientError(Exception):
    pass

class FirecrawlClient:
    """Wrapper for Firecrawl API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.api_key = api_key or FIRECRAWL_API_KEY
        self.base_url = base_url or FIRECRAWL_API_URL
        self.timeout = timeout or FIRECRAWL_TIMEOUT

        if not self.api_key:
            logger.warning("FIRECRAWL_API_KEY is not set. Firecrawl operations will fail if called.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _request_with_retry(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        retries = 2
        delay = 1.0
        
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method,
                        f"{self.base_url}{path}",
                        headers=self._get_headers(),
                        **kwargs
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                if attempt < retries and e.response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"Firecrawl retry {attempt+1}/{retries} after {e.response.status_code}")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                logger.error(f"Firecrawl {method} HTTP error: {e.response.status_code} - {e.response.text}")
                raise FirecrawlClientError(f"HTTP Error: {e.response.status_code}") from e
            except httpx.RequestError as e:
                if attempt < retries:
                    logger.warning(f"Firecrawl retry {attempt+1}/{retries} after request error: {e}")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                logger.error(f"Firecrawl {method} request error: {e}")
                raise FirecrawlClientError(f"Request Error: {str(e)}") from e

    async def scrape(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Scrape a single URL."""
        if not self.api_key:
            raise FirecrawlClientError("Firecrawl API key is missing")

        payload = {"url": url}
        if params:
            payload.update(params)

        return await self._request_with_retry("POST", "/scrape", json=payload)

    async def crawl(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiate a crawl for a URL (asynchronous operation on Firecrawl side)."""
        if not self.api_key:
            raise FirecrawlClientError("Firecrawl API key is missing")

        payload = {"url": url}
        if params:
            payload.update(params)

        return await self._request_with_retry("POST", "/crawl", json=payload)

    async def check_crawl_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a crawl job."""
        if not self.api_key:
            raise FirecrawlClientError("Firecrawl API key is missing")

        return await self._request_with_retry("GET", f"/crawl/{job_id}")
