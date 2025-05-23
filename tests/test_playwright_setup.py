#!/usr/bin/env python3
"""
Test script to validate Playwright setup with the Louis crawler.
"""
import asyncio
import sys
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_playwright_basic():
    """Test basic Playwright functionality."""
    logger.info("Testing basic Playwright functionality...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Test with a simple page
            await page.goto('https://httpbin.org/html')
            title = await page.title()
            
            logger.info(f"Successfully loaded page with title: {title}")
            
            # Test JavaScript execution
            result = await page.evaluate('() => document.title')
            logger.info(f"JavaScript execution test: {result}")
            
            await browser.close()
            logger.info("✅ Basic Playwright test passed")
            return True
            
    except Exception as e:
        logger.error(f"❌ Basic Playwright test failed: {e}")
        return False


async def test_government_site():
    """Test with the actual government site."""
    logger.info("Testing with inspection.canada.ca...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Test the actual site
            await page.goto('https://inspection.canada.ca/en', timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            title = await page.title()
            content = await page.content()
            
            logger.info(f"Site title: {title}")
            logger.info(f"Content length: {len(content)} characters")
            
            # Check for main content
            main_elements = await page.query_selector_all('main')
            logger.info(f"Found {len(main_elements)} main elements")
            
            await browser.close()
            logger.info("✅ Government site test passed")
            return True
            
    except Exception as e:
        logger.error(f"❌ Government site test failed: {e}")
        return False


def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing imports...")
    
    try:
        # Test Playwright import
        import playwright
        try:
            from playwright import __version__ as pw_version
            logger.info(f"✅ Playwright version: {pw_version}")
        except ImportError:
            logger.info("✅ Playwright imported successfully (version detection unavailable)")
        
        # Test scrapy-playwright import
        import scrapy_playwright
        logger.info(f"✅ Scrapy-Playwright imported successfully")
        
        # Test our custom modules
        from louis.crawler.playwright_middleware import PlaywrightMiddleware
        logger.info("✅ PlaywrightMiddleware imported successfully")
        
        from louis.crawler.spiders.base_playwright import PlaywrightSpider, SmartPlaywrightSpider
        logger.info("✅ Playwright spider classes imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting Playwright setup validation...")
    
    tests = [
        ("Import Test", test_imports, False),  # Sync test
        ("Basic Playwright Test", test_playwright_basic, True),  # Async test
        ("Government Site Test", test_government_site, True),  # Async test
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func, is_async in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
                
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Playwright is ready to use.")
        logger.info("\nYou can now run:")
        logger.info("  scrapy crawl goldie_smart")
        logger.info("  scrapy crawl goldie_playwright")
        logger.info("  scrapy crawl goldie_hybrid")
    else:
        logger.error("❌ Some tests failed. Please check the setup.")
        logger.info("\nTroubleshooting:")
        logger.info("1. Run: python setup_playwright.py")
        logger.info("2. Check that all dependencies are installed: pip install -r requirements.txt")
        logger.info("3. Check the documentation: docs/playwright_integration.md")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
