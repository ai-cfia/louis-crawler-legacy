"""
Parallel Playwright-enabled version of the goldie spider for JavaScript-rendered content.
Uses multiprocessing to utilize multiple CPU cores for concurrent crawling.
"""

import re
import time
import os
import signal
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Set, Tuple, Dict, Any
import logging
import queue
from datetime import datetime
import json
import tempfile
import shutil
import uuid

from louis.crawler.spiders.base_playwright import (
    PlaywrightSpider
)
from louis.crawler.items import CrawlItem
from louis.crawler.requests import extract_urls, fix_vhost
import louis.db as db


def init_worker(log_file_path=None, use_console=True):
    """Initialize worker process - set up logging and any required resources."""
    # Set up signal handlers for worker processes
    def worker_signal_handler(signum, frame):
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logging.getLogger().info(f"Worker received {signal_name}, exiting gracefully...")
        # Allow current operation to complete but don't start new ones
        
    signal.signal(signal.SIGINT, worker_signal_handler)
    signal.signal(signal.SIGTERM, worker_signal_handler)
    
    # Configure logging for worker processes to write to shared file
    if log_file_path:
        handlers = [logging.FileHandler(log_file_path)]
        
        # Only add console handler if requested (not when using Scrapy file logging)
        if use_console:
            handlers.append(logging.StreamHandler())
        
        # Use FileHandler for shared logging across processes
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [PID:%(process)d] [%(processName)s] %(levelname)s: %(message)s",
            handlers=handlers,
            force=True,  # Override any existing configuration
        )
    else:
        # Fallback to console logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [PID:%(process)d] [%(processName)s] %(levelname)s: %(message)s",
            force=True,
        )


def process_url_worker(args):
    """
    Worker function to process a single URL with Playwright.
    This function runs in a separate process.

    Args:
        args: Tuple containing (url, depth, spider_config, task_id)

    Returns:
        Dict with processing results or error information
    """
    url, depth, spider_config, task_id = args

    try:
        # Import here to avoid issues with multiprocessing
        from playwright.sync_api import sync_playwright
        import scrapy
        from scrapy.http import HtmlResponse
        from louis.crawler.items import CrawlItem
        from bs4 import BeautifulSoup, Comment

        logger = logging.getLogger(f"worker-{os.getpid()}")
        logger.info(f"[TASK:{task_id}] Processing URL (depth {depth}): {url}")

        result = {
            "url": url,
            "depth": depth,
            "success": False,
            "item": None,
            "links": [],
            "error": None,
            "processing_time": 0,
            "task_id": task_id,
        }

        start_time = time.time()

        with sync_playwright() as p:
            # Launch browser with optimized settings for headless operation
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-web-security",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                ],
            )

            try:
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )
                page = context.new_page()

                # Set timeouts
                page.set_default_timeout(spider_config.get("playwright_timeout", 30000))

                logger.info(f"[TASK:{task_id}] Navigating to {url}")

                # Navigate to URL
                response = page.goto(
                    url,
                    wait_until=spider_config.get(
                        "playwright_wait_until", "networkidle"
                    ),
                )

                if response and response.status < 400:
                    logger.info(
                        f"[TASK:{task_id}] Page loaded successfully, status: {response.status}"
                    )

                    # Wait for additional time if specified
                    wait_time = spider_config.get("playwright_wait_time", 3)
                    if wait_time > 0:
                        logger.info(
                            f"[TASK:{task_id}] Waiting {wait_time}s for JS execution"
                        )
                        page.wait_for_timeout(wait_time * 1000)

                    # Get page content
                    content = page.content()
                    logger.info(
                        f"[TASK:{task_id}] Retrieved page content ({len(content)} characters)"
                    )

                    # Create Scrapy response-like object
                    scrapy_response = HtmlResponse(
                        url=url, body=content.encode("utf-8"), encoding="utf-8"
                    )

                    # Clean content
                    cleaned_content = clean_content_worker(scrapy_response)
                    logger.info(
                        f"[TASK:{task_id}] Content cleaned ({len(cleaned_content)} characters)"
                    )

                    # Create crawl item
                    item = CrawlItem()
                    item["url"] = url
                    item["title"] = scrapy_response.css("title::text").get() or ""
                    item["html_content"] = cleaned_content
                    item["last_crawled"] = datetime.now().isoformat()
                    # Store depth info for tracking (custom field)
                    item["depth"] = depth
                    
                    # Determine language from URL
                    item["lang"] = "fr" if ".ca/fr" in url else "en"

                    # Extract links
                    links = []
                    allowed_domains = spider_config.get("allowed_domains", [])

                    for link in scrapy_response.css("a::attr(href)").getall():
                        if (
                            link
                            and not link.startswith("#")
                            and not link.startswith("mailto:")
                        ):
                            absolute_url = scrapy_response.urljoin(link)

                            # Check if URL is in allowed domains
                            if allowed_domains:
                                domain = (
                                    absolute_url.split("/")[2]
                                    if "://" in absolute_url
                                    else ""
                                )
                                if any(
                                    allowed in domain for allowed in allowed_domains
                                ):
                                    links.append(absolute_url)
                            else:
                                links.append(absolute_url)

                    # Remove duplicates while preserving order
                    seen = set()
                    unique_links = []
                    for link in links:
                        if link not in seen:
                            seen.add(link)
                            unique_links.append(link)
                    
                    # Store links in the children field
                    item["children"] = unique_links

                    logger.info(f"[TASK:{task_id}] Extracted {len(unique_links)} unique links")

                    result.update(
                        {
                            "success": True,
                            "item": dict(item),
                            "links": unique_links,
                            "processing_time": time.time() - start_time,
                        }
                    )

                    logger.info(
                        f"[TASK:{task_id}] Successfully processed {url} in {result['processing_time']:.2f}s - found {len(unique_links)} links"
                    )

                else:
                    result["error"] = (
                        f"HTTP {response.status if response else 'No response'}"
                    )
                    logger.warning(
                        f"[TASK:{task_id}] Failed to load {url}: {result['error']}"
                    )

            finally:
                browser.close()
                logger.info(f"[TASK:{task_id}] Browser closed")

    except Exception as e:
        result["error"] = str(e)
        result["processing_time"] = time.time() - start_time
        logger.error(f"[TASK:{task_id}] Error processing {url}: {e}")

    return result


