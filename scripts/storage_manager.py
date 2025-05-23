#!/usr/bin/env python3
"""Storage manager utility for Louis crawler.

This script provides utilities to view, search, and manage stored crawl data
across both database and disk storage modes.
"""
import sys
import os
import argparse
from datetime import datetime

# Add the parent directory to the path so we can import louis
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from louis.db import (
    get_storage_mode, list_stored_items, load_from_disk, 
    connect_db, cursor, get_storage_directory
)


def format_timestamp(timestamp):
    """Format a Unix timestamp for display."""
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'


def list_items():
    """List all stored items."""
    storage_mode = get_storage_mode()
    print(f"Storage mode: {storage_mode}")
    print("-" * 80)
    
    if storage_mode in ['disk', 'both']:
        print("📁 Disk Storage:")
        items = list_stored_items()
        if items:
            for item in items[:10]:  # Show first 10 items
                print(f"  UUID: {item['id']}")
                print(f"  URL:  {item['url']}")
                print(f"  Title: {item.get('title', 'N/A')}")
                print(f"  Lang: {item.get('lang', 'N/A')}")
                print(f"  Crawled: {format_timestamp(item.get('last_crawled'))}")
                print(f"  Files: {item.get('html_file')}, {item.get('metadata_file')}")
                print()
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more items")
        else:
            print("  No items found on disk")
        print()
    
    if storage_mode in ['database', 'both']:
        print("🗄️  Database Storage:")
        try:
            connection = connect_db()
            with cursor(connection) as cur:
                cur.execute("""
                    SELECT id, url, title, lang, last_crawled, created_at
                    FROM crawl_items 
                    ORDER BY last_crawled DESC 
                    LIMIT 10
                """)
                items = cur.fetchall()
                
                if items:
                    for item in items:
                        print(f"  UUID: {item['id']}")
                        print(f"  URL:  {item['url']}")
                        print(f"  Title: {item.get('title', 'N/A')}")
                        print(f"  Lang: {item.get('lang', 'N/A')}")
                        print(f"  Crawled: {format_timestamp(item.get('last_crawled'))}")
                        print()
                else:
                    print("  No items found in database")
            connection.close()
        except Exception as e:
            print(f"  Error accessing database: {e}")


def search_items(query):
    """Search for items by URL or title."""
    storage_mode = get_storage_mode()
    print(f"Searching for: '{query}'")
    print("-" * 80)
    
    if storage_mode in ['disk', 'both']:
        print("📁 Disk Storage Results:")
        items = list_stored_items()
        found = False
        for item in items:
            if (query.lower() in item.get('url', '').lower() or 
                query.lower() in item.get('title', '').lower()):
                print(f"  UUID: {item['id']}")
                print(f"  URL:  {item['url']}")
                print(f"  Title: {item.get('title', 'N/A')}")
                print()
                found = True
        if not found:
            print("  No matching items found on disk")
        print()
    
    if storage_mode in ['database', 'both']:
        print("🗄️  Database Results:")
        try:
            connection = connect_db()
            with cursor(connection) as cur:
                cur.execute("""
                    SELECT id, url, title, lang, last_crawled
                    FROM crawl_items 
                    WHERE url ILIKE %s OR title ILIKE %s
                    ORDER BY last_crawled DESC
                """, (f'%{query}%', f'%{query}%'))
                items = cur.fetchall()
                
                if items:
                    for item in items:
                        print(f"  UUID: {item['id']}")
                        print(f"  URL:  {item['url']}")
                        print(f"  Title: {item.get('title', 'N/A')}")
                        print()
                else:
                    print("  No matching items found in database")
            connection.close()
        except Exception as e:
            print(f"  Error searching database: {e}")


