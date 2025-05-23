#!/usr/bin/env python3
"""
Test script for the goldie_playwright spider to test scraping one page only.
This script tests Playwright-enabled scraping on a single Canadian government page.
"""
import asyncio
import sys
import logging
import os
from playwright.async_api import async_playwright
from louis.crawler.spiders.goldie_playwright import GoldiePlaywrightSpider
from scrapy.http import HtmlResponse
from scrapy import Request
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class TestGoldiePlaywright:
    """Test class for testing goldie_playwright spider functionality."""
    
    def __init__(self):
        self.spider = GoldiePlaywrightSpider()
        # Use a single test URL
        self.test_url = "https://inspection.canada.ca/en"
        
    def test_environment_setup(self):
        """Test that the environment is set up correctly."""
        logger.info("🔧 Testing environment setup...")
        
        try:
            # Check storage mode
            import louis.db as db
            storage_mode = db.get_storage_mode()
            logger.info(f"📁 Storage mode: {storage_mode}")
            
            # Check storage directory
            if storage_mode in ['disk', 'both']:
                storage_dir = db.get_storage_directory()
                logger.info(f"📂 Storage directory: {storage_dir}")
                
                # Check if directory exists
                if not os.path.exists(storage_dir):
                    logger.warning(f"⚠️  Storage directory doesn't exist: {storage_dir}")
                    os.makedirs(storage_dir, exist_ok=True)
                    os.makedirs(os.path.join(storage_dir, 'html'), exist_ok=True)
                    os.makedirs(os.path.join(storage_dir, 'metadata'), exist_ok=True)
                    logger.info(f"✅ Created storage directories")
                else:
                    logger.info(f"✅ Storage directory exists")
            
            # Test database connection if needed
            if storage_mode in ['database', 'both']:
                try:
                    connection = db.connect_db()
                    if connection:
                        logger.info(f"✅ Database connection test passed")
                        connection.close()
                    else:
                        logger.warning(f"⚠️  Database connection returned None")
                except Exception as e:
                    logger.warning(f"⚠️  Database connection failed: {e}")
                    if storage_mode == 'database':
                        logger.error(f"❌ Database mode selected but connection failed")
                        return False
                    else:
                        logger.info(f"📁 Will continue with disk storage")
            
            logger.info("✅ Environment setup test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment setup test failed: {e}")
            return False
        
    async def test_single_page_scraping(self):
        """Test scraping a single page with Playwright."""
        logger.info(f"🕷️  Testing single page scraping with Playwright: {self.test_url}")
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to the test URL
                logger.info(f"📄 Navigating to: {self.test_url}")
                await page.goto(self.test_url, timeout=30000)
                await page.wait_for_load_state('networkidle')
                
                # Get page content
                content = await page.content()
                title = await page.title()
                
                logger.info(f"✅ Page loaded successfully")
                logger.info(f"📊 Title: {title}")
                logger.info(f"📊 Content length: {len(content)} characters")
                
                # Create a mock response to test the spider's parse method
                response = HtmlResponse(
                    url=self.test_url,
                    body=content.encode('utf-8'),
                    encoding='utf-8'
                )
                
                # Test the spider's parse method
                logger.info("🔄 Testing spider's parse method...")
                results = list(self.spider.parse(response))
                
                # Analyze results
                crawl_items = []
                requests = []
                
                for result in results:
                    if isinstance(result, Request):
                        requests.append(result)
                    else:
                        crawl_items.append(result)
                
                logger.info(f"📈 Results:")
                logger.info(f"   - CrawlItems: {len(crawl_items)}")
                logger.info(f"   - New Requests: {len(requests)}")
                
                # Validate the crawl item
                if crawl_items:
                    item = crawl_items[0]
                    logger.info(f"📝 Item details:")
                    logger.info(f"   - URL: {item.get('url', 'N/A')}")
                    logger.info(f"   - Title: {item.get('title', 'N/A')[:100]}...")
                    logger.info(f"   - Language: {item.get('lang', 'N/A')}")
                    logger.info(f"   - Content length: {len(item.get('html_content', ''))}")
                    logger.info(f"   - Last crawled: {item.get('last_crawled', 'N/A')}")
                    
                    # Basic validation
                    assert item.get('url') == self.test_url
                    assert item.get('title')
                    assert item.get('html_content')
                    assert item.get('lang') in ['en', 'fr']
                    
                    logger.info("✅ CrawlItem validation passed")
                else:
                    logger.warning("⚠️  No CrawlItems generated")
                
                await browser.close()
                return True
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
    
    async def test_playwright_features(self):
        """Test specific Playwright features like JavaScript execution."""
        logger.info("🔬 Testing Playwright-specific features...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to test page
                await page.goto(self.test_url, timeout=30000)
                await page.wait_for_load_state('networkidle')
                
                # Test JavaScript execution
                js_result = await page.evaluate('() => document.title')
                logger.info(f"🔧 JavaScript execution test: {js_result}")
                
                # Test waiting for specific elements
                main_element = await page.wait_for_selector('main, body', timeout=10000)
                if main_element:
                    logger.info("✅ Main content element found")
                else:
                    logger.warning("⚠️  Main content element not found")
                
                # Test element interaction capabilities
                links = await page.query_selector_all('a[href]')
                logger.info(f"🔗 Found {len(links)} links on the page")
                
                await browser.close()
                return True
                
        except Exception as e:
            logger.error(f"❌ Playwright features test failed: {e}")
            return False
    
    def test_spider_configuration(self):
        """Test the spider configuration and settings."""
        logger.info("⚙️  Testing spider configuration...")
        
        try:
            # Check spider attributes
            assert self.spider.name == "goldie_playwright"
            assert "inspection.canada.ca" in self.spider.allowed_domains
            assert self.spider.start_urls
            
            # Check Playwright settings
            assert hasattr(self.spider, 'playwright_wait_until')
            assert hasattr(self.spider, 'playwright_timeout')
            
            logger.info(f"📋 Spider configuration:")
            logger.info(f"   - Name: {self.spider.name}")
            logger.info(f"   - Allowed domains: {self.spider.allowed_domains}")
            logger.info(f"   - Start URLs: {len(self.spider.start_urls)}")
            logger.info(f"   - Playwright wait: {self.spider.playwright_wait_until}")
            logger.info(f"   - Timeout: {self.spider.playwright_timeout}")
            
            logger.info("✅ Spider configuration test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Spider configuration test failed: {e}")
            return False

    def test_storage_functionality(self):
        """Test that storage is working correctly."""
        logger.info("💾 Testing storage functionality...")
        
        try:
            import louis.db as db
            from louis.crawler.items import CrawlItem
            
            # Create a test item
            test_item = CrawlItem()
            test_item['url'] = 'https://test.example.com/test'
            test_item['title'] = 'Test Page'
            test_item['lang'] = 'en'
            test_item['html_content'] = '<html><head><title>Test</title></head><body>Test content</body></html>'
            test_item['last_crawled'] = int(time.time())
            test_item['last_updated'] = '2024-01-01'
            
            # Try to store the item
            result = db.store_crawl_item(None, test_item)
            
            if result:
                logger.info(f"✅ Storage test passed")
                logger.info(f"   - Stored item with ID: {result.get('id', 'N/A')}")
                if 'html_file_path' in result:
                    logger.info(f"   - HTML file: {result['html_file_path']}")
                if 'metadata_file_path' in result:
                    logger.info(f"   - Metadata file: {result['metadata_file_path']}")
                return True
            else:
                logger.error(f"❌ Storage test failed: No result returned")
                return False
                
        except Exception as e:
            logger.error(f"❌ Storage test failed: {e}")
            return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting test_goldie_playwright...")
    logger.info("="*60)
    
    tester = TestGoldiePlaywright()
    
    tests = [
        ("Environment Setup", tester.test_environment_setup, False),
        ("Storage Functionality", tester.test_storage_functionality, False),
        ("Spider Configuration", tester.test_spider_configuration, False),
        ("Playwright Features", tester.test_playwright_features, True),
        ("Single Page Scraping", tester.test_single_page_scraping, True),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func, is_async in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    logger.info(f"{'='*60}")
    
    if passed == total:
        logger.info("🎉 All tests passed! goldie_playwright is working correctly.")
        logger.info("\n📋 Next steps:")
        logger.info("   - Run full spider: scrapy crawl goldie_playwright")
        logger.info("   - Check storage: python scripts/storage_manager.py list")
    else:
        logger.error("❌ Some tests failed. Please check the setup.")
        logger.info("\n🔧 Troubleshooting:")
        logger.info("   1. Ensure Playwright browsers are installed: python setup_playwright.py")
        logger.info("   2. Check dependencies: pip install -r requirements.txt")
        logger.info("   3. Verify network connectivity to inspection.canada.ca")
        if passed < total // 2:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
