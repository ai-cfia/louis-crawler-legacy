#!/usr/bin/env python3
"""Initialize the Louis crawler database.

This script creates the necessary tables and indexes for the Louis crawler.
Run this script once before using the crawler for the first time.
"""
import sys
import os

# Add the parent directory to the path so we can import louis
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from louis.db import initialize_database

if __name__ == "__main__":
    print("Initializing Louis crawler database...")
    try:
        initialize_database()
        print("✅ Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Set up your database connection in environment variables (see .env.example)")
        print("2. Run the crawler: scrapy crawl goldie")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nPlease check your database connection settings and try again.")
        sys.exit(1) 