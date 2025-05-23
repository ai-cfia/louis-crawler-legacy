"""
Base spider classes for Playwright-enabled web scraping.
"""
import scrapy
from scrapy import Request
from typing import Optional, Dict, Any, List
import time
import re
from bs4 import BeautifulSoup, Comment

from louis.crawler.items import CrawlItem
from louis.crawler.requests import extract_urls, fix_vhost


class PlaywrightSpider(scrapy.Spider):
    """Base spider class with Playwright integration for JavaScript-rendered content."""
    
    # Enable Playwright for this spider
    use_playwright = True
    
    # Default Playwright settings
    playwright_wait_until = 'networkidle'  # or 'load', 'domcontentloaded', 'networkidle'
    playwright_timeout = 30000  # 30 seconds
    playwright_block_resources = True  # Block images, fonts, stylesheets for faster loading
    playwright_wait_time = 2  # Additional wait time in seconds
    
    def make_playwright_request(self, url: str, callback=None, **kwargs) -> Request:
        """Create a Scrapy request that will be handled by Playwright."""
        meta = {
            'playwright': True,
            'playwright_wait_until': kwargs.get('wait_until', self.playwright_wait_until),
            'playwright_timeout': kwargs.get('timeout', self.playwright_timeout),
            'playwright_block_resources': kwargs.get('block_resources', self.playwright_block_resources),
            'playwright_wait_time': kwargs.get('wait_time', self.playwright_wait_time),
        }
        
        # Optional: wait for specific selector
        if 'wait_for_selector' in kwargs:
            meta['playwright_wait_for_selector'] = kwargs['wait_for_selector']
            meta['playwright_selector_timeout'] = kwargs.get('selector_timeout', 10000)
        
        # Optional: wait for specific JavaScript function
        if 'wait_for_function' in kwargs:
            meta['playwright_wait_for_function'] = kwargs['wait_for_function']
            meta['playwright_function_timeout'] = kwargs.get('function_timeout', 10000)
        
        # Additional headers
        if 'headers' in kwargs:
            meta['headers'] = kwargs['headers']
        
        # Merge external meta with internal meta
        if 'meta' in kwargs:
            meta.update(kwargs['meta'])
        
        return Request(
            url=url,
            callback=callback or self.parse,
            meta=meta,
            **{k: v for k, v in kwargs.items() if k not in [
                'wait_until', 'timeout', 'block_resources', 'wait_time',
                'wait_for_selector', 'selector_timeout', 'wait_for_function',
                'function_timeout', 'headers', 'meta'
            ]}
        )
    
    def make_regular_request(self, url: str, callback=None, **kwargs) -> Request:
        """Create a regular Scrapy request (no Playwright)."""
        return Request(
            url=url,
            callback=callback or self.parse,
            **kwargs
        )
    
    def convert_to_crawl_item(self, response) -> CrawlItem:
        """Convert response to CrawlItem - can be overridden by subclasses."""
        title = " ".join([t.get() for t in response.xpath("//title/text()")])
        title = re.sub(r'\s+', ' ', title).strip()
        last_updated = response.xpath("//time/text()").get()
        content = self.clean_content(response)
        url = fix_vhost(response.url)
        now = int(time.time())
        lang = self.detect_language(url)
        
        return CrawlItem({
            'url': url,
            'title': title,
            'lang': lang,
            'html_content': content,
            'last_crawled': now,
            'last_updated': last_updated
        })
    
    def clean_content(self, response) -> str:
        """Clean and extract main content from response - can be overridden."""
        # Try to find main content area
        main = response.css('main')
        if not main:
            main = response.css('article')
        if not main:
            main = response.css('.content, #content, .main-content, #main-content')
        if not main:
            main = response  # Use full response if no main content area found
        
        # Remove unwanted elements
        main.css('aside').drop()
        main.css('script').drop()
        main.css('style').drop()
        main.css('.pagedetails').drop()
        main.css('.nojs-hide').drop()
        main.css('.alert').drop()
        main.css('nav').drop()
        main.css('header').drop()
        main.css('footer').drop()
        
        # Use BeautifulSoup for additional cleaning
        soup = BeautifulSoup(main.get(), "lxml")
        
        # Remove comments
        for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove empty elements
        for element in soup.find_all():
            if not element.get_text(strip=True) and not element.find('img'):
                element.decompose()
        
        content = str(soup)
        return re.sub(r'\s+', ' ', content).strip()
    
    def detect_language(self, url: str) -> str:
        """Detect language from URL - can be overridden."""
        if '/fra/' in url or '/fr/' in url:
            return 'fr'
        return 'en'
    
    def parse(self, response):
        """Default parse method - should be overridden by subclasses."""
        yield self.convert_to_crawl_item(response)
        yield from extract_urls(response, self.parse)


