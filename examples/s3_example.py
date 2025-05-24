#!/usr/bin/env python3
"""
Example script demonstrating S3 storage functionality for Louis crawler.

This script shows how to:
1. Set up S3 storage mode
2. Store crawl items to S3
3. Load items from S3
4. List all stored items

Prerequisites:
- MinIO server running (or any S3-compatible service)
- minio package installed: uv pip install minio

Environment variables:
- STORAGE_MODE=s3 (or 'database' or 'disk')
- S3_ENDPOINT=localhost:9000 (default)
- S3_ACCESS_KEY=minioadmin (default)
- S3_SECRET_KEY=minioadmin (default)
- S3_BUCKET_NAME=louis-crawler (default)
- S3_SECURE=false (default, set to true for HTTPS)
"""

import os
import sys
from datetime import datetime
import time

# Add the louis directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from louis.db import (
    initialize_database,
    store_crawl_item,
    load_from_s3,
    list_s3_items,
    get_storage_mode
)


def main():
    # Set storage mode to S3
    os.environ['STORAGE_MODE'] = 's3'
    
    print("🚀 Louis Crawler S3 Storage Example")
    print(f"Storage mode: {get_storage_mode()}")
    print()
    
    # Initialize storage
    print("Initializing storage...")
    try:
        initialize_database()
    except Exception as e:
        print(f"❌ Failed to initialize storage: {e}")
        print("\n💡 Make sure MinIO is running:")
        print("   docker run -p 9000:9000 -p 9001:9001 \\")
        print("     -e MINIO_ROOT_USER=minioadmin \\")
        print("     -e MINIO_ROOT_PASSWORD=minioadmin \\")
        print("     minio/minio server /data --console-address ':9001'")
        return
    
    print()
    
    # Example crawl item
    example_item = {
        'url': 'https://example.com/test-page',
        'title': 'Test Page for S3 Storage',
        'lang': 'en',
        'html_content': '''<!DOCTYPE html>
<html>
<head>
    <title>Test Page for S3 Storage</title>
</head>
<body>
    <h1>Hello from S3!</h1>
    <p>This is a test page stored in S3 using MinIO.</p>
    <p>The HTML content is stored as html/{uuid}.html</p>
    <p>The metadata is stored as metadata/{uuid}.json</p>
</body>
</html>''',
        'last_crawled': int(time.time()),
        'last_updated': datetime.now().isoformat()
    }
    
    # Store the item
    print("📝 Storing crawl item to S3...")
    try:
        result = store_crawl_item(None, example_item)  # None cursor for S3-only
        print(f"✅ Stored item with ID: {result['id']}")
        print(f"   HTML object: {result['html_object']}")
        print(f"   Metadata object: {result['metadata_object']}")
        print(f"   Bucket: {result['bucket_name']}")
        file_uuid = result['id']
    except Exception as e:
        print(f"❌ Failed to store item: {e}")
        return
    
    print()
    
    # Load the item back
    print("📖 Loading item from S3...")
    try:
        loaded_item = load_from_s3(file_uuid)
        if loaded_item:
            print(f"✅ Loaded item: {loaded_item['title']}")
            print(f"   URL: {loaded_item['url']}")
            print(f"   HTML length: {len(loaded_item['html_content'])} characters")
        else:
            print("❌ Item not found")
    except Exception as e:
        print(f"❌ Failed to load item: {e}")
    
    print()
    
    # List all items
    print("📋 Listing all items in S3...")
    try:
        items = list_s3_items()
        print(f"✅ Found {len(items)} items:")
        for item in items:
            print(f"   - {item['title']} ({item['url']})")
            print(f"     ID: {item['id']}")
            print(f"     Objects: {item['html_object']}, {item['metadata_object']}")
    except Exception as e:
        print(f"❌ Failed to list items: {e}")
    
    print()
    print("🎉 S3 storage example completed!")
    print("\n💡 You can view the objects in MinIO console at http://localhost:9001")
    print("   Login: minioadmin / minioadmin")


if __name__ == "__main__":
    main()
