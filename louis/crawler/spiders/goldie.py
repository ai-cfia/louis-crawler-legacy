import re
import time
import scrapy
from bs4 import BeautifulSoup, Comment

from louis.crawler.items import CrawlItem
from louis.crawler.requests import extract_urls, fix_vhost


def convert_to_crawl_item(response):
    title = " ".join([t.get() for t in response.xpath("//title/text()")])
    title = re.sub(r'\s+', ' ', title).strip()
    last_updated =  response.xpath("//time/text()").get()
    content = clean(response)
    url = fix_vhost(response.url)
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
    main = response.css('main')
    main.css('aside').drop()
    main.css('.pagedetails').drop()
    main.css('script').drop()
    main.css('.nojs-hide').drop()
    main.css('.alert').drop()
    soup = BeautifulSoup(main.get(), "lxml")
    # remove comments
    _ignored = [c.extract() for c in soup.findAll(string=lambda text:isinstance(text, Comment))]
    content = str(soup)
    return re.sub(r'\s+', ' ', content).strip()

class GoldieSpider(scrapy.Spider):
    """crawl through the page, extracting chunks and urls"""
    name = "goldie"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/splash"]

    def parse(self, response):
        yield from convert_to_crawl_item(response)
        yield from extract_urls(response, self.parse)
