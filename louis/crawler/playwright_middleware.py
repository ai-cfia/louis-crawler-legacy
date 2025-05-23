"""
Playwright middleware for handling JavaScript-rendered content in Scrapy.
"""
import asyncio
from typing import Union, Optional
from scrapy import signals
from scrapy.http import HtmlResponse, Request
from scrapy.utils.defer import deferred_from_coro
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import logging

logger = logging.getLogger(__name__)


class PlaywrightMiddleware:
    """Scrapy middleware to handle requests with Playwright for JavaScript rendering."""
    
    def __init__(self, browser_type='chromium', headless=True, **browser_kwargs):
        self.browser_type = browser_type
        self.headless = headless
        self.browser_kwargs = browser_kwargs
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.browser_context: Optional[BrowserContext] = None
        
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler settings."""
        browser_type = crawler.settings.get('PLAYWRIGHT_BROWSER_TYPE', 'chromium')
        headless = crawler.settings.get('PLAYWRIGHT_HEADLESS', True)
        
        # Additional browser arguments
        browser_kwargs = {
            'args': crawler.settings.get('PLAYWRIGHT_BROWSER_ARGS', []),
        }
        
        middleware = cls(
            browser_type=browser_type,
            headless=headless,
            **browser_kwargs
        )
        
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        
        return middleware
    
    async def _create_browser(self):
        """Create browser instance."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = await browser_launcher.launch(
            headless=self.headless,
            **self.browser_kwargs
        )
        
        # Create a browser context with common settings
        self.browser_context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
    async def _close_browser(self):
        """Close browser and playwright."""
        if self.browser_context:
            await self.browser_context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def spider_opened(self, spider):
        """Initialize when spider opens."""
        spider.logger.info("PlaywrightMiddleware: Spider opened")
        return deferred_from_coro(self._create_browser())
    
    def spider_closed(self, spider):
        """Cleanup when spider closes."""
        spider.logger.info("PlaywrightMiddleware: Spider closed")
        return deferred_from_coro(self._close_browser())
    
    def process_request(self, request: Request, spider):
        """Process request with Playwright if needed."""
        # Only use Playwright for requests that need it
        if not self._should_use_playwright(request, spider):
            return None
            
        return deferred_from_coro(self._handle_playwright_request(request, spider))
    
    def _should_use_playwright(self, request: Request, spider) -> bool:
        """Determine if request should be handled by Playwright."""
        # Use Playwright if explicitly requested
        if request.meta.get('playwright', False):
            return True
            
        # Use Playwright for spiders that opt-in
        if hasattr(spider, 'use_playwright') and spider.use_playwright:
            return True
            
        return False
    
    async def _handle_playwright_request(self, request: Request, spider) -> HtmlResponse:
        """Handle request using Playwright."""
        try:
            if not self.browser_context:
                await self._create_browser()
            
            page: Page = await self.browser_context.new_page()
            
            # Configure page settings
            await self._configure_page(page, request)
            
            # Navigate to the URL
            response = await page.goto(
                request.url,
                wait_until=request.meta.get('playwright_wait_until', 'networkidle'),
                timeout=request.meta.get('playwright_timeout', 30000)
            )
            
            # Wait for specific elements or conditions if specified
            await self._wait_for_conditions(page, request)
            
            # Get the page content
            content = await page.content()
            
            # Create Scrapy response
            scrapy_response = HtmlResponse(
                url=request.url,
                body=content.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            
            await page.close()
            return scrapy_response
            
        except Exception as e:
            spider.logger.error(f"PlaywrightMiddleware error for {request.url}: {e}")
            # Return None to let Scrapy handle with default downloader
            return None
    
    async def _configure_page(self, page: Page, request: Request):
        """Configure page settings before navigation."""
        # Set headers if provided
        if 'headers' in request.meta:
            await page.set_extra_http_headers(request.meta['headers'])
        
        # Block unnecessary resources if specified
        if request.meta.get('playwright_block_resources'):
            await page.route(
                "**/*",
                lambda route: route.abort() if route.request.resource_type in ["image", "font", "stylesheet"] else route.continue_()
            )
    
    async def _wait_for_conditions(self, page: Page, request: Request):
        """Wait for specific conditions before extracting content."""
        # Wait for specific selector
        if 'playwright_wait_for_selector' in request.meta:
            selector = request.meta['playwright_wait_for_selector']
            timeout = request.meta.get('playwright_selector_timeout', 10000)
            try:
                await page.wait_for_selector(selector, timeout=timeout)
            except Exception as e:
                logger.warning(f"Timeout waiting for selector {selector}: {e}")
        
        # Wait for specific function
        if 'playwright_wait_for_function' in request.meta:
            function = request.meta['playwright_wait_for_function']
            timeout = request.meta.get('playwright_function_timeout', 10000)
            try:
                await page.wait_for_function(function, timeout=timeout)
            except Exception as e:
                logger.warning(f"Timeout waiting for function {function}: {e}")
        
        # Additional wait time
        if 'playwright_wait_time' in request.meta:
            await asyncio.sleep(request.meta['playwright_wait_time'])