class SmartPlaywrightSpider(PlaywrightSpider):
    """
    Smart spider that automatically decides whether to use Playwright or regular requests
    based on content analysis.
    """
    
    # Enable both modes
    use_playwright = False  # Start with regular requests
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.playwright_urls = set()  # URLs that need Playwright
        self.regular_urls = set()     # URLs that work with regular requests
    
    def start_requests(self):
        """Generate initial requests."""
        for url in self.start_urls:
            yield self.make_regular_request(url, callback=self.parse_with_detection)
    
    def parse_with_detection(self, response):
        """Parse response and detect if Playwright is needed."""
        # Check if page seems to be missing content (indicators of JS rendering)
        content_indicators = self._analyze_content(response)
        
        if content_indicators['needs_js'] and response.url not in self.playwright_urls:
            self.logger.info(f"Detected JS-rendered content on {response.url}, retrying with Playwright")
            self.playwright_urls.add(response.url)
            yield self.make_playwright_request(
                response.url,
                callback=self.parse_playwright_response,
                wait_for_selector='body',  # Wait for basic page structure
                wait_time=3  # Give extra time for JS to execute
            )
        else:
            self.regular_urls.add(response.url)
            yield from self.parse_content(response)
    
    def parse_playwright_response(self, response):
        """Parse Playwright response."""
        yield from self.parse_content(response)
    
    def parse_content(self, response):
        """Parse the actual content."""
        yield self.convert_to_crawl_item(response)
        
        # Extract URLs and decide which method to use for each
        for url in self._extract_urls(response):
            if url in self.playwright_urls:
                yield self.make_playwright_request(url, callback=self.parse_playwright_response)
            elif url in self.regular_urls:
                yield self.make_regular_request(url, callback=self.parse_content)
            else:
                # First time seeing this URL, try regular request first
                yield self.make_regular_request(url, callback=self.parse_with_detection)
    
    def _analyze_content(self, response) -> Dict[str, Any]:
        """Analyze response to determine if JavaScript rendering is needed."""
        text_content = response.text
        
        # Indicators that JavaScript might be needed
        indicators = {
            'needs_js': False,
            'reasons': []
        }
        
        # Check for minimal content
        main_content = response.css('main, article, .content, #content').get()
        if main_content:
            text_length = len(BeautifulSoup(main_content, 'html.parser').get_text(strip=True))
        else:
            text_length = len(response.css('body').get_text())
        
        if text_length < 500:  # Very little content
            indicators['needs_js'] = True
            indicators['reasons'].append('minimal_content')
        
        # Check for loading indicators
        loading_patterns = [
            'loading...', 'please wait', 'loading content',
            'javascript is required', 'enable javascript',
            '<noscript>', 'document.ready', '$(document)',
            'window.onload', 'DOMContentLoaded'
        ]
        
        for pattern in loading_patterns:
            if pattern.lower() in text_content.lower():
                indicators['needs_js'] = True
                indicators['reasons'].append(f'loading_pattern: {pattern}')
                break
        
        # Check for React/Vue/Angular apps
        js_frameworks = [
            'react', 'vue', 'angular', 'ember',
            'data-reactroot', 'ng-app', 'v-app'
        ]
        
        for framework in js_frameworks:
            if framework.lower() in text_content.lower():
                indicators['needs_js'] = True
                indicators['reasons'].append(f'js_framework: {framework}')
                break
        
        return indicators
    
    def _extract_urls(self, response) -> List[str]:
        """Extract URLs from response."""
        urls = []
        for link in response.css('a::attr(href)').getall():
            if link and not link.startswith('#') and not link.startswith('mailto:'):
                absolute_url = response.urljoin(link)
                if self.allowed_domains:
                    domain = absolute_url.split('/')[2] if '://' in absolute_url else ''
                    if any(allowed in domain for allowed in self.allowed_domains):
                        urls.append(absolute_url)
                else:
                    urls.append(absolute_url)
        return urls
