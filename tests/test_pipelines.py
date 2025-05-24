"""
Unit tests for Louis Crawler pipelines.

Tests the DiskPipeline and S3Pipeline classes to ensure they handle
items correctly and provide appropriate fallback behavior.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import shutil

from louis.crawler.pipelines import LouisPipeline, DiskPipeline, S3Pipeline
from louis.crawler.items import CrawlItem


class TestDiskPipeline(unittest.TestCase):
    """Test the DiskPipeline class."""

    def setUp(self):
        """Set up test environment."""
        self.pipeline = DiskPipeline()
        self.mock_spider = Mock()
        self.mock_spider.name = "goldie"
        
        # Create a sample CrawlItem
        self.sample_item = CrawlItem()
        self.sample_item['url'] = 'https://example.com/test'
        self.sample_item['title'] = 'Test Title'
        self.sample_item['lang'] = 'en'
        self.sample_item['html_content'] = '<html><body><p>Test content</p></body></html>'
        self.sample_item['last_crawled'] = '2024-01-01T12:00:00'
        self.sample_item['last_updated'] = '2024-01-01T12:00:00'

    def test_open_spider(self):
        """Test pipeline initialization."""
        # Should not raise any errors
        self.pipeline.open_spider(self.mock_spider)

    def test_close_spider(self):
        """Test pipeline cleanup."""
        # Should not raise any errors
        self.pipeline.close_spider(self.mock_spider)

    @patch('louis.db.store_to_disk')
    def test_process_goldie_item_success(self, mock_store):
        """Test successful processing of goldie spider item."""
        # Mock successful storage
        mock_store.return_value = {
            'id': 'test-uuid',
            'url': self.sample_item['url'],
            'title': self.sample_item['title']
        }
        
        result = self.pipeline.process_item(self.sample_item, self.mock_spider)
        
        # Verify store_to_disk was called
        mock_store.assert_called_once_with(self.sample_item)
        
        # Verify result
        self.assertEqual(result['id'], 'test-uuid')
        self.assertEqual(result['url'], self.sample_item['url'])

    @patch('louis.db.store_to_disk')
    def test_process_goldie_item_failure(self, mock_store):
        """Test handling of storage failure for goldie spider item."""
        # Mock storage failure
        mock_store.side_effect = Exception("Storage failed")
        
        result = self.pipeline.process_item(self.sample_item, self.mock_spider)
        
        # Should return original item on failure
        self.assertEqual(result, self.sample_item)

    def test_process_unsupported_spider(self):
        """Test processing item from unsupported spider."""
        self.mock_spider.name = "hawn"
        
        result = self.pipeline.process_item(self.sample_item, self.mock_spider)
        
        # Should return original item unchanged
        self.assertEqual(result, self.sample_item)


class TestS3Pipeline(unittest.TestCase):
    """Test the S3Pipeline class."""

    def setUp(self):
        """Set up test environment."""
        self.pipeline = S3Pipeline()
        self.mock_spider = Mock()
        self.mock_spider.name = "goldie"
        
        # Create a sample CrawlItem
        self.sample_item = CrawlItem()
        self.sample_item['url'] = 'https://example.com/test'
        self.sample_item['title'] = 'Test Title'
        self.sample_item['lang'] = 'en'
        self.sample_item['html_content'] = '<html><body><p>Test content</p></body></html>'
        self.sample_item['last_crawled'] = '2024-01-01T12:00:00'
        self.sample_item['last_updated'] = '2024-01-01T12:00:00'

    @patch('louis.db.get_s3_config')
    @patch('louis.db.get_s3_client')
    def test_open_spider_s3_available(self, mock_get_client, mock_get_config):
        """Test pipeline initialization when S3 is available."""
        # Mock S3 being available
        mock_get_config.return_value = {'bucket_name': 'test-bucket'}
        mock_get_client.return_value = MagicMock()
        
        self.pipeline.open_spider(self.mock_spider)
        
        self.assertTrue(self.pipeline.s3_available)

    @patch('louis.db.get_s3_config')
    @patch('louis.db.get_s3_client')
    def test_open_spider_s3_unavailable(self, mock_get_client, mock_get_config):
        """Test pipeline initialization when S3 is unavailable."""
        # Mock S3 being unavailable
        mock_get_config.return_value = None
        mock_get_client.return_value = None
        
        self.pipeline.open_spider(self.mock_spider)
        
        self.assertFalse(self.pipeline.s3_available)

    @patch('louis.db.get_s3_config')
    @patch('louis.db.get_s3_client')
    def test_open_spider_s3_error(self, mock_get_client, mock_get_config):
        """Test pipeline initialization when S3 configuration fails."""
        # Mock S3 configuration error
        mock_get_config.side_effect = Exception("S3 config error")
        
        self.pipeline.open_spider(self.mock_spider)
        
        self.assertFalse(self.pipeline.s3_available)

    @patch('louis.db.store_to_s3')
    def test_process_goldie_item_s3_success(self, mock_store_s3):
        """Test successful S3 storage of goldie spider item."""
        # Set S3 as available
        self.pipeline.s3_available = True
        
        # Mock successful S3 storage
        mock_store_s3.return_value = {
            'id': 'test-uuid',
            'url': self.sample_item['url'],
            'bucket_name': 'test-bucket'
        }
        
        result = self.pipeline.process_item(self.sample_item, self.mock_spider)
        
        # Verify store_to_s3 was called
        mock_store_s3.assert_called_once_with(self.sample_item)
        
        # Verify result
        self.assertEqual(result['id'], 'test-uuid')
        self.assertEqual(result['bucket_name'], 'test-bucket')

    @patch('louis.db.store_to_disk')
    @patch('louis.db.store_to_s3')
    def test_process_goldie_item_s3_fallback(self, mock_store_s3, mock_store_disk):
        """Test S3 storage with disk fallback."""
        # Set S3 as available
        self.pipeline.s3_available = True
        
        # Mock S3 failure and disk success
        mock_store_s3.side_effect = Exception("S3 failed")
        mock_store_disk.return_value = {
            'id': 'test-uuid',
            'url': self.sample_item['url']
        }
        
        result = self.pipeline.process_item(self.sample_item, self.mock_spider)
        
        # Verify both storage methods were called
        mock_store_s3.assert_called_once_with(self.sample_item)
        mock_store_disk.assert_called_once_with(self.sample_item)
        
        # Verify result from disk storage
        self.assertEqual(result['id'], 'test-uuid')

    @patch('louis.db.store_to_disk')
    def test_process_goldie_item_s3_unavailable(self, mock_store_disk):
        """Test processing when S3 is unavailable."""
        # Set S3 as unavailable
        self.pipeline.s3_available = False
        
        # Mock disk storage success
        mock_store_disk.return_value = {
            'id': 'test-uuid',
            'url': self.sample_item['url']
        }
        
        result = self.pipeline.process_item(self.sample_item, self.mock_spider)
        
        # Verify only disk storage was called
        mock_store_disk.assert_called_once_with(self.sample_item)
        
        # Verify result
        self.assertEqual(result['id'], 'test-uuid')

    def test_process_unsupported_spider(self):
        """Test processing item from unsupported spider."""
        self.mock_spider.name = "kurt"
        
        result = self.pipeline.process_item(self.sample_item, self.mock_spider)
        
        # Should return original item unchanged
        self.assertEqual(result, self.sample_item)


class TestLouisPipeline(unittest.TestCase):
    """Test the original LouisPipeline class for regression."""

    def setUp(self):
        """Set up test environment."""
        self.pipeline = LouisPipeline()
        self.mock_spider = Mock()
        self.mock_spider.name = "goldie"

    @patch('louis.db.connect_db')
    def test_open_spider_success(self, mock_connect):
        """Test successful database connection."""
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        self.pipeline.open_spider(self.mock_spider)
        
        self.assertEqual(self.pipeline.connection, mock_connection)

    @patch('louis.db.connect_db')
    def test_open_spider_failure(self, mock_connect):
        """Test handling of database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        
        self.pipeline.open_spider(self.mock_spider)
        
        self.assertIsNone(self.pipeline.connection)

    def test_close_spider_with_connection(self):
        """Test closing spider with active database connection."""
        mock_connection = Mock()
        self.pipeline.connection = mock_connection
        
        self.pipeline.close_spider(self.mock_spider)
        
        mock_connection.close.assert_called_once()

    def test_close_spider_without_connection(self):
        """Test closing spider without database connection."""
        self.pipeline.connection = None
        
        # Should not raise any errors
        self.pipeline.close_spider(self.mock_spider)


if __name__ == '__main__':
    unittest.main() 