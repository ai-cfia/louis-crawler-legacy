# S3 Object Storage Support for Louis Crawler

Louis crawler now supports S3-compatible object storage using [MinIO](https://github.com/minio/minio-py) as a third storage option alongside PostgreSQL database and local disk storage.

## Features

- ✅ Store HTML content and metadata to S3-compatible object storage
- ✅ Simple storage modes: choose one of `s3`, `database`, or `disk`
- ✅ Automatic bucket creation and management
- ✅ Organized storage with prefixes: `html/` and `metadata/`
- ✅ Compatible with MinIO, AWS S3, and other S3-compatible services

## Installation

Install the MinIO Python SDK:

```bash
pip install minio
# or with uv
uv pip install minio
```

## Configuration

Configure S3 storage using environment variables:

```bash
# Required: Set storage mode (only one at a time)
export STORAGE_MODE=s3                    # S3 only
export STORAGE_MODE=database             # PostgreSQL only
export STORAGE_MODE=disk                 # Local disk only

# S3 connection settings (with defaults)
export S3_ENDPOINT=localhost:9000        # MinIO endpoint
export S3_ACCESS_KEY=minioadmin          # Access key
export S3_SECRET_KEY=minioadmin          # Secret key
export S3_BUCKET_NAME=louis-crawler      # Bucket name
export S3_SECURE=false                   # Use HTTPS (true/false)
```

## Storage Structure

Files are stored in the bucket with organized prefixes:

```
bucket-name/
├── html/
│   ├── uuid1.html              # HTML content
│   ├── uuid2.html
│   └── ...
└── metadata/
    ├── uuid1.json              # Metadata (title, url, timestamps, etc.)
    ├── uuid2.json
    └── ...
```

For example, a file named `test_file.html` would be stored as:
- HTML content: `html/12345678-1234-1234-1234-123456789abc.html`
- Metadata: `metadata/12345678-1234-1234-1234-123456789abc.json`

## Quick Start with MinIO

1. **Start MinIO server** (using Docker):
```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ':9001'
```

2. **Set environment variables**:
```bash
export STORAGE_MODE=s3
export S3_ENDPOINT=localhost:9000
export S3_ACCESS_KEY=minioadmin
export S3_SECRET_KEY=minioadmin
export S3_BUCKET_NAME=louis-crawler
```

3. **Run the example**:
```bash
python s3_example.py
```

4. **View stored objects** in MinIO Console at http://localhost:9001
   - Login: `minioadmin` / `minioadmin`

## API Usage

```python
from louis.db import (
    initialize_database,
    store_crawl_item,
    load_from_s3,
    list_s3_items
)

# Initialize S3 storage
initialize_database()

# Store a crawl item
item = {
    'url': 'https://example.com',
    'title': 'Example Page',
    'lang': 'en',
    'html_content': '<html>...</html>',
    'last_crawled': 1234567890,
    'last_updated': '2024-01-01T00:00:00'
}

result = store_crawl_item(None, item)  # None cursor for S3-only
print(f"Stored with ID: {result['id']}")

# Load item back
loaded = load_from_s3(result['id'])
print(f"Loaded: {loaded['title']}")

# List all stored items
items = list_s3_items()
print(f"Found {len(items)} items")
```

## Storage Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `s3` | S3 only | Cloud-native, scalable storage |
| `database` | PostgreSQL only | Traditional database with full SQL queries |
| `disk` | Local disk only | Simple file-based storage, no dependencies |

## Benefits of S3 Storage

- **Scalability**: Handle massive amounts of crawled data
- **Durability**: Built-in redundancy and data protection
- **Cost-effective**: Pay only for what you store
- **Cloud-native**: Easy integration with cloud workflows
- **Compatibility**: Works with AWS S3, MinIO, and other S3-compatible services

## Production Considerations

1. **Security**: Use proper access keys and enable HTTPS in production
2. **Performance**: Consider network latency for high-frequency operations
3. **Costs**: Monitor storage and transfer costs with cloud providers
4. **Backup**: Implement proper backup strategies for critical data
5. **Monitoring**: Set up monitoring for bucket operations and errors

## Troubleshooting

### Common Issues

1. **MinIO not available**: Install with `pip install minio`
2. **Connection failed**: Check endpoint, credentials, and network connectivity
3. **Bucket not found**: The library auto-creates buckets, check permissions
4. **SSL/TLS errors**: Set `S3_SECURE=false` for local MinIO or configure certificates

### Environment Variables Check

```python
import os
print("S3 Configuration:")
for key in ['STORAGE_MODE', 'S3_ENDPOINT', 'S3_ACCESS_KEY', 'S3_SECRET_KEY', 'S3_BUCKET_NAME', 'S3_SECURE']:
    print(f"  {key}={os.getenv(key, 'NOT SET')}")
```
