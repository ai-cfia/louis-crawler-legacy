# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import louis.db as db
import louis.db.crawler as crawler

class LouisPipeline:
    """Pipeline for storing items in the database"""
    def open_spider(self, _spider):
        """open connection to the database"""
        self.connection = db.connect_db()

    def close_spider(self, _spider):
        """close connection to database"""
        self.connection.close()

    def process_item(self, item, spider):
        """process item and store in database"""
        try:
            if spider.name == 'goldie':
                with db.cursor(self.connection) as cursor:
                    return crawler.store_crawl_item(cursor, item)
            elif spider.name in ['hawn', 'russell']:
                with db.cursor(self.connection) as cursor:
                    return crawler.store_chunk_item(cursor, item)
            elif spider.name == 'kurt':
                with db.cursor(self.connection) as cursor:
                    return crawler.store_embedding_item(cursor, item)
        except db.DBError:
            # spider.logger.error("Error storing item", exc_info=True)
            self.connection.rollback()
            raise