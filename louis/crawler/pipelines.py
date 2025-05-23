# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import louis.db as db


class LouisPipeline:
    """Pipeline for storing items in the database"""

    def open_spider(self, spider):
        """open connection to the database"""
        try:
            self.connection = db.connect_db()
            print(f"✅ Pipeline: Database connection established")
        except Exception as e:
            print(f"⚠️  Pipeline: Database connection failed: {e}")
            self.connection = None
            print(f"📁 Pipeline: Using disk storage mode")

    def close_spider(self, spider):
        """close connection to database"""
        if self.connection:
            self.connection.close()
            print(f"✅ Pipeline: Database connection closed")

    def process_item(self, item, spider):
        """process item and store in database"""
        if spider.name in [
            "goldie",
            "test_goldie",
            "goldie_playwright",
            "goldie_playwright_parallel",
        ]:
            try:
                with db.cursor(self.connection) as cursor:
                    result = db.store_crawl_item(cursor, item)
                    print(f"✅ Stored item: {item.get('url', 'unknown')}")
                    return result
            except Exception as e:
                print(f"⚠️  Storage error: {e}")
                # The store_crawl_item function should handle disk storage fallback
                try:
                    result = db.store_crawl_item(None, item)
                    print(f"📁 Stored to disk: {item.get('url', 'unknown')}")
                    return result
                except Exception as disk_error:
                    print(f"❌ Disk storage also failed: {disk_error}")
                    return item
        elif spider.name == "hawn":
            with db.cursor(self.connection) as cursor:
                return db.store_chunk_item(cursor, item)
        elif spider.name == "kurt":
            with db.cursor(self.connection) as cursor:
                return db.store_embedding_item(cursor, item)

        return item
