import unittest

import ailab.db as db


class TestDBLayer(unittest.TestCase):
    def setUp(self):
        self.connection = db.connect_db()

    def tearDown(self):
        self.connection.close()

    # def test_store_embedding_item(self):
    #     """sample test to check if store_embedding_item works"""
    #     with db.cursor(self.connection) as cursor:
    #         crawler.store_embedding_item(cursor, items.EmbeddingItem({
    #             "token_id": "00000000-0000-0000-0000-000000000000",
    #             "embedding": list(range(0, 1536)),
    #             "embedding_model": "ada_002"
    #         }))
    #         self.connection.rollback()

    # def test_store_chunk_item(self):
    #     """sample test to check if store_chunk_item works"""""
    #     with db.cursor(self.connection) as cursor:
    #         crawler.store_chunk_item(cursor, items.ChunkItem({
    #             "url": "https://inspection.canada.ca/a-propos-de-l-acia/contactez-nous/fra/1546627816321/1546627838025",
    #             "title": "Test Title",
    #             "text_content": "Test Text Content",
    #             "token_count": 3,
    #             "tokens": [1, 2, 3],
    #         }))
    #         self.connection.rollback()

    # def test_store_crawl_item(self):
    #     """sample test to check if store_crawl_item work"""
    #     with db.cursor(self.connection) as cursor:
    #         crawler.store_crawl_item(cursor, items.CrawlItem({
    #             "url": "https://inspection.canada.ca/a-propos-de-l-acia/contactez-nous/fra/1546627816321/1546627838025",
    #             "title": "Test Title",
    #             "lang": "fr",
    #             "html_content": "<html><body><p>Test Text Content</p></body></html>",
    #             "last_updated": "2023-06-01",
    #             "last_crawled": time.time()
    #         }))
    #         self.connection.rollback()
