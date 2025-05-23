#!/usr/bin/env python3
"""
Setup script for Playwright browsers.
Run this after installing the requirements to set up Playwright browsers.
"""
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run a command and log the result."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Success: {description}")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Error: {e.stderr}")
        return False


def main():
    """Main setup function."""
    logger.info("Setting up Playwright for louis-crawler")
    
    # Install Playwright browsers
    commands = [
        (
            [sys.executable, "-m", "playwright", "install", "chromium"],
            "Installing Chromium browser"
        ),
        (
            [sys.executable, "-m", "playwright", "install", "firefox"],
            "Installing Firefox browser"
        ),
        (
            [sys.executable, "-m", "playwright", "install", "webkit"],
            "Installing WebKit browser"
        ),
        (
            [sys.executable, "-m", "playwright", "install-deps"],
            "Installing system dependencies"
        ),
    ]
    
    success_count = 0
    for cmd, description in commands:
        if run_command(cmd, description):
            success_count += 1
    
    logger.info(f"Setup completed: {success_count}/{len(commands)} commands successful")
    
    if success_count == len(commands):
        logger.info("✅ Playwright setup completed successfully!")
        logger.info("You can now run spiders with Playwright support:")
        logger.info("  scrapy crawl goldie_playwright")
        logger.info("  scrapy crawl goldie_smart")
        logger.info("  scrapy crawl goldie_hybrid")
    else:
        logger.error("❌ Some setup steps failed. Please check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 