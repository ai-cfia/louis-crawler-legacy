# Playwright Integration for Louis Crawler

This document explains how to use Playwright with the Louis crawler to handle JavaScript-rendered content that traditional Scrapy + BeautifulSoup might miss.

## Overview

Playwright is a browser automation library that can execute JavaScript and wait for dynamic content to load. This is essential for modern websites that heavily rely on client-side JavaScript to render content.

## Installation

1. Install the new dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
python setup_playwright.py
```

Or manually:
```bash
python -m playwright install chromium firefox webkit
python -m playwright install-deps
```

## Spider Types

### 1. PlaywrightSpider (Full Playwright)

Use this when you know the entire site relies heavily on JavaScript.

```python
from louis.crawler.spiders.base_playwright import PlaywrightSpider

class MyPlaywrightSpider(PlaywrightSpider):
    name = "my_playwright_spider"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]
    
    def start_requests(self):
        for url in self.start_urls:
            yield self.make_playwright_request(
                url,
                callback=self.parse,
                wait_for_selector='.content',
                wait_time=3
            )
```

### 2. SmartPlaywrightSpider (Automatic Detection)

Use this when you want the spider to automatically detect when Playwright is needed.

```python
from louis.crawler.spiders.base_playwright import SmartPlaywrightSpider

class MySmartSpider(SmartPlaywrightSpider):
    name = "my_smart_spider"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]
    
    # No need to specify which requests use Playwright
    # The spider will detect automatically
```

### 3. Hybrid Approach

Manually control which URLs use Playwright based on patterns.

```python
class MyHybridSpider(PlaywrightSpider):
    name = "my_hybrid_spider"
    
    playwright_url_patterns = [
        r'.*search.*',
        r'.*ajax.*',
        r'.*api.*'
    ]
    
    def _needs_playwright(self, url):
        for pattern in self.playwright_url_patterns:
            if re.search(pattern, url):
                return True
        return False
```

## Playwright Request Options

When creating Playwright requests, you can use these options:

```python
yield self.make_playwright_request(
    url,
    callback=self.parse,
    # Wait conditions
    wait_until='networkidle',  # 'load', 'domcontentloaded', 'networkidle'
    timeout=30000,  # 30 seconds
    wait_time=3,  # Additional wait time in seconds
    
    # Wait for specific elements
    wait_for_selector='.content',
    selector_timeout=10000,
    
    # Wait for JavaScript function
    wait_for_function='() => document.readyState === "complete"',
    function_timeout=10000,
    
    # Performance optimization
    block_resources=True,  # Block images, fonts, stylesheets
    
    # Custom headers
    headers={'User-Agent': 'Custom Agent'}
)
```

## Configuration

Configure Playwright in `settings.py`:

```python
# Playwright settings
PLAYWRIGHT_BROWSER_TYPE = 'chromium'  # 'chromium', 'firefox', 'webkit'
PLAYWRIGHT_HEADLESS = True
PLAYWRIGHT_BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
]
```

## Examples

### Example 1: Government Site with Dynamic Content

```python
class GoldiePlaywrightSpider(PlaywrightSpider):
    name = "goldie_playwright"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/splash"]
    
    def start_requests(self):
        for url in self.start_urls:
            yield self.make_playwright_request(
                url,
                wait_for_selector='main',
                wait_time=5
            )
```

### Example 2: E-commerce Site with Lazy Loading

```python
class EcommerceSpider(PlaywrightSpider):
    name = "ecommerce"
    
    def parse_product_list(self, response):
        # Wait for all products to load
        yield self.make_playwright_request(
            response.url,
            callback=self.parse_products,
            wait_for_function='() => document.querySelectorAll(".product").length > 10',
            wait_time=2
        )
```

### Example 3: SPA (Single Page Application)

```python
class SPASpider(PlaywrightSpider):
    name = "spa_spider"
    
    def parse_spa(self, response):
        # Wait for React/Vue app to render
        yield self.make_playwright_request(
            response.url,
            callback=self.parse_content,
            wait_for_selector='[data-reactroot], #app',
            wait_for_function='() => window.appLoaded === true',
            wait_time=5
        )
```

## Running Spiders

```bash
# Run the full Playwright spider
scrapy crawl goldie_playwright

# Run the smart spider (automatic detection)
scrapy crawl goldie_smart

# Run the hybrid spider
scrapy crawl goldie_hybrid

# Run with custom settings
scrapy crawl goldie_playwright -s PLAYWRIGHT_HEADLESS=False
```

## Performance Considerations

1. **Resource Blocking**: Enable `block_resources=True` to block images, fonts, and stylesheets for faster loading.

2. **Selective Usage**: Use SmartPlaywrightSpider or Hybrid approach to only use Playwright when necessary.

3. **Timeout Management**: Set appropriate timeouts to avoid hanging on slow pages.

4. **Concurrent Requests**: Reduce `CONCURRENT_REQUESTS` when using Playwright extensively:
```python
CONCURRENT_REQUESTS = 2  # Lower for Playwright spiders
```

## Troubleshooting

### Common Issues

1. **Browser not found**: Run `python setup_playwright.py` to install browsers.

2. **Permission errors**: Make sure you have the necessary permissions for browser installation.

3. **Memory issues**: Reduce concurrent requests and enable resource blocking.

4. **Timeout errors**: Increase timeouts for slow-loading pages.

### Debug Mode

Run with visible browser for debugging:
```bash
scrapy crawl my_spider -s PLAYWRIGHT_HEADLESS=False
```

### Logging

Enable debug logging:
```python
import logging
logging.getLogger('playwright').setLevel(logging.DEBUG)
```

## Best Practices

1. **Start Small**: Begin with SmartPlaywrightSpider to see which pages need JavaScript rendering.

2. **Monitor Performance**: Keep track of crawl speed and adjust settings accordingly.

3. **Resource Management**: Always enable resource blocking unless you specifically need images/CSS.

4. **Error Handling**: The middleware gracefully falls back to regular Scrapy if Playwright fails.

5. **Testing**: Test your spiders with both regular and Playwright modes to ensure they work correctly.

## Migration from Existing Spiders

To migrate an existing spider to use Playwright:

1. Import the base classes:
```python
from louis.crawler.spiders.base_playwright import SmartPlaywrightSpider
```

2. Change the parent class:
```python
class MySpider(SmartPlaywrightSpider):  # Instead of scrapy.Spider
```

3. Test the spider to see which pages need Playwright

4. Optionally customize the detection logic in `_analyze_content()`

This approach allows you to maintain your existing spider logic while adding JavaScript rendering capabilities where needed.
