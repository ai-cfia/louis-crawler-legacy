# Parallel Playwright Spider - Complete Guide

This guide covers the `goldie_playwright_parallel` spider, which provides parallel processing capabilities with comprehensive logging and monitoring features.

## Overview

The `goldie_playwright_parallel` spider is an enhanced version of the regular `goldie_playwright` spider that:
- Uses multiple CPU cores for concurrent URL processing
- Implements shared logging across all worker processes with unique task IDs
- Provides resume capability and URL tracking
- Includes comprehensive monitoring and debugging tools

## Quick Start

### Basic Usage
```bash
# Default settings (depth=1, CPU core count workers)
scrapy crawl goldie_playwright_parallel

# Custom depth and workers
scrapy crawl goldie_playwright_parallel -a max_depth=2 -a num_workers=4

# All logs to files, no console output
scrapy crawl goldie_playwright_parallel -a max_depth=1 -a num_workers=2
```

### Alternative: CrawlerProcess Method
```python
from scrapy.crawler import CrawlerProcess
from louis.crawler.spiders.goldie_playwright_parallel import GoldiePlaywrightParallelSpider

process = CrawlerProcess()
process.crawl(GoldiePlaywrightParallelSpider, max_depth=2, num_workers=4)
process.start()
```

## Parameters

All parameters can be passed using the `-a` flag:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_depth` | 1 | Maximum crawl depth (0 = start URLs only) |
| `num_workers` | CPU count | Number of worker processes |
| `batch_size` | 10 | URLs processed per batch |
| `scraped_urls_file` | "logs/scraped_urls.txt" | Track completed URLs |
| `pending_urls_file` | "logs/pending_urls.txt" | Track pending URLs |
| `errored_urls_file` | "logs/errored_urls.txt" | Track failed URLs |
| `log_file` | "logs/crawler_parallel.log" | Shared worker log file |

## Logging System

### Default Logging Behavior
The spider automatically configures logging with no console output for clean execution:

- **Scrapy logs**: `logs/scrapy.log` (main spider lifecycle, stats, errors)
- **Worker logs**: `logs/crawler_parallel.log` (task-specific processing with task IDs)
- **Console output**: Disabled by default

### File Structure
```
logs/
├── scrapy.log                 # Main Scrapy log (spider lifecycle, stats, errors)
├── crawler_parallel.log       # Worker process logs with task IDs
├── scraped_urls.txt           # Successfully processed URLs
├── pending_urls.txt           # URLs waiting to be processed
└── errored_urls.txt           # URLs that failed processing
```

### Log Contents

#### `logs/scrapy.log` - Main Spider Log
```
2025-01-15 15:16:35 [scrapy.utils.log] INFO: Scrapy 2.13.0 started (bot: louis)
2025-01-15 15:16:35 [goldie_playwright_parallel] INFO: Parallel spider initialized:
2025-01-15 15:16:35 [goldie_playwright_parallel] INFO:   max_depth=1
2025-01-15 15:16:45 [scrapy.core.engine] INFO: Spider closed (finished)
```

#### `logs/crawler_parallel.log` - Worker Process Log
```
2025-01-15 15:30:01,123 [PID:12345] [ForkProcess-1] INFO: [TASK:abc12345] Processing URL (depth 1): https://example.com/page1
2025-01-15 15:30:01,345 [PID:12345] [ForkProcess-1] INFO: [TASK:abc12345] Navigating to https://example.com/page1
2025-01-15 15:30:02,456 [PID:12345] [ForkProcess-1] INFO: [TASK:abc12345] Page loaded successfully, status: 200
2025-01-15 15:30:05,901 [PID:12345] [ForkProcess-1] INFO: [TASK:abc12345] Successfully processed https://example.com/page1 in 4.78s - found 15 links
```

## Usage Examples

### Basic Crawling
```bash
# Crawl only start URLs
scrapy crawl goldie_playwright_parallel -a max_depth=0

# Crawl start URLs + their links (default)
scrapy crawl goldie_playwright_parallel -a max_depth=1

# Deep crawl (2 levels)
scrapy crawl goldie_playwright_parallel -a max_depth=2
```

### Performance Tuning
```bash
# Use more workers for faster processing
scrapy crawl goldie_playwright_parallel -a num_workers=8

