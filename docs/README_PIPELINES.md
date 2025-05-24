# Louis Crawler Storage Pipelines

This document summarizes the new storage pipeline functionality added to the Louis Crawler project.

## Overview

The Louis Crawler now supports **three different storage backends** through dedicated pipelines:

1. **Database Pipeline** (`LouisPipeline`) - PostgreSQL storage with disk fallback
2. **Disk Pipeline** (`DiskPipeline`) - Direct local file storage  
3. **S3 Pipeline** (`S3Pipeline`) - Amazon S3 cloud storage with disk fallback

## What Was Added

### New Pipeline Classes

**File**: `louis/crawler/pipelines.py`

- `DiskPipeline` - Stores items directly to local disk using the existing `db.store_to_disk()` function
- `S3Pipeline` - Stores items to S3 using the existing `db.store_to_s3()` function with automatic fallback to disk

Both new pipelines follow the same pattern as the existing `LouisPipeline` but are specialized for their respective storage backends.

### Documentation

**File**: `docs/pipelines.md`

Comprehensive documentation covering:
- Detailed explanation of each pipeline
- Configuration examples
- Spider support matrix
- Usage patterns
- Environment setup requirements

### Example Configurations

**File**: `examples/pipeline_configurations.py`

Ready-to-use configuration examples showing:
- Database-only storage
- Disk-only storage  
- S3-only storage
- Multi-pipeline setups
- Environment-based configuration
- Runtime pipeline switching

### Unit Tests

**File**: `tests/test_pipelines.py`

Complete test coverage for:
- All three pipeline classes
- Success and error scenarios
- S3 availability detection
- Fallback behavior
- Spider compatibility

## Key Features

### Automatic Fallback
- **S3Pipeline**: Falls back to disk storage if S3 is unavailable or fails
- **LouisPipeline**: Already had disk fallback for database failures

### Smart Configuration Detection
- **S3Pipeline**: Automatically detects S3 configuration and availability
- Graceful degradation when cloud services are unavailable

### Clear Status Messages
Each pipeline provides clear console output with emojis:
- 🗄️ Database operations
- 📁 Disk operations  
- ☁️ S3 operations
- ⚠️ Warnings and fallbacks
- ❌ Errors

### Spider Compatibility
| Pipeline | Goldie Spiders | Hawn Spider | Kurt Spider |
|----------|----------------|-------------|-------------|
| LouisPipeline | ✅ Full Support | ✅ Full Support | ✅ Full Support |
| DiskPipeline | ✅ Full Support | ⚠️ Not Yet Implemented | ⚠️ Not Yet Implemented |
| S3Pipeline | ✅ Full Support | ⚠️ Not Yet Implemented | ⚠️ Not Yet Implemented |

## Quick Start

### Use Disk Storage (No Database Required)
```python
custom_settings = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.DiskPipeline': 300,
    },
}
```

### Use S3 Storage (With Disk Fallback)
```python
custom_settings = {
    'ITEM_PIPELINES': {
        'louis.crawler.pipelines.S3Pipeline': 300,
    },
}
```

### Environment Variables for S3
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

### Command Line Usage
```bash
# Use disk storage
scrapy crawl goldie_playwright_parallel

# Or modify spider settings programmatically
# See examples/pipeline_configurations.py for details
```

## Benefits

1. **Flexibility**: Choose the storage backend that fits your deployment environment
2. **Reliability**: Automatic fallback ensures data is never lost
3. **Scalability**: S3 storage supports distributed and cloud deployments
4. **Development**: Disk storage eliminates database dependency for local development
5. **Backward Compatibility**: Existing database pipeline remains unchanged

## Future Enhancements

The new pipelines currently support crawl items (goldie spiders). Future improvements could include:

1. **Chunk Item Support**: Extend disk and S3 pipelines to handle chunk items from hawn spider
2. **Embedding Item Support**: Add support for embedding items from kurt spider  
3. **Compression**: Add optional compression for S3 storage
4. **Encryption**: Add client-side encryption for sensitive data
5. **Metadata Indexing**: Create searchable indexes for disk/S3 stored items

## Testing

All pipelines are fully tested:

```bash
source .venv/bin/activate
python -m pytest tests/test_pipelines.py -v
```

The test suite covers:
- Pipeline initialization and cleanup
- Successful storage operations
- Error handling and fallback behavior
- S3 availability detection
- Spider compatibility

## Files Modified/Created

### Modified
- `louis/crawler/pipelines.py` - Added DiskPipeline and S3Pipeline classes

### Created
- `docs/pipelines.md` - Comprehensive pipeline documentation
- `examples/pipeline_configurations.py` - Configuration examples
- `tests/test_pipelines.py` - Unit tests
- `README_PIPELINES.md` - This summary document

## Conclusion

The Louis Crawler now provides flexible, reliable storage options that can adapt to different deployment environments while maintaining backward compatibility and data integrity through automatic fallback mechanisms. 