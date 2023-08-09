
import scrapy

import louis.db as db

from louis.db.crawler import fetch_crawl_ids_without_chunk
from louis.crawler.convert import convert_html_content_to_chunk_items

class RussellSpider(scrapy.Spider):
    name = "russell"

    def __init__(self, category=None, *args, **kwargs):
        super(RussellSpider, self).__init__(*args, **kwargs)
        self.connection = db.connect_db()
        self.dbname = self.connection.info.dbname

    def spider_closed(self, spider):
        self.connection.close()

    def start_requests(self):
        with db.cursor(self.connection) as cursor:
            crawl_ids = fetch_crawl_ids_without_chunk(cursor)
        # for crawl_id in crawl_ids:
        #     url = db.create_postgresql_url(self.dbname, 'crawl', crawl_id)
        #     yield scrapy.Request(url=url, callback=self.parse)
        url = db.create_postgresql_url(self.dbname, 'crawl', crawl_ids[0])
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        yield from convert_html_content_to_chunk_items(response.url, response.body)