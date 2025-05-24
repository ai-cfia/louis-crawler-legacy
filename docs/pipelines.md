# Louis Crawler Pipelines

The Louis crawler provides three different storage pipelines to handle different storage backends. Each pipeline can be configured in your spider's `custom_settings` or in the main Scrapy settings.

## Available Pipelines

### 1. LouisPipeline (Database)
**Path**: `louis.crawler.pipelines.LouisPipeline`
**Purpose**: Stores items in a PostgreSQL database with automatic fallback to disk storage.

**Features**:
- Primary storage in PostgreSQL database
- Automatic fallback to disk if database unavailable
- Supports all spider types (goldie, hawn, kurt)
- Maintains database connections efficiently

**Configuration**:
```python
ITEM_PIPELINES = {
    'louis.crawler.pipelines.LouisPipeline': 300,
}
```

### 2. DiskPipeline (Local File Storage)
**Path**: `louis.crawler.pipelines.DiskPipeline`
**Purpose**: Stores items directly to local disk storage.

**Features**:
- Direct disk storage without database dependency
- Creates separate HTML and JSON metadata files
- Currently supports crawl items (goldie spiders)
- Uses UUID-based filenames for organization

**Storage Structure**:
```
data/
├── html/
│   └── {uuid}.html        # Raw HTML content
└── metadata/
    └── {uuid}.json        # Item metadata
```

**Configuration**:
```python
ITEM_PIPELINES = {
    'louis.crawler.pipelines.DiskPipeline': 300,
}
```

### 3. S3Pipeline (Cloud Storage)
**Path**: `louis.crawler.pipelines.S3Pipeline`
**Purpose**: Stores items to Amazon S3 with automatic fallback to disk storage.

**Features**:
- Primary storage in S3 bucket
- Automatic fallback to disk if S3 unavailable or misconfigured
- Requires S3 credentials and configuration
- Currently supports crawl items (goldie spiders)

**S3 Structure**:
```
bucket-name/
├── html/
│   └── {uuid}.html        # Raw HTML content
└── metadata/
    └── {uuid}.json        # Item metadata
```

**Configuration**:
```python
ITEM_PIPELINES = {
    'louis.crawler.pipelines.S3Pipeline': 300,
}
```

**Required Environment Variables**:
```bash
# S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_ENDPOINT_URL=https://s3.amazonaws.com  # Optional for custom endpoints
```

## Spider Support Matrix

| Pipeline | Goldie Spiders | Hawn Spider | Kurt Spider |
|----------|----------------|-------------|-------------|
| LouisPipeline | ✅ Full Support | ✅ Full Support | ✅ Full Support |
| DiskPipeline | ✅ Full Support | ⚠️ Not Yet Implemented | ⚠️ Not Yet Implemented |
| S3Pipeline | ✅ Full Support | ⚠️ Not Yet Implemented | ⚠️ Not Yet Implemented |

## Usage Examples

### Using Database Pipeline (Default)
```python
# In your spider's custom_settings
custom_settings = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.LouisPipeline': 300,
    },
}
```

### Using Disk Pipeline for Local Development
```python
# In your spider's custom_settings
custom_settings = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.DiskPipeline': 300,
    },
}
```

### Using S3 Pipeline for Production
```python
# In your spider's custom_settings
custom_settings = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.S3Pipeline': 300,
    },
}
```

### Multiple Pipelines (Advanced)
You can also run multiple pipelines simultaneously by assigning different priority numbers:

```python
custom_settings = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.LouisPipeline': 300,   # Database
        'louis.crawler.pipelines.DiskPipeline': 400,    # Disk backup
    },
}
```

## Pipeline Behavior

### Error Handling
- **LouisPipeline**: Falls back to disk storage if database connection fails
- **DiskPipeline**: Logs errors and returns original item if disk storage fails
- **S3Pipeline**: Falls back to disk storage if S3 operations fail

### Output Messages
Each pipeline provides clear console output with emojis for easy identification:
- 🗄️ Database operations
- 📁 Disk operations  
- ☁️ S3 operations
- ⚠️ Warnings
- ❌ Errors
- ✅ Success

### Storage Modes
The storage behavior is also influenced by the global storage mode configuration in your environment. See `louis.db.get_storage_mode()` for more details on how this affects the LouisPipeline's fallback behavior.

## Extending Pipelines

To add support for chunk items (hawn spider) or embedding items (kurt spider) to the disk and S3 pipelines, you would need to:

1. Implement `store_chunk_to_disk()` and `store_chunk_to_s3()` functions in `louis.db`
2. Implement `store_embedding_to_disk()` and `store_embedding_to_s3()` functions in `louis.db`  
3. Update the pipeline `process_item()` methods to handle these item types

The database pipeline already supports these through the existing `store_chunk_item()` and `store_embedding_item()` functions. 