def view_item(uuid_str):
    """View a specific item by UUID."""
    storage_mode = get_storage_mode()
    
    if storage_mode in ['disk', 'both']:
        print("📁 Checking disk storage...")
        item = load_from_disk(uuid_str)
        if item:
            print(f"Found item on disk:")
            print(f"  UUID: {item['id']}")
            print(f"  URL:  {item['url']}")
            print(f"  Title: {item.get('title', 'N/A')}")
            print(f"  Lang: {item.get('lang', 'N/A')}")
            print(f"  Crawled: {format_timestamp(item.get('last_crawled'))}")
            print(f"  HTML Length: {len(item.get('html_content', ''))} characters")
            print(f"  Files: {item.get('html_file_path')}")
            print(f"         {item.get('metadata_file_path')}")
            return
    
    if storage_mode in ['database', 'both']:
        print("🗄️  Checking database...")
        try:
            connection = connect_db()
            with cursor(connection) as cur:
                cur.execute("SELECT * FROM crawl_items WHERE id = %s", (uuid_str,))
                item = cur.fetchone()
                
                if item:
                    print(f"Found item in database:")
                    print(f"  UUID: {item['id']}")
                    print(f"  URL:  {item['url']}")
                    print(f"  Title: {item.get('title', 'N/A')}")
                    print(f"  Lang: {item.get('lang', 'N/A')}")
                    print(f"  Crawled: {format_timestamp(item.get('last_crawled'))}")
                    print(f"  HTML Length: {len(item.get('html_content', ''))} characters")
                    return
            connection.close()
        except Exception as e:
            print(f"  Error accessing database: {e}")
    
    print(f"Item with UUID '{uuid_str}' not found")


def storage_stats():
    """Show storage statistics."""
    storage_mode = get_storage_mode()
    print(f"Storage mode: {storage_mode}")
    print("-" * 80)
    
    if storage_mode in ['disk', 'both']:
        print("📁 Disk Storage Statistics:")
        try:
            items = list_stored_items()
            print(f"  Total items: {len(items)}")
            
            storage_dir = get_storage_directory()
            html_dir = storage_dir / 'html'
            metadata_dir = storage_dir / 'metadata'
            
            html_files = list(html_dir.glob('*.html')) if html_dir.exists() else []
            json_files = list(metadata_dir.glob('*.json')) if metadata_dir.exists() else []
            
            print(f"  HTML files: {len(html_files)}")
            print(f"  JSON files: {len(json_files)}")
            print(f"  Storage directory: {storage_dir}")
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in html_files + json_files)
            print(f"  Total size: {total_size / (1024*1024):.2f} MB")
            
        except Exception as e:
            print(f"  Error calculating disk stats: {e}")
        print()
    
    if storage_mode in ['database', 'both']:
        print("🗄️  Database Statistics:")
        try:
            connection = connect_db()
            with cursor(connection) as cur:
                # Count items in each table
                cur.execute("SELECT COUNT(*) as count FROM crawl_items")
                crawl_count = cur.fetchone()['count']
                
                cur.execute("SELECT COUNT(*) as count FROM chunk_items")
                chunk_count = cur.fetchone()['count']
                
                cur.execute("SELECT COUNT(*) as count FROM embedding_items")
                embedding_count = cur.fetchone()['count']
                
                cur.execute("SELECT COUNT(*) as count FROM page_links")
                links_count = cur.fetchone()['count']
                
                print(f"  Crawl items: {crawl_count}")
                print(f"  Chunk items: {chunk_count}")
                print(f"  Embedding items: {embedding_count}")
                print(f"  Page links: {links_count}")
                
            connection.close()
        except Exception as e:
            print(f"  Error accessing database: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Louis crawler storage manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List stored items')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search items by URL or title')
    search_parser.add_argument('query', help='Search query')
    
    # View command
    view_parser = subparsers.add_parser('view', help='View a specific item by UUID')
    view_parser.add_argument('uuid', help='Item UUID')
    
    # Stats command
    subparsers.add_parser('stats', help='Show storage statistics')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_items()
    elif args.command == 'search':
        search_items(args.query)
    elif args.command == 'view':
        view_item(args.uuid)
    elif args.command == 'stats':
        storage_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 