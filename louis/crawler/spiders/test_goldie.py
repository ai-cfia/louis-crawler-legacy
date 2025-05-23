"""Test version of goldie spider for single page testing"""
import re
import time
import scrapy
from bs4 import BeautifulSoup, Comment

from louis.crawler.items import CrawlItem
# from louis.crawler.requests import extract_urls, fix_vhost


def convert_to_crawl_item(response):
    title = " ".join([t.get() for t in response.xpath("//title/text()")])
    title = re.sub(r'\s+', ' ', title).strip()
    last_updated =  response.xpath("//time/text()").get()
    content = clean(response)
    url = response.url  # Don't use fix_vhost for testing
    now = int(time.time())
    lang = 'en'
    if url.find('/fra/') != -1:
        lang = 'fr'

    yield CrawlItem({
        'url': url,
        'title': title,
        'lang': lang,
        'html_content': content,
        'last_crawled': now,
        'last_updated': last_updated
    })

def clean(response):
    """drop extraneous content from the page"""
    # Get the entire response body as a string if no main element exists
    body_html = response.text
    
    # Try to find main content
    main = response.css('main')
    if main:
        main.css('aside').drop()
        main.css('.pagedetails').drop()
        main.css('script').drop()
        main.css('.nojs-hide').drop()
        main.css('.alert').drop()
        soup = BeautifulSoup(main.get(), "lxml")
    else:
        # Fallback to body content and clean it
        soup = BeautifulSoup(body_html, "lxml")
        # Remove scripts, styles, and other unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
    
    # remove comments
    _ignored = [
        c.extract() for c in soup.findAll(
            string=lambda text:isinstance(text, Comment))]
    content = str(soup)
    return re.sub(r'\s+', ' ', content).strip()

class TestGoldieSpider(scrapy.Spider):
    """Test version of goldie spider - crawls only one page"""
    name = "test_goldie"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    
    # Use a simple test URL that we know will work
    start_urls = ["https://inspection.canada.ca/en"]
    
    # Custom settings to limit crawling and disable problematic middleware
    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 1,  # Stop after 1 page
        'DOWNLOAD_DELAY': 0,  # No delay for testing
        'CONCURRENT_REQUESTS': 1,  # One request at a time
        # Disable the problematic middleware and pipeline for testing
        'DOWNLOADER_MIDDLEWARES': {},
        'ITEM_PIPELINES': {
            'louis.crawler.pipelines.LouisPipeline': 300,
        },
    }

    def parse(self, response):
        print(f"🕷️  Crawling: {response.url}")
        print(f"📄 Response status: {response.status}")
        print(f"📊 Content length: {len(response.text)} characters")
        
        yield from convert_to_crawl_item(response)
        
        # Don't follow links for this test
        print("✅ Single page test completed - not following links") 