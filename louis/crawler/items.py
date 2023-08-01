# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlItem(scrapy.Item):
    """Item for storing crawl data"""
    id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    lang = scrapy.Field()
    html_content = scrapy.Field()
    last_crawled = scrapy.Field()
    last_updated = scrapy.Field()

class ChunkItem(scrapy.Item):
    """Item for storing chunk data"""
    url = scrapy.Field()
    title = scrapy.Field()
    text_content = scrapy.Field()
    token_count = scrapy.Field()
    tokens = scrapy.Field()

class EmbeddingItem(scrapy.Item):
    """Item for storing embedding data"""
    token_id = scrapy.Field()
    embedding = scrapy.Field()
    embedding_model = scrapy.Field()

    def __repr__(self):
        """Return a string representation of the item"""
        return f"EmbeddingItem(token_id={self['token_id']}, embedding_model={self['embedding_model']})"