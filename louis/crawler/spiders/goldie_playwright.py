"""
Playwright-enabled version of the goldie spider for JavaScript-rendered content.
"""
import re
import time
from louis.crawler.spiders.base_playwright import PlaywrightSpider, SmartPlaywrightSpider
from louis.crawler.items import CrawlItem
from louis.crawler.requests import extract_urls, fix_vhost


class GoldiePlaywrightSpider(PlaywrightSpider):
    """
    Goldie spider with full Playwright support for JavaScript-rendered content.
    Use this when you know the site heavily relies on JavaScript.
    """
    name = "goldie_playwright"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/en"]
    
    # Playwright settings specific to this site
    playwright_wait_until = 'networkidle'
    playwright_timeout = 30000
    playwright_wait_time = 3  # Wait 3 seconds for any final JS execution
    
    def start_requests(self):
        """Generate initial requests with Playwright."""
        for url in self.start_urls:
            yield self.make_playwright_request(
                url,
                callback=self.parse,
                wait_for_selector='main, body',  # Wait for main content area
                wait_time=5  # Extra wait for initial page
            )
    
    def parse(self, response):
        """Parse response and extract data."""
        self.logger.info(f"Parsing with Playwright: {response.url}")
        
        # Convert to crawl item
        yield self.convert_to_crawl_item(response)
        
        # Extract and follow links
        yield from self.extract_and_follow_urls(response)
    
    def extract_and_follow_urls(self, response):
        """Extract URLs and create new Playwright requests."""
        for link in response.css('a::attr(href)').getall():
            if link and not link.startswith('#') and not link.startswith('mailto:'):
                absolute_url = response.urljoin(link)
                
                # Check if URL is in allowed domains
                if self.allowed_domains:
                    domain = absolute_url.split('/')[2] if '://' in absolute_url else ''
                    if any(allowed in domain for allowed in self.allowed_domains):
                        yield self.make_playwright_request(
                            absolute_url,
                            callback=self.parse,
                            wait_for_selector='main',
                            wait_time=2
                        )
    
    def clean_content(self, response) -> str:
        """Custom content cleaning for goldie spider."""
        # Find main content area
        main = response.css('main')
        if main:
            # Remove unwanted sections
            main.css('aside').drop()
            main.css('.pagedetails').drop()
            main.css('script').drop()
            main.css('.nojs-hide').drop()
            main.css('.alert').drop()
            main.css('nav').drop()
            main.css('header').drop()
            main.css('footer').drop()
            
            content = main.get()
        else:
            # Fallback to body if no main element
            content = response.css('body').get()
        
        if content:
            # Use BeautifulSoup for final cleaning
            from bs4 import BeautifulSoup, Comment
            soup = BeautifulSoup(content, "lxml")
            
            # Remove comments
            for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            content = str(soup)
            return re.sub(r'\s+', ' ', content).strip()
        
        return ""


class GoldieSmartSpider(SmartPlaywrightSpider):
    """
    Smart goldie spider that automatically detects when to use Playwright.
    This is more efficient as it only uses Playwright when necessary.
    """
    name = "goldie_smart"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/en"]
    
    def clean_content(self, response) -> str:
        """Custom content cleaning for goldie spider."""
        # Find main content area
        main = response.css('main')
        if main:
            # Remove unwanted sections
            main.css('aside').drop()
            main.css('.pagedetails').drop()
            main.css('script').drop()
            main.css('.nojs-hide').drop()
            main.css('.alert').drop()
            
            content = main.get()
        else:
            # Fallback to body if no main element
            content = response.css('body').get()
        
        if content:
            # Use BeautifulSoup for final cleaning
            from bs4 import BeautifulSoup, Comment
            soup = BeautifulSoup(content, "lxml")
            
            # Remove comments
            for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            content = str(soup)
            return re.sub(r'\s+', ' ', content).strip()
        
        return ""
    
    def _analyze_content(self, response):
        """Custom content analysis for goldie spider."""
        indicators = super()._analyze_content(response)
        
        # Additional checks specific to inspection.canada.ca
        text_content = response.text.lower()
        
        # Check for specific patterns that indicate JS rendering
        if 'please enable javascript' in text_content:
            indicators['needs_js'] = True
            indicators['reasons'].append('js_disabled_message')
        
        # Check if main content area is mostly empty
        main_content = response.css('main').get()
        if main_content:
            main_text = response.css('main').get_text().strip()
            if len(main_text) < 200:  # Very little content in main
                indicators['needs_js'] = True
                indicators['reasons'].append('empty_main_content')
        
        return indicators


class GoldieHybridSpider(PlaywrightSpider):
    """
    Hybrid spider that uses both regular requests and Playwright strategically.
    You can manually control which URLs use Playwright.
    """
    name = "goldie_hybrid"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/en"]
    
    # Define URL patterns that need Playwright
    playwright_url_patterns = [
        r'.*search.*',      # Search pages likely use JS
        r'.*ajax.*',        # AJAX endpoints
        r'.*api.*',         # API endpoints
        r'.*dynamic.*',     # Dynamic content
    ]
    
    def start_requests(self):
        """Generate initial requests."""
        for url in self.start_urls:
            if self._needs_playwright(url):
                yield self.make_playwright_request(url, callback=self.parse)
            else:
                yield self.make_regular_request(url, callback=self.parse)
    
    def parse(self, response):
        """Parse response and extract data."""
        yield self.convert_to_crawl_item(response)
        yield from self.extract_and_follow_urls(response)
    
    def extract_and_follow_urls(self, response):
        """Extract URLs and create appropriate requests."""
        for link in response.css('a::attr(href)').getall():
            if link and not link.startswith('#') and not link.startswith('mailto:'):
                absolute_url = response.urljoin(link)
                
                # Check if URL is in allowed domains
                if self.allowed_domains:
                    domain = absolute_url.split('/')[2] if '://' in absolute_url else ''
                    if any(allowed in domain for allowed in self.allowed_domains):
                        if self._needs_playwright(absolute_url):
                            yield self.make_playwright_request(
                                absolute_url,
                                callback=self.parse,
                                wait_for_selector='main',
                                wait_time=2
                            )
                        else:
                            yield self.make_regular_request(absolute_url, callback=self.parse)
    
    def _needs_playwright(self, url: str) -> bool:
        """Determine if URL needs Playwright based on patterns."""
        for pattern in self.playwright_url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def clean_content(self, response) -> str:
        """Custom content cleaning for goldie spider."""
        return GoldiePlaywrightSpider.clean_content(self, response)
