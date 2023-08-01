"""Test the Kurt spider"""
import unittest

from louis.crawler.spiders.kurt import KurtSpider

from louis.crawler.responses import response_from_chunk_token

class TestKurt(unittest.TestCase):
    """Test the Kurt spider"""
    def setUp(self):
        self.spider = KurtSpider()

    def test_parse(self):
        """Test that the spider returns a request for each chunk_id"""
        data = {
            'tokens': list(range(0,100))
        }
        response = response_from_chunk_token(data, 'https://example.com/path')
        item = yield from self.spider.parse(response)
        self.assertEqual(item['chunk_id'], 'https://example.com/path')

    def test_start_requests(self):
        """Test that the spider returns a request for each chunk_id"""
        requests = self.spider.start_requests()
        print(requests)
        #self.assertEqual(len(list(requests)), 1)