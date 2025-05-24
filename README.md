# louis-crawler
Crawler related facilities

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up storage configuration:**
   Create a `.env` file with your storage preferences:
   ```bash
   # Storage Mode: 'database', 'disk', or 'both'
   STORAGE_MODE=disk

   # For disk storage
   STORAGE_DIRECTORY=./storage

   # For database storage (if using database or both modes)
   # Option 1: Full database URL
   DATABASE_URL=postgresql://username:password@localhost:5432/louis

   # Option 2: Individual variables  
   POSTGRES_DB=louis
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

3. **Initialize storage:**
   ```bash
   python scripts/init_db.py
   ```

## Storage Options

The crawler supports three storage modes:

### 🗄️ Database Storage (`STORAGE_MODE=database`)
- Stores HTML content and metadata in PostgreSQL
- Requires database setup and connection
- Good for structured queries and relationships

### 📁 Disk Storage (`STORAGE_MODE=disk`)
- Stores HTML as `.html` files with UUID filenames
- Stores metadata as `.json` files with matching UUIDs
- No database required
- Easy to browse and inspect files manually
- Example file structure:
  ```
  storage/
  ├── html/
  │   ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.html
  │   └── f9e8d7c6-b5a4-3210-9876-543210fedcba.html
  └── metadata/
      ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.json
      └── f9e8d7c6-b5a4-3210-9876-543210fedcba.json
  ```

### 🔄 Both Storage (`STORAGE_MODE=both`)
- Stores data in both database and disk simultaneously
- Provides redundancy and flexibility
- Allows switching between access methods

## Running the Goldie Crawler

The goldie crawler is the main spider that scrapes HTML content from Canadian government inspection websites.

```bash
scrapy crawl goldie
```

### Where scraped HTML is stored

Depending on your `STORAGE_MODE`:

**Database Storage:**
- **Table:** `crawl_items`
- **HTML field:** `html_content` - contains the cleaned HTML content
- **Other fields:** `url`, `title`, `lang` (en/fr), `last_crawled`, `last_updated`, `children` (links found on page)

**Disk Storage:**
- **HTML files:** `storage/html/{uuid}.html` - cleaned HTML content
- **Metadata files:** `storage/metadata/{uuid}.json` - contains URL, title, language, timestamps, and children links

### Data Pipeline

1. **goldie** - Crawls websites and stores raw HTML (`CrawlItem`)
2. **hawn** - Processes HTML into semantic text chunks (`ChunkItem`) 
3. **kurt** - Generates AI embeddings from chunks (`EmbeddingItem`)

## Storage Management

Use the storage manager utility to view and manage your crawled data:

```bash
# List stored items
python scripts/storage_manager.py list

# Search for items by URL or title
python scripts/storage_manager.py search "inspection"

# View a specific item by UUID
python scripts/storage_manager.py view a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Show storage statistics
python scripts/storage_manager.py stats
```

## Development

Run tests:
```bash
python -m pytest
```

## Database Schema

When using database storage, these tables are created:
- `crawl_items` - Raw HTML content from web pages with children links
- `chunk_items` - Processed text chunks with token information  
- `embedding_items` - AI embeddings for semantic search
- `page_links` - Link relationships between pages

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `STORAGE_MODE` | `database` | Storage mode: `database`, `disk`, or `both` |
| `STORAGE_DIRECTORY` | `storage` | Directory for disk storage (relative or absolute path) |
| `DATABASE_URL` | - | Full PostgreSQL connection URL |
| `POSTGRES_DB` | `louis` | Database name |
| `POSTGRES_USER` | `postgres` | Database username |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
