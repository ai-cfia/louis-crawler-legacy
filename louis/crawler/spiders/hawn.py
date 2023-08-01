import re
import time
import scrapy
from bs4 import BeautifulSoup, Comment

from louis.crawler.items import ChunkItem
from louis.crawler.requests import extract_urls
from louis.crawler.chunking import chunk_html


def convert_to_chunk_items(response):
    soup, chunks = chunk_html(response.body)
    for chunk in chunks:
        yield ChunkItem(
            {
                "url": response.url,
                "title": chunk['title'],
                "text_content": chunk['text_content'],
                "token_count": chunk['token_count'],
                "tokens": chunk['tokens'],
            }
        )


class HawnSpider(scrapy.Spider):
    name = "hawn"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/splash"]

    def parse(self, response):
        yield from convert_to_chunk_items(response)
        yield from extract_urls(response, self.parse)
