"""
Example configurations for using different storage pipelines with Louis Crawler spiders.

These examples show how to configure your spiders to use different storage backends:
- Database storage (default)
- Disk storage (for local development)  
- S3 storage (for cloud deployment)
"""

# Example 1: Database Storage (Default)
# Best for: Production environments with PostgreSQL database
DATABASE_PIPELINE_CONFIG = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.LouisPipeline': 300,
    },
    'LOG_LEVEL': 'INFO',
}

# Example 2: Disk Storage Only
# Best for: Local development, testing, or when database is unavailable
DISK_PIPELINE_CONFIG = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.DiskPipeline': 300,
    },
    'LOG_LEVEL': 'INFO',
}

# Example 3: S3 Storage with Disk Fallback
# Best for: Cloud deployments, distributed systems
S3_PIPELINE_CONFIG = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.S3Pipeline': 300,
    },
    'LOG_LEVEL': 'INFO',
}

# Example 4: Multiple Pipelines (Database + Disk Backup)
# Best for: High-reliability scenarios where you want multiple storage backends
DUAL_PIPELINE_CONFIG = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.LouisPipeline': 300,   # Database (primary)
        'louis.crawler.pipelines.DiskPipeline': 400,    # Disk (backup)
    },
    'LOG_LEVEL': 'INFO',
}

# Example 5: Complete Spider Configuration with Disk Storage
class ExampleGoldieSpider:
    """Example spider configuration using disk storage"""
    
    name = "example_goldie"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/en"]
    
    # Use disk storage instead of database
    custom_settings = {
        'ITEM_PIPELINES': {
            'louis.crawler.pipelines.DiskPipeline': 300,
        },
        'LOG_LEVEL': 'INFO',
        'DOWNLOAD_DELAY': 1,  # Be respectful to the server
    }

# Example 6: Parallel Spider with S3 Storage
class ExampleParallelSpider:
    """Example parallel spider configuration using S3 storage"""
    
    name = "example_parallel"
    allowed_domains = ["inspection.gc.ca", "inspection.canada.ca"]
    start_urls = ["https://inspection.canada.ca/en"]
    
    # Use S3 storage for cloud deployment
    custom_settings = {
        'LOG_FILE': 'logs/scrapy.log',
        'LOG_LEVEL': 'INFO',
        'LOG_STDOUT': False,
        'ITEM_PIPELINES': {
            'louis.crawler.pipelines.S3Pipeline': 300,
        },
    }

# Example 7: Environment-based Pipeline Selection
def get_pipeline_config(environment='development'):
    """
    Return pipeline configuration based on environment.
    
    Args:
        environment: 'development', 'staging', or 'production'
    
    Returns:
        dict: Pipeline configuration
    """
    if environment == 'development':
        return DISK_PIPELINE_CONFIG
    elif environment == 'staging':
        return S3_PIPELINE_CONFIG
    elif environment == 'production':
        return DUAL_PIPELINE_CONFIG
    else:
        return DATABASE_PIPELINE_CONFIG

# Example 8: Runtime Pipeline Switching
def create_spider_settings(storage_backend='database'):
    """
    Create spider settings with specified storage backend.
    
    Args:
        storage_backend: 'database', 'disk', 's3', or 'dual'
    
    Returns:
        dict: Spider custom_settings
    """
    base_settings = {
        'LOG_LEVEL': 'INFO',
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 8,
    }
    
    if storage_backend == 'database':
        base_settings['ITEM_PIPELINES'] = {
            'louis.crawler.pipelines.LouisPipeline': 300,
        }
    elif storage_backend == 'disk':
        base_settings['ITEM_PIPELINES'] = {
            'louis.crawler.pipelines.DiskPipeline': 300,
        }
    elif storage_backend == 's3':
        base_settings['ITEM_PIPELINES'] = {
            'louis.crawler.pipelines.S3Pipeline': 300,
        }
    elif storage_backend == 'dual':
        base_settings['ITEM_PIPELINES'] = {
            'louis.crawler.pipelines.LouisPipeline': 300,
            'louis.crawler.pipelines.DiskPipeline': 400,
        }
    
    return base_settings

# Example Usage in Spider
"""
To use these configurations in your spider:

1. Direct configuration:
class MySpider(scrapy.Spider):
    custom_settings = DISK_PIPELINE_CONFIG

2. Environment-based:
class MySpider(scrapy.Spider):
    custom_settings = get_pipeline_config('production')

3. Runtime switching:
class MySpider(scrapy.Spider):
    def __init__(self, storage='disk', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_settings = create_spider_settings(storage)

4. Command line usage:
scrapy crawl goldie -a storage=s3
scrapy crawl goldie_playwright_parallel -a storage=disk
""" 