# Process larger batches
scrapy crawl goldie_playwright_parallel -a batch_size=20

# Conservative settings for limited resources
scrapy crawl goldie_playwright_parallel -a num_workers=2 -a batch_size=5
```

### Custom File Locations
```bash
# Custom log and tracking files
scrapy crawl goldie_playwright_parallel \
    -a log_file="custom_logs/crawl.log" \
    -a scraped_urls_file="data/completed.txt" \
    -a pending_urls_file="data/pending.txt"
```

### Output Options
```bash
# Save items to JSON file
scrapy crawl goldie_playwright_parallel -o items.json

# Save to CSV
scrapy crawl goldie_playwright_parallel -o items.csv

# Full configuration with output
scrapy crawl goldie_playwright_parallel \
    -a max_depth=2 \
    -a num_workers=4 \
    -o output/crawl_results.jsonl
```

## Custom Logging Options

### Custom Log File Locations
```bash
# Custom Scrapy log location
scrapy crawl goldie_playwright_parallel --logfile custom/scrapy.log

# Custom worker log location
scrapy crawl goldie_playwright_parallel -a log_file="custom/workers.log"

# Both custom
scrapy crawl goldie_playwright_parallel \
    --logfile custom/scrapy.log \
    -a log_file="custom/workers.log"
```

### Enable Console Output
If you want to see logs on console AND save to files:
```bash
# Method 1: Don't use --logfile (uses built-in file logging)
scrapy crawl goldie_playwright_parallel -a max_depth=1

# Method 2: Override spider settings
scrapy crawl goldie_playwright_parallel \
    -s LOG_STDOUT=True \
    -a max_depth=1
```

### Different Log Levels
```bash
# More verbose logging
scrapy crawl goldie_playwright_parallel --loglevel DEBUG

# Less verbose logging  
scrapy crawl goldie_playwright_parallel --loglevel WARNING

# Only errors
scrapy crawl goldie_playwright_parallel --loglevel ERROR
```

## Monitoring & Analysis

### Real-time Monitoring
```bash
# Monitor main spider log
tail -f logs/scrapy.log

# Monitor worker processes  
tail -f logs/crawler_parallel.log

# Monitor both simultaneously
tail -f logs/scrapy.log logs/crawler_parallel.log

# Start crawl in background and monitor logs
scrapy crawl goldie_playwright_parallel -a max_depth=2 &
tail -f logs/crawler_parallel.log
```

### Log Analysis
```bash
# Analyze completed crawl
python log_analyzer.py logs/crawler_parallel.log

# Check specific task
python log_analyzer.py logs/crawler_parallel.log abc12345

# Find task IDs
grep -o "TASK:[a-f0-9]\{8\}" logs/crawler_parallel.log | sort | uniq

# Check spider statistics
grep "statistics" logs/scrapy.log

