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


class DiskPipeline:
    """Pipeline for storing items directly to disk"""

    def open_spider(self, spider):
        """Initialize pipeline for disk storage"""
        print(f"📁 Pipeline: Disk storage mode initialized")

    def close_spider(self, spider):
        """Pipeline cleanup"""
        print(f"📁 Pipeline: Disk storage mode closed")

    def process_item(self, item, spider):
        """Process item and store to disk"""
        if spider.name in [
            "goldie",
            "test_goldie", 
            "goldie_playwright",
            "goldie_playwright_parallel",
        ]:
            try:
                result = db.store_to_disk(item)
                print(f"📁 Stored to disk: {item.get('url', 'unknown')}")
                return result
            except Exception as e:
                print(f"❌ Disk storage failed: {e}")
                return item
        elif spider.name == "hawn":
            # For chunk items, we need to handle disk storage
            # Note: The current db module doesn't have store_chunk_to_disk
            # but we can extend this as needed
            print(f"⚠️  Chunk items not yet supported for disk storage")
            return item
        elif spider.name == "kurt":
            # For embedding items, we need to handle disk storage
            # Note: The current db module doesn't have store_embedding_to_disk
            # but we can extend this as needed
            print(f"⚠️  Embedding items not yet supported for disk storage")
            return item

        return item


class S3Pipeline:
    """Pipeline for storing items to S3"""

    def open_spider(self, spider):
        """Initialize pipeline for S3 storage"""
        try:
            # Verify S3 connection by checking configuration
            config = db.get_s3_config()
            client = db.get_s3_client()
            if client and config:
                print(f"☁️  Pipeline: S3 storage mode initialized (bucket: {config.get('bucket_name', 'unknown')})")
                self.s3_available = True
            else:
                print(f"⚠️  Pipeline: S3 not configured, falling back to disk")
                self.s3_available = False
        except Exception as e:
            print(f"⚠️  Pipeline: S3 initialization failed: {e}")
            print(f"📁 Pipeline: Falling back to disk storage")
            self.s3_available = False

    def close_spider(self, spider):
        """Pipeline cleanup"""
        if self.s3_available:
            print(f"☁️  Pipeline: S3 storage mode closed")
        else:
            print(f"📁 Pipeline: Disk fallback mode closed")

    def process_item(self, item, spider):
        """Process item and store to S3 with disk fallback"""
        if spider.name in [
            "goldie",
            "test_goldie",
            "goldie_playwright", 
            "goldie_playwright_parallel",
        ]:
            if self.s3_available:
                try:
                    result = db.store_to_s3(item)
                    print(f"☁️  Stored to S3: {item.get('url', 'unknown')}")
                    return result
                except Exception as e:
                    print(f"⚠️  S3 storage failed, falling back to disk: {e}")
                    try:
                        result = db.store_to_disk(item)
                        print(f"📁 Stored to disk (fallback): {item.get('url', 'unknown')}")
                        return result
                    except Exception as disk_error:
                        print(f"❌ Both S3 and disk storage failed: {disk_error}")
                        return item
            else:
                # S3 not available, use disk directly
                try:
                    result = db.store_to_disk(item)
                    print(f"📁 Stored to disk (S3 unavailable): {item.get('url', 'unknown')}")
                    return result
                except Exception as e:
                    print(f"❌ Disk storage failed: {e}")
                    return item
        elif spider.name == "hawn":
            # For chunk items, we need to handle S3 storage
            # Note: The current db module doesn't have store_chunk_to_s3
            # but we can extend this as needed
            print(f"⚠️  Chunk items not yet supported for S3 storage")
            return item
        elif spider.name == "kurt":
            # For embedding items, we need to handle S3 storage  
            # Note: The current db module doesn't have store_embedding_to_s3
            # but we can extend this as needed
            print(f"⚠️  Embedding items not yet supported for S3 storage")
            return item

        return item
