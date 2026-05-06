import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.firecrawl_service import FirecrawlService, FirecrawlServiceError
from app.integrations.firecrawl_client import FirecrawlClient, FirecrawlClientError
import app.config
import importlib
import httpx
import os

@pytest.fixture
def mock_client():
    client = MagicMock(spec=FirecrawlClient)
    client.scrape = AsyncMock()
    client.crawl = AsyncMock()
    client.check_crawl_status = AsyncMock()
    client.api_key = "test-key"
    return client

@pytest.fixture
def service(mock_client):
    svc = FirecrawlService(client=mock_client)
    # Clear allowed domains to test allow-all by default, or set specifically
    svc.allowed_domains = []
    return svc

# -----------------------------------------------------------------------------
# Service Normalization & Validation Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scrape_url_success(service, mock_client):
    mock_response = {
        "success": True,
        "data": {
            "content": "Test content",
            "metadata": {
                "title": "Test Title",
                "description": "Test Desc"
            }
        }
    }
    mock_client.scrape.return_value = mock_response

    result = await service.scrape_url("https://example.com/page")
    
    assert result["status"] == "success"
    assert result["source_type"] == "scrape"
    assert result["source_url"] == "https://example.com/page"
    assert "timestamp" in result
    assert result["metadata"]["title"] == "Test Title"
    mock_client.scrape.assert_called_once_with("https://example.com/page")

@pytest.mark.asyncio
async def test_scrape_url_domain_not_allowed(service, mock_client):
    service.allowed_domains = ["allowed.com"]
    with pytest.raises(FirecrawlServiceError, match="URL not valid or domain not allowed"):
        await service.scrape_url("https://malicious.com/page")
    mock_client.scrape.assert_not_called()

@pytest.mark.asyncio
async def test_scrape_url_domain_subdomain_allowed(service, mock_client):
    service.allowed_domains = ["allowed.com"]
    mock_client.scrape.return_value = {"success": True}
    
    await service.scrape_url("https://sub.allowed.com/page")
    mock_client.scrape.assert_called_once_with("https://sub.allowed.com/page")

@pytest.mark.asyncio
async def test_scrape_url_invalid_scheme(service, mock_client):
    with pytest.raises(FirecrawlServiceError, match="URL not valid or domain not allowed"):
        await service.scrape_url("ftp://example.com/page")
    mock_client.scrape.assert_not_called()

@pytest.mark.asyncio
async def test_scrape_url_missing_hostname(service, mock_client):
    with pytest.raises(FirecrawlServiceError, match="URL not valid or domain not allowed"):
        await service.scrape_url("https:///page")
    mock_client.scrape.assert_not_called()

@pytest.mark.asyncio
async def test_scrape_url_client_error(service, mock_client):
    mock_client.scrape.side_effect = FirecrawlClientError("HTTP Error: 404")
    with pytest.raises(FirecrawlServiceError, match="Scrape failed"):
        await service.scrape_url("https://example.com/404")

@pytest.mark.asyncio
async def test_crawl_site_success_normalization(service, mock_client):
    mock_client.crawl.return_value = {"id": "job-123"}
    
    result = await service.crawl_site("https://example.com/docs")
    
    assert result["source_type"] == "crawl_job"
    assert result["job_id"] == "job-123"
    assert result["status"] == "initiated"
    assert result["source_url"] == "https://example.com/docs"
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_crawl_site_limit_capping(service, mock_client):
    mock_client.crawl.return_value = {"id": "job-124"}
    service.max_pages = 50
    await service.crawl_site("https://example.com/docs", limit=100)
    mock_client.crawl.assert_called_once_with("https://example.com/docs", params={"limit": 50})

@pytest.mark.asyncio
async def test_crawl_site_limit_zero_rejected(service, mock_client):
    with pytest.raises(FirecrawlServiceError, match="Crawl limit must be a positive integer"):
        await service.crawl_site("https://example.com/docs", limit=0)
    mock_client.crawl.assert_not_called()

@pytest.mark.asyncio
async def test_crawl_site_limit_negative_rejected(service, mock_client):
    with pytest.raises(FirecrawlServiceError, match="Crawl limit must be a positive integer"):
        await service.crawl_site("https://example.com/docs", limit=-5)
    mock_client.crawl.assert_not_called()