def clean_content_worker(response) -> str:
    """Custom content cleaning for goldie spider - worker version."""
    try:
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
    except Exception as e:
        return ""


def generate_timestamped_filename(base_name: str, extension: str = "log") -> str:
    """Generate a filename with timestamp suffix in format _yyyymmddhhmmss.
    
    Args:
        base_name: Base name without extension (e.g., 'logs/crawler_parallel')
        extension: File extension (e.g., 'log'). If None, will extract from base_name
    
    Returns:
        str: Filename with timestamp suffix (e.g., 'logs/crawler_parallel_20250115153045.log')
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


def get_pipeline_config_for_storage_mode():
    """Get the appropriate pipeline configuration based on STORAGE_MODE environment variable.
    
    Returns:
        dict: Pipeline configuration dictionary
    """
    storage_mode = db.get_storage_mode()
    
    if storage_mode == 'database':
        return {
            'louis.crawler.pipelines.LouisPipeline': 300,
        }
    elif storage_mode == 'disk':
        return {
            'louis.crawler.pipelines.DiskPipeline': 300,
        }
    elif storage_mode == 's3':
        return {
            'louis.crawler.pipelines.S3Pipeline': 300,
        }
    else:
        # Fallback to database pipeline for unknown modes
        print(f"Warning: Unknown storage mode '{storage_mode}', falling back to database pipeline")
        return {
            'louis.crawler.pipelines.LouisPipeline': 300,
        }


class GoldiePlaywrightParallelSpider(PlaywrightSpider):
    """
    Parallel version of Goldie spider with multiprocessing support for JavaScript-rendered content.
    Uses multiple CPU cores to process URLs concurrently.
    """

    name = "goldie_playwright_parallel"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/"]

    # Playwright settings specific to this site
    playwright_wait_until = "networkidle"
    playwright_timeout = 120000
    playwright_wait_time = 10  # Wait 3 seconds for any final JS execution

    # Custom settings to ensure all logging goes to files
    # Pipeline is dynamically selected based on STORAGE_MODE environment variable
    custom_settings = {
        'LOG_FILE': generate_timestamped_filename('logs/scrapy', 'log'),
        'LOG_LEVEL': 'INFO',
        'LOG_STDOUT': False,  # Don't log to stdout
        'ITEM_PIPELINES': get_pipeline_config_for_storage_mode(),
    }

    def __init__(
        self,
        max_depth=1,
        num_workers=None,
        batch_size=10,
        scraped_urls_file=None,
        pending_urls_file=None,
        errored_urls_file=None,
        log_file=None,
        *args,
        **kwargs,
    ):
        """
        Initialize the parallel spider with depth control, URL tracking, and worker management.

        Args:
            max_depth (int): Maximum crawl depth (0 = only start URLs, 1 = start URLs + their links)
            num_workers (int): Number of worker processes (defaults to CPU count)
            batch_size (int): Number of URLs to process in each batch
            scraped_urls_file (str): File to store scraped URLs to avoid duplicates
            pending_urls_file (str): File to store pending URLs for resuming interrupted scraping
            errored_urls_file (str): File to store URLs that resulted in errors
            log_file (str): Shared log file for all workers and main process
        """
        super().__init__(*args, **kwargs)
        self.max_depth = int(max_depth)
        self.num_workers = int(num_workers) if num_workers else 2
        self.batch_size = int(batch_size)
        
        # Shutdown flag for graceful termination
        self.shutdown_requested = False
        
        # Generate timestamped filenames if not provided
        self.scraped_urls_file = scraped_urls_file or generate_timestamped_filename("logs/scraped_urls")
        self.pending_urls_file = pending_urls_file or generate_timestamped_filename("logs/pending_urls")
        self.errored_urls_file = errored_urls_file or generate_timestamped_filename("logs/errored_urls")
        self.log_file = log_file or generate_timestamped_filename("logs/crawler_parallel")

        # Ensure logs directory exists
        self._ensure_directories()

        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Set up shared logging for main process (only if not already configured by Scrapy)
        self._setup_main_logging()

        # URL tracking
        self.scraped_urls: Set[str] = set()
        self.pending_urls: Set[Tuple[str, int]] = set()
        self.processing_urls: Set[str] = set()
        self.errored_urls: Set[str] = set()

        # Statistics
        self.total_processed = 0
        self.total_errors = 0
        self.total_items = 0

        # Load existing URLs
        self._load_scraped_urls()
        self._load_pending_urls()
        self._load_errored_urls()

        # Create spider config for workers
        self.spider_config = {
            "allowed_domains": self.allowed_domains,
            "playwright_wait_until": self.playwright_wait_until,
            "playwright_timeout": self.playwright_timeout,
            "playwright_wait_time": self.playwright_wait_time,
        }

        self.logger.info(f"Parallel spider initialized:")
        self.logger.info(f"  max_depth={self.max_depth}")
        self.logger.info(f"  num_workers={self.num_workers}")
        self.logger.info(f"  batch_size={self.batch_size}")
        self.logger.info(f"  scraped_urls_file={self.scraped_urls_file}")
        self.logger.info(f"  pending_urls_file={self.pending_urls_file}")
        self.logger.info(f"  errored_urls_file={self.errored_urls_file}")
        self.logger.info(f"  log_file={self.log_file}")
        self.logger.info(f"  Already scraped URLs: {len(self.scraped_urls)}")
        self.logger.info(f"  Pending URLs: {len(self.pending_urls)}")
        self.logger.info(f"  Errored URLs: {len(self.errored_urls)}")

    def _ensure_directories(self):
        """Ensure that all necessary directories exist."""
        directories_to_create = set()
        
        for file_path in [self.scraped_urls_file, self.pending_urls_file, 
                         self.errored_urls_file, self.log_file]:
            directory = os.path.dirname(file_path)
            if directory and directory != '.':
                directories_to_create.add(directory)
        
        for directory in directories_to_create:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {e}")

    def _setup_main_logging(self):
        """Set up shared logging configuration for the main process."""
        # Only set up our logging if Scrapy hasn't already configured logging
        root_logger = logging.getLogger()
        
        # Add our file handler for worker logs (separate from Scrapy's log)
        # This ensures worker process logs also go to our shared file
        file_handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            "%(asctime)s [PID:%(process)d] [%(processName)s] %(levelname)s: %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        # Only add console handler if not using Scrapy's file logging
        scrapy_log_file = getattr(self.settings, 'LOG_FILE', None) if hasattr(self, 'settings') else None
        
        if not scrapy_log_file:
            # No Scrapy log file configured, add console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Always add our file handler for worker process logs
        root_logger.addHandler(file_handler)
        root_logger.setLevel(logging.INFO)

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

    def _save_scraped_urls_batch(self, urls: List[str]):
        """Save multiple scraped URLs to file in batch."""
        new_urls = [url for url in urls if url not in self.scraped_urls]
        if new_urls:
            self.scraped_urls.update(new_urls)
            try:
                with open(self.scraped_urls_file, "a", encoding="utf-8") as f:
                    for url in new_urls:
                        f.write(f"{url}\n")
                self.logger.info(f"Saved {len(new_urls)} new scraped URLs")
            except Exception as e:
                self.logger.error(f"Error saving scraped URLs: {e}")

    def _save_errored_urls_batch(self, urls: List[str]):
        """Save multiple errored URLs to file in batch."""
        new_urls = [url for url in urls if url not in self.errored_urls]
        if new_urls:
            self.errored_urls.update(new_urls)
            try:
                with open(self.errored_urls_file, "a", encoding="utf-8") as f:
                    for url in new_urls:
                        f.write(f"{url}\n")
                self.logger.info(f"Saved {len(new_urls)} new errored URLs")
            except Exception as e:
                self.logger.error(f"Error saving errored URLs: {e}")

    def _add_pending_urls_batch(self, url_depth_pairs: List[Tuple[str, int]]):
        """Add multiple URLs to pending queue in batch."""
        new_pairs = []
        for url, depth in url_depth_pairs:
            if (
                url not in self.scraped_urls
                and url not in self.errored_urls
                and url not in self.processing_urls
            ):
                if (url, depth) not in self.pending_urls:
                    new_pairs.append((url, depth))
                    self.pending_urls.add((url, depth))

        if new_pairs:
            try:
                with open(self.pending_urls_file, "a", encoding="utf-8") as f:
                    for url, depth in new_pairs:
                        f.write(f"{url}|{depth}\n")
                self.logger.info(f"Added {len(new_pairs)} new pending URLs")
            except Exception as e:
                self.logger.error(f"Error saving pending URLs: {e}")

    def _remove_pending_urls_batch(self, urls: List[str]):
        """Remove multiple URLs from pending queue in batch."""
        # Remove all entries with these URLs
        to_remove = [item for item in self.pending_urls if item[0] in urls]
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

    def _get_next_batch(self) -> List[Tuple[str, int]]:
        """Get the next batch of URLs to process."""
        batch = []
        batch_urls = set()

        # Get URLs from pending queue
        pending_list = list(self.pending_urls)
        pending_list.sort(key=lambda x: x[1])  # Sort by depth

        for url, depth in pending_list:
            if len(batch) >= self.batch_size:
                break
            if url not in self.scraped_urls and url not in self.processing_urls:
                batch.append((url, depth))
                batch_urls.add(url)
                self.processing_urls.add(url)

        return batch

    def process_batch_parallel(
        self, batch: List[Tuple[str, int]]
    ) -> List[Dict[str, Any]]:
        """Process a batch of URLs in parallel using multiprocessing."""
        if not batch:
            return []

        self.logger.info(
            f"Processing batch of {len(batch)} URLs with {self.num_workers} workers"
        )

        # Prepare arguments for workers
        worker_args = []
        for url, depth in batch:
            task_id = str(uuid.uuid4())[:8]  # Short unique ID for each task
            worker_args.append((url, depth, self.spider_config, task_id))

        results = []

        try:
            # Check if we should use console logging for workers
            scrapy_log_file = getattr(self.settings, 'LOG_FILE', None) if hasattr(self, 'settings') else None
            use_console = not scrapy_log_file  # Don't use console if Scrapy is logging to file
            
            with ProcessPoolExecutor(
                max_workers=self.num_workers,
                initializer=init_worker,
                initargs=(self.log_file, use_console),  # Pass log file path and console preference
            ) as executor:
                # Submit all tasks
                future_to_url = {
                    executor.submit(process_url_worker, args): args[0]
                    for args in worker_args
                }

                # Collect results as they complete
                for future in as_completed(future_to_url):
                    # Check for shutdown request
                    if self.shutdown_requested:
                        self.logger.info("Shutdown requested, cancelling remaining tasks...")
                        
                        # Cancel all pending futures
                        for f in future_to_url:
                            if not f.done():
                                f.cancel()
                        
                        # Shutdown executor immediately
                        executor.shutdown(wait=False)
                        
                        # Add partial results for URLs that didn't complete
                        completed_urls = {future_to_url[r] for r in results}
                        for f, url in future_to_url.items():
                            if url not in completed_urls and not f.done():
                                results.append({
                                    "url": url,
                                    "success": False,
                                    "error": "Cancelled due to shutdown",
                                    "processing_time": 0,
                                    "depth": next((depth for u, depth in batch if u == url), 0)
                                })
                        
                        self.logger.info(f"Cancelled batch processing with {len(results)} partial results")
                        return results
                    
                    url = future_to_url[future]
                    try:
                        result = future.result(timeout=60)  # 60 second timeout per URL
                        results.append(result)

                        if result["success"]:
                            self.logger.info(
                                f"✓ Completed: {url} (depth {result['depth']}) - {result['processing_time']:.2f}s"
                            )
                        else:
                            self.logger.warning(f"✗ Failed: {url} - {result['error']}")

                    except Exception as e:
                        self.logger.error(f"✗ Worker exception for {url}: {e}")
                        results.append(
                            {
                                "url": url,
                                "success": False,
                                "error": str(e),
                                "processing_time": 0,
                                "depth": next((depth for u, depth in batch if u == url), 0)
                            }
                        )

        except Exception as e:
            self.logger.error(f"Error in parallel processing: {e}")
            if self.shutdown_requested:
                self.logger.info("Error occurred during shutdown, this is expected.")

        return results

    def start_requests(self):
        """Generate initial requests and start parallel processing."""
        # Add start URLs to pending if not already processed
        for url in self.start_urls:
            if url not in self.scraped_urls and url not in self.errored_urls:
                self._add_pending_urls_batch([(url, 0)])

        # Main processing loop
        while True:
            # Check for shutdown request
            if self.shutdown_requested:
                self.logger.info("Shutdown requested, exiting main processing loop...")
                break
                
            # Get next batch of URLs to process
            batch = self._get_next_batch()

            if not batch:
                self.logger.info("No more URLs to process")
                break

            # Process batch in parallel
            results = self.process_batch_parallel(batch)
            
            # If shutdown was requested during processing, handle gracefully
            if self.shutdown_requested:
                self.logger.info("Processing shutdown request...")
                # Still process any completed results
                if results:
                    self.logger.info(f"Processing {len(results)} completed results before shutdown...")

            # Process results
            processed_urls = []
            errored_urls = []
            new_pending_urls = []
            items_yielded = 0

            for result in results:
                url = result["url"]
                depth = result.get("depth", 0)
                task_id = result.get("task_id", "unknown")

                # Remove from processing set
                self.processing_urls.discard(url)

                if result["success"]:
                    # Mark as processed
                    processed_urls.append(url)

                    # Yield the item
                    if result["item"]:
                        yield CrawlItem(result["item"])
                        items_yielded += 1

                    # Add new links to pending if within depth limit and not shutting down
                    if not self.shutdown_requested:
                        next_depth = depth + 1
                        if next_depth <= self.max_depth:
                            for link_url in result["links"]:
                                if (
                                    link_url not in self.scraped_urls
                                    and link_url not in self.errored_urls
                                ):
                                    new_pending_urls.append((link_url, next_depth))

                    self.total_processed += 1
                    self.total_items += 1
                    self.logger.info(
                        f"[TASK:{task_id}] ✓ Main process: Item yielded for {url} - Title: {result['item'].get('title', 'N/A')[:100]}"
                    )
                else:
                    # Mark as errored
                    errored_urls.append(url)
                    self.total_errors += 1
                    self.logger.warning(
                        f"[TASK:{task_id}] ✗ Main process: Failed processing {url} - {result.get('error', 'Unknown error')}"
                    )

            # Update files in batch
            if processed_urls:
                self._save_scraped_urls_batch(processed_urls)
                self._remove_pending_urls_batch(processed_urls)

            if errored_urls:
                self._save_errored_urls_batch(errored_urls)
                self._remove_pending_urls_batch(errored_urls)

            if new_pending_urls and not self.shutdown_requested:
                self._add_pending_urls_batch(new_pending_urls)

            # Log progress
            self.logger.info(
                f"Batch complete: {len(results)} URLs processed, {items_yielded} items yielded"
            )
            self.logger.info(
                f"Progress: {self.total_processed} processed, {self.total_errors} errors, {len(self.pending_urls)} pending"
            )
            
            # Exit if shutdown requested
            if self.shutdown_requested:
                self.logger.info("Graceful shutdown completed.")
                break

            # Small delay between batches
            time.sleep(1)

    def parse(self, response):
        """This method is not used in parallel version - processing happens in workers."""
        pass

    def closed(self, reason):
        """Called when the spider is closed."""
        self.logger.info(f"Parallel spider closed: {reason}")
        
        if self.shutdown_requested:
            self.logger.info("Spider was shut down gracefully via signal (Ctrl+C)")
        
        self.logger.info(f"Final statistics:")
        self.logger.info(f"  Total URLs processed: {self.total_processed}")
        self.logger.info(f"  Total items yielded: {self.total_items}")
        self.logger.info(f"  Total errors: {self.total_errors}")
        self.logger.info(f"  URLs scraped: {len(self.scraped_urls)}")
        self.logger.info(f"  URLs errored: {len(self.errored_urls)}")
        self.logger.info(f"  Pending URLs remaining: {len(self.pending_urls)}")

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

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle signal for graceful shutdown."""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        self.logger.info(f"Received {signal_name}. Requesting graceful shutdown...")
        self.shutdown_requested = True
