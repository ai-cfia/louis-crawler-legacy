import unittest

import louis.crawler.items as items

import time

import louis.db as db
import louis.db.crawler as crawler

class TestDBLayer(unittest.TestCase):
    def setUp(self):
        self.connection = db.connect_db()
        self.dbname = self.connection.info.dbname

    def tearDown(self):
        self.connection.close()

    def test_store_embedding_item(self):
        """sample test to check if store_embedding_item works"""
        with db.cursor(self.connection) as cursor:
            crawler.store_embedding_item(cursor, items.EmbeddingItem({
                "token_id": "00000000-0000-0000-0000-000000000000",
                "embedding": list(range(0, 1536)),
                "embedding_model": "ada_002"
            }))
            self.connection.rollback()

    def test_store_chunk_item(self):
        """sample test to check if store_chunk_item works"""""
        with db.cursor(self.connection) as cursor:
            crawler.store_chunk_item(cursor, items.ChunkItem({
                "url": "https://inspection.canada.ca/a-propos-de-l-acia/contactez-nous/fra/1546627816321/1546627838025",
                "title": "Test Title",
                "text_content": "Test Text Content",
                "token_count": 3,
                "tokens": [1, 2, 3],
            }))
            self.connection.rollback()

    def test_store_crawl_item(self):
        """sample test to check if store_crawl_item work"""
        with db.cursor(self.connection) as cursor:
            crawler.store_crawl_item(cursor, items.CrawlItem({
                "url": "https://inspection.canada.ca/a-propos-de-l-acia/contactez-nous/fra/1546627816321/1546627838025",
                "title": "Test Title",
                "lang": "fr",
                "html_content": "<html><body><p>Test Text Content</p></body></html>",
                "last_updated": "2023-06-01",
                "last_crawled": time.time()
            }))
            self.connection.rollback()

    def test_fetch_crawl_ids_without_chunk(self):
        """sample test to check if fetch_crawl_ids_without_chunk works"""
        with db.cursor(self.connection) as cursor:
            # in RussellSpider start_requests
            crawl_ids = crawler.fetch_crawl_ids_without_chunk(cursor)
            url = db.create_postgresql_url(self.dbname, 'crawl', crawl_ids[0])
            # in LouisDownloaderMiddleware process_request
            row =  crawler.fetch_crawl_row(cursor, url)
            self.connection.rollback()

    def test_store_chunk_item2(self):
        """sample test to check if store_chunk_item works"""""
        import objects.chunk as chunk
        with db.cursor(self.connection) as cursor:
            crawler.store_chunk_item(cursor, items.ChunkItem(chunk.example1))
            self.connection.rollback()