@pytest.mark.asyncio
async def test_check_crawl_status_completed_normalization(service, mock_client):
    mock_client.check_crawl_status.return_value = {
        "status": "completed",
        "completed": 5,
        "total": 5,
        "data": [
            {"url": "https://example.com/1", "content": "c1"},
            {"url": "https://example.com/2", "content": "c2"}
        ]
    }
    
    result = await service.check_crawl_status("job-123")
    
    assert result["status"] == "completed"
    assert len(result["data"]) == 2
    assert result["completed"] == 5
    assert result["source_type"] == "crawl_result"
    assert result["job_id"] == "job-123"
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_check_crawl_status_in_progress(service, mock_client):
    mock_client.check_crawl_status.return_value = {
        "status": "scraping",
        "completed": 2,
        "total": 10
    }
    result = await service.check_crawl_status("job-123")
    assert result["status"] == "scraping"
    assert result["data"] == []
    assert result["completed"] == 2

# -----------------------------------------------------------------------------
# Client Retry Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_api_key():
    client = FirecrawlClient(api_key="")
    with pytest.raises(FirecrawlClientError, match="API key is missing"):
        await client.scrape("http://example.com")

@pytest.mark.asyncio
@patch("app.integrations.firecrawl_client.httpx.AsyncClient")
async def test_retry_on_429_then_success(mock_async_client_class):
    client = FirecrawlClient(api_key="test")
    
    # Setup mock to raise HTTPStatusError with 429 on first call, then succeed
    mock_client_instance = AsyncMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_client_instance
    
    # Create a 429 error
    error_response = httpx.Response(429, request=httpx.Request("POST", "http://test"))
    http_error = httpx.HTTPStatusError("Too Many Requests", request=error_response.request, response=error_response)
    
    # Create a success response
    success_response = MagicMock()
    success_response.json.return_value = {"success": True, "data": {"content": "ok"}}
    success_response.raise_for_status.return_value = None
    
    mock_client_instance.request.side_effect = [http_error, success_response]
    
    with patch("app.integrations.firecrawl_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await client.scrape("http://example.com")
        assert result["success"] is True
        assert mock_client_instance.request.call_count == 2
        mock_sleep.assert_called_once()

@pytest.mark.asyncio
@patch("app.integrations.firecrawl_client.httpx.AsyncClient")
async def test_request_error_retry_exhaustion(mock_async_client_class):
    client = FirecrawlClient(api_key="test")
    
    mock_client_instance = AsyncMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_client_instance
    
    # Create a request error that occurs 3 times (retries=2 + 1 initial = 3)
    req_error = httpx.RequestError("Connection failed", request=httpx.Request("POST", "http://test"))
    mock_client_instance.request.side_effect = [req_error, req_error, req_error]
    
    with patch("app.integrations.firecrawl_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(FirecrawlClientError, match="Request Error: Connection failed"):
            await client.scrape("http://example.com")
            
        assert mock_client_instance.request.call_count == 3
        assert mock_sleep.call_count == 2

# -----------------------------------------------------------------------------
# Config Validation Tests
# -----------------------------------------------------------------------------

def get_base_env():
    return {
        "EVIDENCE_HMAC_SECRET": "test-secret-key-12345",
        "DATABASE_URL": "sqlite:///:memory:",
        "OPENAI_API_KEY": "test",
        "APP_ENV": "test",
        "FEATURE_ID_ENFORCEMENT": "warn",
        "CANDIDATE_VERSION_POLICY": "allow_with_warning"
    }

def test_config_timeout_negative():
    env = get_base_env()
    env["FIRECRAWL_TIMEOUT"] = "-5"
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(RuntimeError, match="FIRECRAWL_TIMEOUT must be a positive integer."):
            importlib.reload(app.config)
            
    # Restore normal config after test deterministically
    with patch.dict(os.environ, get_base_env(), clear=True):
        importlib.reload(app.config)

def test_config_max_pages_zero():
    env = get_base_env()
    env["FIRECRAWL_MAX_PAGES"] = "0"
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(RuntimeError, match="FIRECRAWL_MAX_PAGES must be a positive integer."):
            importlib.reload(app.config)
            
    # Restore normal config after test deterministically
    with patch.dict(os.environ, get_base_env(), clear=True):
        importlib.reload(app.config)
