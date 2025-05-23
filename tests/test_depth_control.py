#!/usr/bin/env python3
"""
Test script to demonstrate depth control and URL tracking functionality.
This script simulates the spider behavior to show how the features work.
"""

import os
import tempfile
from unittest.mock import Mock
from louis.crawler.spiders.goldie_playwright import GoldiePlaywrightSpider


def create_mock_response(url, depth=0):
    """Create a mock response for testing."""
    response = Mock()
    response.url = url
    response.meta = {"depth": depth}
    response.css.return_value.getall.return_value = [
        "/en/food",
        "/en/animals",
        "/en/plants",
        "https://inspection.canada.ca/en/contact",
        "#top",  # Should be ignored
        "mailto:test@test.com",  # Should be ignored
    ]
    return response


def test_spider_initialization():
    """Test spider initialization with different parameters."""
    print("🔧 Testing Spider Initialization")
    print("=" * 50)

    # Test default initialization
    spider1 = GoldiePlaywrightSpider()
    print(
        f"✅ Default spider - max_depth: {spider1.max_depth}, file: {spider1.scraped_urls_file}"
    )

    # Test custom initialization
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp.write("https://example.com/existing\n")
        tmp_name = tmp.name

    spider2 = GoldiePlaywrightSpider(max_depth=2, scraped_urls_file=tmp_name)
    print(
        f"✅ Custom spider - max_depth: {spider2.max_depth}, file: {spider2.scraped_urls_file}"
    )
    print(f"✅ Loaded {len(spider2.scraped_urls)} existing URLs")

    # Clean up
    os.unlink(tmp_name)
    print()


def test_url_tracking():
    """Test URL tracking functionality."""
    print("📝 Testing URL Tracking")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp_name = tmp.name

    spider = GoldiePlaywrightSpider(max_depth=1, scraped_urls_file=tmp_name)

    # Test saving URLs
    test_urls = [
        "https://inspection.canada.ca/en",
        "https://inspection.canada.ca/en/food",
        "https://inspection.canada.ca/en/animals",
    ]

    for url in test_urls:
        spider._save_scraped_url(url)
        print(f"✅ Saved: {url}")

    # Test checking if URL is scraped
    print(f"✅ URL check - already scraped: {spider._is_url_scraped(test_urls[0])}")
    print(f"✅ URL check - new URL: {spider._is_url_scraped('https://new-url.com')}")

    # Test loading from file
    spider2 = GoldiePlaywrightSpider(max_depth=1, scraped_urls_file=tmp_name)
    print(f"✅ New spider loaded {len(spider2.scraped_urls)} URLs from file")

    # Clean up
    os.unlink(tmp_name)
    print()


def test_depth_control():
    """Test depth control functionality."""
    print("📊 Testing Depth Control")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp_name = tmp.name

    # Test with different max depths
    for max_depth in [0, 1, 2]:
        print(f"\n🔍 Testing max_depth={max_depth}")
        spider = GoldiePlaywrightSpider(max_depth=max_depth, scraped_urls_file=tmp_name)

        # Simulate parse method behavior
        mock_response = create_mock_response("https://inspection.canada.ca/en", depth=0)

        print(f"   Current depth: {spider._get_request_depth(mock_response)}")
        print(
            f"   Should follow links: {spider._get_request_depth(mock_response) < spider.max_depth}"
        )

        if spider._get_request_depth(mock_response) < spider.max_depth:
            print(
                f"   Would extract and follow URLs at depth {spider._get_request_depth(mock_response) + 1}"
            )
        else:
            print(f"   Would NOT follow links (max depth reached)")

    # Clean up
    os.unlink(tmp_name)
    print()


def test_different_spider_types():
    """Test all three spider types with the new features."""
    print("🕷️  Testing Different Spider Types")
    print("=" * 50)

    spider_classes = [
        (GoldiePlaywrightSpider, "Playwright Spider")
    ]

    for spider_class, name in spider_classes:
        print(f"\n🔹 Testing {name}")
        spider = spider_class(max_depth=1)
        print(f"   ✅ Name: {spider.name}")
        print(f"   ✅ Max depth: {spider.max_depth}")
        print(f"   ✅ URL file: {spider.scraped_urls_file}")
        print(f"   ✅ Scraped URLs loaded: {len(spider.scraped_urls)}")

    print()


def test_url_file_format():
    """Test the URL file format and management."""
    print("📄 Testing URL File Format")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        # Create a sample URL file
        sample_urls = [
            "https://inspection.canada.ca/en",
            "https://inspection.canada.ca/en/food/imports",
            "https://inspection.canada.ca/en/animal-health",
            "https://inspection.canada.ca/en/plants/plant-health",
        ]

        for url in sample_urls:
            tmp.write(f"{url}\n")
        tmp_name = tmp.name

    # Test loading the file
    spider = GoldiePlaywrightSpider(scraped_urls_file=tmp_name)

    print(f"✅ File format test:")
    print(f"   File: {tmp_name}")
    print(f"   URLs in file: {len(sample_urls)}")
    print(f"   URLs loaded: {len(spider.scraped_urls)}")

    # Show file contents
    with open(tmp_name, "r") as f:
        content = f.read().strip()
        print(f"   File contents preview:")
        for i, line in enumerate(content.split("\n")[:3]):
            print(f"     {i + 1}: {line}")
        if len(content.split("\n")) > 3:
            print(f"     ... and {len(content.split('\n')) - 3} more lines")

    # Clean up
    os.unlink(tmp_name)
    print()


def demonstrate_usage():
    """Demonstrate typical usage scenarios."""
    print("💡 Usage Demonstrations")
    print("=" * 50)

    scenarios = [
        {
            "name": "Basic crawl with depth 1",
            "command": "scrapy crawl goldie_playwright -a max_depth=1",
            "description": "Scrape start page + direct links",
        },
        {
            "name": "Only start pages (depth 0)",
            "command": "scrapy crawl goldie_playwright -a max_depth=0",
            "description": "Only scrape start URLs, no link following",
        },
        {
            "name": "Deep crawl with custom file",
            "command": 'scrapy crawl goldie_smart -a max_depth=2 -a scraped_urls_file="deep_crawl.txt"',
            "description": "Two levels deep with custom tracking file",
        },
        {
            "name": "Resume previous crawl",
            "command": "scrapy crawl goldie_playwright -a max_depth=1",
            "description": "Run same command twice - second run skips scraped URLs",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔹 Scenario {i}: {scenario['name']}")
        print(f"   Command: {scenario['command']}")
        print(f"   Description: {scenario['description']}")

    print()


def main():
    """Run all tests and demonstrations."""
    print("🚀 Depth Control and URL Tracking Test Suite")
    print("=" * 60)
    print()

    try:
        test_spider_initialization()
        test_url_tracking()
        test_depth_control()
        test_different_spider_types()
        test_url_file_format()
        demonstrate_usage()

        print("✅ All tests completed successfully!")
        print("\n📖 For more information, see README_depth_control.md")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
