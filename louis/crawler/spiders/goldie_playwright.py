"""
Playwright-enabled version of the goldie spider for JavaScript-rendered content.
"""

import re
import time
import os
from datetime import datetime
from louis.crawler.spiders.base_playwright import (
    PlaywrightSpider,
    SmartPlaywrightSpider,
)
from louis.crawler.items import CrawlItem
from louis.crawler.requests import extract_urls, fix_vhost


def generate_timestamped_filename(base_name: str, extension: str = "log") -> str:
    """Generate a filename with timestamp suffix in format _yyyymmddhhmmss.
    
    Args:
        base_name: Base name without extension (e.g., 'logs/scraped_urls')
        extension: File extension (e.g., 'txt'). If None, will extract from base_name
    
    Returns:
        str: Filename with timestamp suffix (e.g., 'logs/scraped_urls_20250115153045.txt')
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    if extension is None:
        # Try to extract extension from base_name
        if '.' in base_name:
            base_name, extension = base_name.rsplit('.', 1)
        else:
            extension = ''
    
    if extension:
        return f"{base_name}_{timestamp}.{extension}"
    else:
        return f"{base_name}_{timestamp}"


class GoldiePlaywrightSpider(PlaywrightSpider):
    """
    Goldie spider with full Playwright support for JavaScript-rendered content.
    Use this when you know the site heavily relies on JavaScript.
    """

    name = "goldie_playwright"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/en"]

    # Playwright settings specific to this site
    playwright_wait_until = "networkidle"
    playwright_timeout = 30000
    playwright_wait_time = 3  # Wait 3 seconds for any final JS execution

    def __init__(
        self,
        max_depth=1,
        scraped_urls_file=None,
        pending_urls_file=None,
        errored_urls_file=None,
        *args,
        **kwargs,
    ):
        """
        Initialize the spider with depth control and URL tracking.

        Args:
            max_depth (int): Maximum crawl depth (0 = only start URLs, 1 = start URLs + their links)
            scraped_urls_file (str): File to store scraped URLs to avoid duplicates
            pending_urls_file (str): File to store pending URLs for resuming interrupted scraping
            errored_urls_file (str): File to store URLs that resulted in errors
        """
        super().__init__(*args, **kwargs)
        self.max_depth = int(max_depth)
        
        # Generate timestamped filenames if not provided
        self.scraped_urls_file = scraped_urls_file or generate_timestamped_filename("logs/scraped_urls")
        self.pending_urls_file = pending_urls_file or generate_timestamped_filename("logs/pending_urls")
        self.errored_urls_file = errored_urls_file or generate_timestamped_filename("logs/errored_urls")
        
        self.scraped_urls = set()
        self.pending_urls = set()
        self.errored_urls = set()
        self._load_scraped_urls()
        self._load_pending_urls()
        self._load_errored_urls()

        self.logger.info(f"Spider initialized with max_depth={self.max_depth}")
        self.logger.info(
            f"scraped_urls_file={self.scraped_urls_file}, pending_urls_file={self.pending_urls_file}, errored_urls_file={self.errored_urls_file}"
        )
        self.logger.info(f"Already scraped URLs loaded: {len(self.scraped_urls)}")
        self.logger.info(f"Pending URLs loaded: {len(self.pending_urls)}")
        self.logger.info(f"Errored URLs loaded: {len(self.errored_urls)}")

    def _load_scraped_urls(self):
        """Load previously scraped URLs from file."""
        if os.path.exists(self.scraped_urls_file):
            try:
                with open(self.scraped_urls_file, "r", encoding="utf-8") as f:
                    self.scraped_urls = set(line.strip() for line in f if line.strip())
                self.logger.info(
                    f"Loaded {len(self.scraped_urls)} URLs from {self.scraped_urls_file}"
                )
            except Exception as e:
                self.logger.error(f"Error loading scraped URLs: {e}")
                self.scraped_urls = set()
        else:
            self.logger.info(
                f"No existing scraped URLs file found: {self.scraped_urls_file}"
            )

    def _load_pending_urls(self):
        """Load pending URLs from file."""
        if os.path.exists(self.pending_urls_file):
            try:
                with open(self.pending_urls_file, "r", encoding="utf-8") as f:
                    # Load pending URLs with their depth information
                    self.pending_urls = set()
                    for line in f:
                        line = line.strip()
                        if line:
                            # Format: URL|depth
                            if "|" in line:
                                url, depth = line.rsplit("|", 1)
                                try:
                                    depth = int(depth)
                                    self.pending_urls.add((url, depth))
                                except ValueError:
                                    # Fallback: treat as URL with depth 0
                                    self.pending_urls.add((line, 0))
                            else:
                                # Backward compatibility: URL without depth
                                self.pending_urls.add((line, 0))
                self.logger.info(
                    f"Loaded {len(self.pending_urls)} pending URLs from {self.pending_urls_file}"
                )
            except Exception as e:
                self.logger.error(f"Error loading pending URLs: {e}")
                self.pending_urls = set()
        else:
            self.logger.info(
                f"No existing pending URLs file found: {self.pending_urls_file}"
            )

    def _load_errored_urls(self):
        """Load previously errored URLs from file."""
        if os.path.exists(self.errored_urls_file):
            try:
                with open(self.errored_urls_file, "r", encoding="utf-8") as f:
                    self.errored_urls = set(line.strip() for line in f if line.strip())
                self.logger.info(
                    f"Loaded {len(self.errored_urls)} errored URLs from {self.errored_urls_file}"
                )
            except Exception as e:
                self.logger.error(f"Error loading errored URLs: {e}")
                self.errored_urls = set()
        else:
            self.logger.info(
                f"No existing errored URLs file found: {self.errored_urls_file}"
            )

    def _save_scraped_url(self, url):
        """Save a newly scraped URL to file."""
        if url not in self.scraped_urls:
            self.scraped_urls.add(url)
            try:
                with open(self.scraped_urls_file, "a", encoding="utf-8") as f:
                    f.write(f"{url}\n")
            except Exception as e:
                self.logger.error(f"Error saving scraped URL: {e}")

    def _save_errored_url(self, url):
        """Save a newly errored URL to file."""
        if url not in self.errored_urls:
            self.errored_urls.add(url)
            try:
                with open(self.errored_urls_file, "a", encoding="utf-8") as f:
                    f.write(f"{url}\n")
            except Exception as e:
                self.logger.error(f"Error saving errored URL: {e}")

    def _add_pending_url(self, url, depth):
        """Add a URL to pending queue."""
        if url not in self.scraped_urls and url not in self.errored_urls:
            url_depth_tuple = (url, depth)
            if url_depth_tuple not in self.pending_urls:
                self.pending_urls.add(url_depth_tuple)
                try:
                    with open(self.pending_urls_file, "a", encoding="utf-8") as f:
                        f.write(f"{url}|{depth}\n")
                except Exception as e:
                    self.logger.error(f"Error saving pending URL: {e}")

    def _remove_pending_url(self, url):
        """Remove a URL from pending queue."""
        # Remove all entries with this URL (regardless of depth)
        to_remove = [item for item in self.pending_urls if item[0] == url]
        for item in to_remove:
            self.pending_urls.remove(item)

        # Rewrite the pending URLs file
        self._save_all_pending_urls()

    def _save_all_pending_urls(self):
        """Save all pending URLs to file (overwrites existing file)."""
        try:
            with open(self.pending_urls_file, "w", encoding="utf-8") as f:
                for url, depth in self.pending_urls:
                    f.write(f"{url}|{depth}\n")
        except Exception as e:
            self.logger.error(f"Error saving all pending URLs: {e}")

    def _is_url_scraped(self, url):
        """Check if URL has already been scraped."""
        return url in self.scraped_urls

    def _get_request_depth(self, response):
        """Get the current depth of a request."""
        return response.meta.get("depth", 0)

    def start_requests(self):
        """Generate initial requests with Playwright."""
        # First, process any pending URLs from previous run
        for (
            url,
            depth,
        ) in (
            self.pending_urls.copy()
        ):  # Use copy to avoid modification during iteration
            if not self._is_url_scraped(url):
                self.logger.info(f"Resuming pending URL (depth {depth}): {url}")
                yield self.make_playwright_request(
                    url,
                    callback=self.parse,
                    errback=self.handle_error,
                    wait_for_selector="main, body",
                    wait_time=3,
                    meta={"depth": depth},
                )
            else:
                self.logger.info(f"Removing already scraped pending URL: {url}")
                self._remove_pending_url(url)

        # Then, process start URLs if not already scraped or pending
        for url in self.start_urls:
            if not self._is_url_scraped(url) and not any(
                pending_url == url for pending_url, _ in self.pending_urls
            ):
                self.logger.info(f"Starting new URL: {url}")
                self._add_pending_url(url, 0)  # Add to pending before processing
                yield self.make_playwright_request(
                    url,
                    callback=self.parse,
                    errback=self.handle_error,
                    wait_for_selector="main, body",  # Wait for main content area
                    wait_time=5,  # Extra wait for initial page
                    meta={"depth": 0},  # Start at depth 0
                )
            else:
                self.logger.info(
                    f"Skipping already scraped or pending start URL: {url}"
                )

    def parse(self, response):
        """Parse response and extract data."""
        current_depth = self._get_request_depth(response)
        self.logger.info(
            f"Parsing with Playwright (depth {current_depth}): {response.url}"
        )

        # Remove URL from pending queue (it's now being processed)
        self._remove_pending_url(response.url)

        # Mark URL as scraped
        self._save_scraped_url(response.url)

        # Convert to crawl item
        yield self.convert_to_crawl_item(response)

        # Always extract URLs for discovery, but behavior depends on depth
        yield from self.extract_and_follow_urls(response, current_depth)

    def extract_and_follow_urls(self, response, current_depth):
        """Extract URLs and either follow them or save to pending based on depth."""
        next_depth = current_depth + 1
        links_found = 0
        links_followed = 0
        links_saved_for_later = 0

        # Determine if we should follow links or just save them for later
        should_follow_links = current_depth < self.max_depth
        should_save_for_later = current_depth <= self.max_depth

        if should_follow_links:
            self.logger.info(
                f"Following links from depth {current_depth} (max_depth={self.max_depth})"
            )
        elif should_save_for_later:
            self.logger.info(
                f"At max depth {self.max_depth}, saving links for future runs from: {response.url}"
            )
        else:
            self.logger.info(
                f"Beyond max depth {self.max_depth}, not processing links from: {response.url}"
            )
            return

        for link in response.css("a::attr(href)").getall():
            if link and not link.startswith("#") and not link.startswith("mailto:"):
                absolute_url = response.urljoin(link)
                links_found += 1

                # Check if URL is in allowed domains
                if self.allowed_domains:
                    domain = absolute_url.split("/")[2] if "://" in absolute_url else ""
                    if any(allowed in domain for allowed in self.allowed_domains):
                        # Check if URL has already been scraped, errored, or is pending
                        if (
                            not self._is_url_scraped(absolute_url)
                            and absolute_url not in self.errored_urls
                            and not any(
                                pending_url == absolute_url
                                for pending_url, _ in self.pending_urls
                            )
                        ):
                            if should_follow_links:
                                # Add to pending queue and create request
                                self._add_pending_url(absolute_url, next_depth)
                                yield self.make_playwright_request(
                                    absolute_url,
                                    callback=self.parse,
                                    errback=self.handle_error,
                                    wait_for_selector="main",
                                    wait_time=2,
                                    meta={"depth": next_depth},
                                )
                                links_followed += 1
                            elif should_save_for_later:
                                # Just save to pending for future runs
                                self._add_pending_url(absolute_url, next_depth)
                                links_saved_for_later += 1
                        else:
                            self.logger.debug(
                                f"Skipping already scraped or pending URL: {absolute_url}"
                            )

        if should_follow_links:
            self.logger.info(
                f"Found {links_found} links, following {links_followed} new ones at depth {next_depth}"
            )
        elif should_save_for_later:
            self.logger.info(
                f"Found {links_found} links, saved {links_saved_for_later} new ones for future runs at depth {next_depth}"
            )

    def handle_error(self, failure):
        """Handle request errors and save errored URLs."""
        url = failure.request.url
        error_msg = str(failure.value)

        self.logger.error(f"Request failed for {url}: {error_msg}")

        # Remove from pending queue (it's no longer pending)
        self._remove_pending_url(url)

        # Save to errored URLs
        self._save_errored_url(url)

    def closed(self, reason):
        """Called when the spider is closed."""
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total URLs scraped: {len(self.scraped_urls)}")
        self.logger.info(f"Total URLs errored: {len(self.errored_urls)}")
        self.logger.info(f"Pending URLs remaining: {len(self.pending_urls)}")

        if self.pending_urls:
            self.logger.info(
                f"You can resume scraping later with {len(self.pending_urls)} pending URLs"
            )
            # Ensure all pending URLs are saved to file
            self._save_all_pending_urls()
        else:
            # Clean up pending file if no URLs remain
            if os.path.exists(self.pending_urls_file):
                try:
                    os.remove(self.pending_urls_file)
                    self.logger.info(
                        f"Removed empty pending URLs file: {self.pending_urls_file}"
                    )
                except Exception as e:
                    self.logger.error(f"Error removing pending URLs file: {e}")

    def clean_content(self, response) -> str:
        """Custom content cleaning for goldie spider."""
        # Find main content area
        main = response.css("main")
        if main:
            # Remove unwanted sections
            main.css("aside").drop()
            main.css(".pagedetails").drop()
            main.css("script").drop()
            main.css(".nojs-hide").drop()
            main.css(".alert").drop()
            main.css("nav").drop()
            main.css("header").drop()
            main.css("footer").drop()

            content = main.get()
        else:
            # Fallback to body if no main element
            content = response.css("body").get()

        if content:
            # Use BeautifulSoup for final cleaning
            from bs4 import BeautifulSoup, Comment

            soup = BeautifulSoup(content, "lxml")

            # Remove comments
            for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            content = str(soup)
            return re.sub(r"\s+", " ", content).strip()

        return ""
