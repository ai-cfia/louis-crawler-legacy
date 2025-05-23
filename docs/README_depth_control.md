# Depth Control and URL Tracking for Goldie Spiders

This document explains the new depth control and URL tracking features added to all three goldie spider variants.

## Features Overview

### 1. **Depth Control**
- Control how deep the spider crawls into linked pages
- `depth 0`: Only scrape the start URLs (no following of links)
- `depth 1`: Scrape start URLs + their direct links
- `depth 2`: Scrape start URLs + their links + links from those pages
- And so on...

### 2. **URL Tracking**
- Automatically track scraped URLs in a text file (one URL per line)
- Prevents duplicate scraping across multiple runs
- Resumable crawls - spider skips already scraped URLs
- Separate tracking files for each spider type

## Usage

### Command Line Arguments

All three spider variants now accept these arguments:

```bash
# Basic usage with depth control
scrapy crawl goldie_playwright -a max_depth=0    # Only start URLs
scrapy crawl goldie_playwright -a max_depth=1    # Start URLs + direct links
scrapy crawl goldie_playwright -a max_depth=2    # Two levels deep

# Custom URL tracking file
scrapy crawl goldie_playwright -a max_depth=1 -a scraped_urls_file="my_urls.txt"

# Both arguments together
scrapy crawl goldie_smart -a max_depth=2 -a scraped_urls_file="smart_crawl.txt"
```

### Default Settings

If you don't specify arguments, the defaults are:
- `max_depth=1`: Scrape start URLs and their direct links
- `scraped_urls_file`: Different for each spider:
  - `goldie_playwright`: `scraped_urls.txt`
  - `goldie_smart`: `scraped_urls_smart.txt`
  - `goldie_hybrid`: `scraped_urls_hybrid.txt`

## Examples

### Example 1: Only Scrape Start URLs (Depth 0)

```bash
scrapy crawl goldie_playwright -a max_depth=0
```

This will:
- Only scrape `https://inspection.canada.ca/en`
- Not follow any links from that page
- Save the URL to `scraped_urls.txt`

### Example 2: Two Levels Deep (Depth 2)

```bash
scrapy crawl goldie_smart -a max_depth=2 -a scraped_urls_file="deep_crawl.txt"
```

This will:
1. Scrape the start URL (depth 0)
2. Follow and scrape all links found on the start page (depth 1)
3. Follow and scrape all links found on those pages (depth 2)
4. Save all URLs to `deep_crawl.txt`

### Example 3: Resume Previous Crawl

If you run the same command twice:

```bash
scrapy crawl goldie_playwright -a max_depth=1
# ... spider runs and creates scraped_urls.txt

# Run again later
scrapy crawl goldie_playwright -a max_depth=1
```

The second run will:
- Load previously scraped URLs from `scraped_urls.txt`
- Skip URLs that have already been scraped
- Only process new URLs that weren't in the file

### Example 4: Different Spiders, Different Files

```bash
# Run different spiders with their own tracking
scrapy crawl goldie_playwright -a max_depth=1    # Uses scraped_urls.txt
scrapy crawl goldie_smart -a max_depth=1         # Uses scraped_urls_smart.txt
scrapy crawl goldie_hybrid -a max_depth=1        # Uses scraped_urls_hybrid.txt
```

Each spider maintains its own URL tracking file by default.

## URL Tracking File Format

The URL tracking files are simple text files with one URL per line:

```text
https://inspection.canada.ca/en
https://inspection.canada.ca/en/food/imports
https://inspection.canada.ca/en/animal-health
https://inspection.canada.ca/en/plants/plant-health
...
```

### Managing URL Files

```bash
# View scraped URLs
cat scraped_urls.txt

# Count scraped URLs
wc -l scraped_urls.txt

# Clear URL history (start fresh)
rm scraped_urls.txt

# Backup URL file
cp scraped_urls.txt scraped_urls_backup.txt

# Merge multiple URL files
cat scraped_urls*.txt | sort | uniq > merged_urls.txt
```

## Implementation Details

### Depth Tracking

Each request carries a `depth` value in its metadata:
- Start URLs begin at depth 0
- Links found on depth 0 pages become depth 1
- Links found on depth 1 pages become depth 2
- And so on...

### URL Deduplication

The spider tracks URLs in memory (set) and on disk (file):
1. On startup, load URLs from file into memory set
2. Before making any request, check if URL is in the set
3. After processing a response, add URL to set and append to file
4. Skip requests for URLs already in the set

### Error Handling

- If the URL file is corrupted, spider starts with empty set
- File I/O errors are logged but don't stop the spider
- Missing URL file is created automatically

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
scrapy crawl goldie_smart -a scraped_urls_file="crawl_$(date +%Y%m%d_%H%M%S).txt"

# Monitor file size
ls -lh scraped_urls*.txt

# Clean up old files
find . -name "scraped_urls*.txt" -mtime +30 -delete
```

## Advanced Usage

### Custom Depth Logic

You can extend the spiders to implement custom depth logic:

```python
class CustomGoldieSpider(GoldiePlaywrightSpider):
    def should_follow_link(self, url, current_depth):
        # Custom logic for which links to follow
        if "search" in url and current_depth >= 1:
            return False  # Don't follow search pages beyond depth 1
        return current_depth < self.max_depth
```

### URL Filtering

You can filter URLs before they're added to the tracking file:

```python
def _save_scraped_url(self, url):
    # Only save URLs that match certain criteria
    if self._should_track_url(url):
        super()._save_scraped_url(url)

def _should_track_url(self, url):
    # Don't track URLs with query parameters
    return '?' not in url
```

## Troubleshooting

### Common Issues

1. **URLs not being skipped**
   - Check if the URL file exists and is readable
   - Verify file permissions
   - Check spider logs for loading messages

2. **Memory usage too high**
   - Clear URL file periodically
   - Use smaller max_depth values
   - Consider implementing URL file rotation

3. **File corruption**
   - The spider handles this gracefully by starting with empty set
   - Backup important URL files
   - Use version control for critical crawl tracking

### Debug Mode

Enable debug logging to see detailed URL tracking:

```bash
scrapy crawl goldie_playwright -a max_depth=1 -L DEBUG
```

This will show:
- URLs being loaded from file
- URLs being skipped (already scraped)
- URLs being added to tracking
- Depth progression for each request

## Best Practices

1. **Start Small**: Begin with `max_depth=1` to understand the site structure
2. **Monitor Resources**: Watch memory and disk usage for large crawls
3. **Backup URL Files**: Keep backups of important tracking files
4. **Use Descriptive Names**: Use meaningful names for custom URL files
5. **Clean Up**: Remove old URL files to save disk space
6. **Test First**: Test depth settings on a small subset before large crawls

## Integration with Existing Workflows

These features are backward compatible:
- Existing spider commands work unchanged (use default depth=1)
- No breaking changes to spider interfaces
- URL tracking files are optional and can be ignored

The features integrate seamlessly with:
- Scrapy's built-in deduplication
- AutoThrottle settings
- Feed exports
- Custom pipelines
- Scrapy Cloud deployments 