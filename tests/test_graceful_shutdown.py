#!/usr/bin/env python3
"""
Test script to demonstrate graceful shutdown functionality.
Run this and press Ctrl+C to test graceful shutdown.
"""

import subprocess
import time
import signal
import sys

def main():
    print("🚀 Starting spider with graceful shutdown capabilities...")
    print("   Press Ctrl+C to test graceful shutdown")
    print("   The spider will handle the signal and stop all workers gracefully")
    print()
    
    try:
        # Run the spider
        result = subprocess.run([
            "scrapy", "crawl", "goldie_playwright_parallel",
            "-a", "max_depth=2",  # Higher depth for longer running
            "-a", "num_workers=2", 
            "-a", "batch_size=3"
        ], cwd="/home/p4r0d1m3pxz/work/louis-crawler-legacy")
        
        print(f"Spider completed with exit code: {result.returncode}")
        
    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C detected! The spider should have handled this gracefully.")
        print("   Check the logs above for graceful shutdown messages.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 
