# Louis Crawler - File Documentation

This document explains the purpose and functionality of each file in the `louis/crawler` directory. The Louis Crawler is a Scrapy-based web scraping framework specifically designed to crawl Canadian government inspection websites, extract content, chunk it for AI processing, and generate embeddings.

## Core Files

### `__init__.py`
**Purpose**: Package initialization file that loads environment variables using `dotenv.load_dotenv()`.
- Sets up the crawler package
- Loads environment variables from `.env` file for configuration

### `items.py`
**Purpose**: Defines Scrapy Item classes for structured data storage.

**Items Defined**:
- **`CrawlItem`**: Stores raw web page data with fields:
  - `id`: Unique identifier
  - `url`: Page URL
  - `title`: Page title
  - `lang`: Language (en/fr)
  - `html_content`: Raw HTML content
  - `last_crawled`: Timestamp of crawl
  - `last_updated`: Page last update timestamp

- **`ChunkItem`**: Stores processed text chunks with fields:
  - `url`: Source page URL
  - `title`: Chunk title/heading
  - `text_content`: Cleaned text content
  - `token_count`: Number of tokens in chunk
  - `tokens`: Tokenized representation

- **`EmbeddingItem`**: Stores AI embeddings with fields:
  - `token_id`: Reference to chunk token
  - `embedding`: Vector embedding data
  - `embedding_model`: Model used (e.g., 'text-embedding-ada-002')

### `settings.py`
**Purpose**: Scrapy configuration settings for the crawler.

**Key Configurations**:
- Bot name: "louis"
- User agent: Identifies as AI-CFIA project
- Robots.txt: Disabled (`ROBOTSTXT_OBEY = False`)
- Concurrent requests: Limited to 8
- Request headers: Accepts English and French content
- AutoThrottle: Enabled with conservative delays (5-60 seconds)
- Custom pipelines and middlewares: Configured for database storage

### `middlewares.py`
**Purpose**: Custom Scrapy middlewares for request/response processing.

**Classes**:
- **`LouisSpiderMiddleware`**: Basic spider middleware (standard implementation)
- **`LouisDownloaderMiddleware`**: Custom downloader middleware that:
  - Manages database connections
  - Routes different spiders to different data sources:
    - `goldie`: Serves cached files from local filesystem
    - `hawn`: Serves content from database crawl records
    - `kurt`: Serves chunk token data from database
  - Tracks page links and relationships

### `pipelines.py`
**Purpose**: Processes scraped items and stores them in the database.

**Class**:
- **`LouisPipeline`**: Main pipeline that:
  - Opens/closes database connections per spider
  - Routes items to appropriate database storage functions based on spider:
    - `goldie` spider → stores `CrawlItem`
    - `hawn` spider → stores `ChunkItem`  
    - `kurt` spider → stores `EmbeddingItem`

### `requests.py`
**Purpose**: URL extraction and processing utilities.

**Functions**:
- **`extract_urls(response, parse)`**: Extracts and processes URLs from page:
  - Filters out PDF files
  - Removes anchors and query parameters
  - Converts relative URLs to absolute
  - Normalizes domain names
  - Creates Scrapy Request objects with referer headers

- **`fix_vhost(url)`**: Normalizes domain variations:
  - Converts `inspection.gc.ca` to `inspection.canada.ca`
  - Standardizes HTTPS/HTTP protocols

### `responses.py`
**Purpose**: Creates fake Scrapy responses for testing and data replay.

**Functions**:
- **`fake_response_from_file(file_name, url)`**: Creates response from local HTML file
- **`response_from_crawl(row, url)`**: Creates response from database crawl record
- **`response_from_chunk_token(row, url)`**: Creates JSON response from chunk token data

### `chunking.py`
**Purpose**: Advanced HTML content processing and text chunking for AI consumption.

**Key Functions**:
- **`chunk_html(html_content)`**: Main function that processes HTML into 512-token chunks
- **`group_heading_by_block(soup)`**: Organizes content by headings (h1-h6) into logical blocks
- **`compute_tokens(block)`**: Calculates token count using tiktoken encoder (cl100k_base)
- **`split_chunk_into_subchunks(large_chunk)`**: Breaks oversized chunks into smaller pieces
- **`segment_blocks_into_chunks(blocks)`**: Optimally groups content blocks into target token sizes

**Process**:
1. Parses HTML with BeautifulSoup
2. Groups content by headings into hierarchical blocks
3. Calculates token counts for each block
4. Intelligently combines blocks to create ~512 token chunks
5. Preserves semantic structure and context

## Spider Files (`spiders/` directory)

### `spiders/__init__.py`
**Purpose**: Standard Scrapy spiders package initialization file.

### `spiders/goldie.py`
**Purpose**: Primary web crawler that fetches and stores raw HTML content.

**Target**: Canadian Food Inspection Agency websites (inspection.canada.ca)
**Process**:
1. Crawls from splash page
2. Extracts and cleans HTML content (removes sidebars, scripts, alerts)
3. Determines language (English/French) based on URL path
4. Creates `CrawlItem` with cleaned content
5. Extracts new URLs for further crawling

**Key Features**:
- Content cleaning using BeautifulSoup
- Language detection
- URL extraction and following

### `spiders/hawn.py`
**Purpose**: Content processing spider that converts stored HTML into text chunks.

**Target**: Previously crawled content from database
**Process**:
1. Reads HTML content from database via middleware
2. Uses `chunking.py` to break content into semantic chunks
3. Creates `ChunkItem` for each chunk with token information
4. Continues URL discovery for comprehensive processing

**Key Features**:
- Semantic text chunking
- Token counting
- Preserves content structure

### `spiders/kurt.py`
**Purpose**: Embedding generation spider that creates AI embeddings from text chunks.

**Target**: Chunk tokens from database without embeddings
**Process**:
1. Queries database for chunks needing embeddings
2. Fetches embeddings from OpenAI API (text-embedding-ada-002)
3. Creates `EmbeddingItem` with vector data
4. Respects API rate limits (1 concurrent request)

**Key Features**:
- OpenAI API integration
- Rate limiting for API compliance
- Database-driven processing queue

## Data Flow

1. **`goldie`** → Crawls websites → Stores raw HTML (`CrawlItem`)
2. **`hawn`** → Processes HTML → Creates semantic chunks (`ChunkItem`) 
3. **`kurt`** → Generates embeddings → Stores vectors (`EmbeddingItem`)

This pipeline enables the system to crawl government websites, process content for AI consumption, and generate embeddings for semantic search and retrieval.
