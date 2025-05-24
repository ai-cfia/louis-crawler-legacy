#!/usr/bin/env python3
"""
Example script showing how to run the parallel spider with shared logging.
All worker processes will write to the same log file with unique task IDs.

This script demonstrates the CrawlerProcess method.
You can also use the standard Scrapy CLI command:
    scrapy crawl goldie_playwright_parallel -a max_depth=2 -a num_workers=4
"""

import os
from scrapy.crawler import CrawlerProcess
from louis.crawler.spiders.goldie_playwright_parallel import GoldiePlaywrightParallelSpider

def main():
    print("=== Parallel Spider Example ===")
    print()
    print("Method 1: Using CrawlerProcess (this script)")
    print("Method 2: Using standard Scrapy CLI:")
    print("    scrapy crawl goldie_playwright_parallel -a max_depth=2 -a num_workers=4")
    print()
    print("Starting parallel crawler with timestamped logging...")
    print("Note: Log files now automatically include timestamps (format: _yyyymmddhhmmss)")
    print("Example: logs/scrapy_20250115153045.log, logs/crawler_parallel_20250115153045.log")
    print("You can still specify custom filenames if needed.")
    print()
    
    # Configure the spider settings
    settings = {
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,  # We handle concurrency with multiprocessing
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'ITEM_PIPELINES': {
            'louis.crawler.pipelines.JsonWriterPipeline': 300,
        },
        'FILES_STORE': './downloads',
        'TELNETCONSOLE_ENABLED': False,
        # Reduce Scrapy's own logging to avoid conflicts
        'LOG_LEVEL': 'WARNING',
    }
    
    # Create crawler process
    process = CrawlerProcess(settings)
    
    # Example 1: Use automatic timestamped filenames (recommended)
    print("Example 1: Using automatic timestamped filenames...")
    process.crawl(
        GoldiePlaywrightParallelSpider,
        max_depth=2,                           # Crawl up to depth 2
        num_workers=4,                         # Use 4 worker processes
        batch_size=8,                          # Process 8 URLs per batch
        # Files will be automatically timestamped:
        # - logs/scraped_urls_20250115153045.txt
        # - logs/pending_urls_20250115153045.txt  
        # - logs/errored_urls_20250115153045.txt
        # - logs/crawler_parallel_20250115153045.log
    )
    
    # Example 2: Use custom filenames (uncomment to use instead)
    # print("Example 2: Using custom filenames...")
    # process.crawl(
    #     GoldiePlaywrightParallelSpider,
    #     max_depth=2,                           # Crawl up to depth 2
    #     num_workers=4,                         # Use 4 worker processes
    #     batch_size=8,                          # Process 8 URLs per batch
    #     scraped_urls_file="logs/scraped_urls.txt",  # Custom filename
    #     pending_urls_file="logs/pending_urls.txt",  # Custom filename
    #     errored_urls_file="logs/errored_urls.txt",  # Custom filename
    #     log_file="logs/crawler_parallel.log"        # Custom filename
    # )
    
    # Start crawling
    process.start()

if __name__ == "__main__":
    main()
