#!/usr/bin/env python3
"""
Simple test for goldie_playwright spider - tests scraping one page only.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from louis.crawler.spiders.goldie_playwright import GoldiePlaywrightSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def test_single_page():
    """Test scraping a single page with goldie_playwright spider."""
    print("🕷️  Testing goldie_playwright spider with single page...")
    
    # Get project settings
    settings = get_project_settings()
    
    # Override settings for single page test
    settings.update({
        'CLOSESPIDER_PAGECOUNT': 1,  # Stop after 1 page
        'DOWNLOAD_DELAY': 0,  # No delay for testing
        'CONCURRENT_REQUESTS': 1,  # One request at a time
        'LOG_LEVEL': 'INFO',  # Show info logs
        'AUTOTHROTTLE_ENABLED': True,
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'ITEM_PIPELINES': {
            'louis.crawler.pipelines.LouisPipeline': 300,
        },
        # Use the built-in Playwright middleware instead of external scrapy-playwright
        'DOWNLOADER_MIDDLEWARES': {
            "louis.crawler.playwright_middleware.PlaywrightMiddleware": 585,
            "louis.crawler.middlewares.LouisDownloaderMiddleware": 543,
        },
        # Fix the deprecation warning
        'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7',
    })
    
    # Create spider with custom start URL for testing
    spider_class = GoldiePlaywrightSpider
    spider_class.start_urls = ["https://inspection.canada.ca/en"]
    spider_class.custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 1,
    }
    
    # Create and run crawler
    process = CrawlerProcess(settings)
    process.crawl(spider_class)
    
    print("🚀 Starting single page test...")
    print("📄 Target URL: https://inspection.canada.ca/en")
    print("💾 Storage: ./test_storage")
    
    try:
        process.start()
        print("✅ Test completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_single_page()