# Find errors across all logs
grep -i error logs/*.log
```

### Performance Analysis
```bash
# Check processing status
grep "Successfully processed" logs/crawler_parallel.log | wc -l

# Find errors
grep "Error processing" logs/crawler_parallel.log

# Check worker distribution
grep "PID:" logs/crawler_parallel.log | cut -d']' -f1 | sort | uniq -c
```

## Key Features

### Shared Logging with Task IDs
- All worker processes write to the same log file
- Each URL gets a unique 8-character task ID for tracking
- Easy debugging and progress tracking
- Process IDs included for worker identification

### Resume Capability
- Automatically skips previously scraped URLs
- Resumes from pending URLs on restart
- Tracks failed URLs separately for retry logic
- Persistent URL tracking across sessions

### Multiprocessing
- Uses multiple CPU cores for parallel processing
- Configurable worker count and batch sizes
- Efficient resource utilization

### Task Tracking
- Unique 8-character task ID for each URL processing task
- Complete traceability from worker to main process
- Easy debugging of specific URL processing issues

## URL Tracking & Resume

### File Formats
The URL tracking files are simple text files with one URL per line:
```text
https://inspection.canada.ca/en
https://inspection.canada.ca/en/food/imports
https://inspection.canada.ca/en/animal-health
```

### Managing URL Files
```bash
# View scraped URLs
cat logs/scraped_urls.txt

# Count scraped URLs
wc -l logs/scraped_urls.txt

# Clear URL history (start fresh)
rm logs/scraped_urls.txt

# Backup URL file
cp logs/scraped_urls.txt logs/scraped_urls_backup.txt
```

### Resume Interrupted Crawls
The spider supports resuming interrupted crawls:
1. URLs are tracked in persistent files
2. Previously scraped URLs are automatically skipped  
3. Pending URLs are resumed from where crawling stopped
4. Error URLs are tracked separately for retry logic

## Troubleshooting

### No Log Files Created
```bash
# Ensure logs directory exists
mkdir -p logs

# Check permissions
ls -la logs/
```

### Still Seeing Console Output
```bash
# Force file-only logging
scrapy crawl goldie_playwright_parallel \
    --logfile logs/scrapy.log \
    --loglevel INFO \
    -s LOG_STDOUT=False
```

### Large Log Files
```bash
# Monitor log file sizes
du -h logs/*.log

# Rotate logs (manual)
mv logs/scrapy.log logs/scrapy.log.old
mv logs/crawler_parallel.log logs/crawler_parallel.log.old
```

### Common Issues

**Spider not found:**
```bash
# Check if spider is discoverable
scrapy list | grep parallel
```

**Permission errors:**
```bash
# Ensure logs directory exists and is writable
mkdir -p logs
chmod 755 logs
```

**Memory usage:**
```bash
# Reduce workers and batch size
scrapy crawl goldie_playwright_parallel -a num_workers=2 -a batch_size=5
```

**Browser launch failures:**
```bash
# Install Playwright browsers
playwright install chromium
```

### Debug Mode
Enable debug logging to see detailed URL tracking:
```bash
scrapy crawl goldie_playwright_parallel -a max_depth=1 -L DEBUG
```

## Best Practices

1. **Default Usage**: Use the spider's built-in file logging for clean output
2. **Development**: Add console output when debugging specific issues  
3. **Production**: Always use file logging with appropriate log levels
4. **Monitoring**: Use `tail -f` for real-time monitoring
5. **Analysis**: Use the log analyzer for post-crawl analysis
6. **Start Small**: Begin with default settings and adjust based on performance
7. **Monitor Resources**: Watch CPU and memory usage during crawling
8. **Use Task IDs**: Reference task IDs when debugging specific URL issues
9. **Regular Cleanup**: Archive or rotate log files for long-running crawls
10. **Resume Friendly**: Use consistent file paths for resumable crawls

## Comparison with Regular Spider

| Feature | goldie_playwright | goldie_playwright_parallel |
|---------|------------------|---------------------------|
| Processing | Single process | Multiple worker processes |
| Logging | Standard Scrapy logs | Shared log file with task IDs |
| Resume | No | Yes, with file tracking |
| Performance | Limited by single core | Scales with CPU cores |
| URL Tracking | Basic Scrapy deduplication | Persistent file-based tracking |
| Monitoring | Basic Scrapy stats | Detailed task-level tracking |

## Integration

The parallel spider integrates seamlessly with:
- Scrapy pipelines and settings
- Custom middleware
- Standard Scrapy CLI commands
- Scrapy Cloud and deployment tools
- Feed exports and output formats

Simply replace `goldie_playwright` with `goldie_playwright_parallel` in your existing commands and add parallel-specific parameters as needed!

## Performance Considerations

### Memory Usage
- URL set is kept in memory for fast lookups
- For very large crawls (100k+ URLs), this may use significant memory
- Consider clearing the URL file periodically for long-running crawls

### File I/O
- Each new URL is appended to file immediately
- This ensures URLs are saved even if spider crashes
- For high-frequency crawling, this might create I/O overhead

### Optimization Tips
```bash
# For large crawls, use a dedicated file per crawl session
scrapy crawl goldie_playwright_parallel \
    -a scraped_urls_file="crawl_$(date +%Y%m%d_%H%M%S).txt"

# Monitor file size
ls -lh logs/*.log

# Clean up old files
find . -name "logs/*.txt" -mtime +30 -delete
``` 