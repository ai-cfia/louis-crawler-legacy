"""Database module for Louis crawler.

This module provides database connectivity and operations for storing
crawled data, chunks, and embeddings using PostgreSQL.
It also supports storing HTML content and metadata to disk as files.
"""
import os
import json
import uuid
from contextlib import contextmanager
from urllib.parse import urlencode, urlparse, parse_qs
from pathlib import Path

# Make psycopg import optional for disk-only storage
try:
    import psycopg
    from psycopg.rows import dict_row
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False
    print("Warning: psycopg not available. Database storage disabled.")


def get_storage_mode():
    """Get the storage mode from environment variables.
    
    Returns:
        str: 'database', 'disk', or 'both'
    """
    mode = os.getenv('STORAGE_MODE', 'database').lower()
    
    # Force disk mode if psycopg is not available
    if not PSYCOPG_AVAILABLE and mode in ['database', 'both']:
        print(f"Warning: psycopg not available, forcing disk storage mode")
        return 'disk'
    
    return mode


def get_storage_directory():
    """Get the directory for disk storage.
    
    Returns:
        Path: Path object for the storage directory
    """
    storage_dir = os.getenv('STORAGE_DIRECTORY', 'storage')
    return Path(storage_dir)


def ensure_storage_directories():
    """Create storage directories if they don't exist."""
    base_dir = get_storage_directory()
    html_dir = base_dir / 'html'
    metadata_dir = base_dir / 'metadata'
    
    html_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    return html_dir, metadata_dir


def store_to_disk(item):
    """Store a CrawlItem to disk as HTML and JSON files.
    
    Args:
        item: CrawlItem object with fields: url, title, lang, html_content, 
              last_crawled, last_updated
              
    Returns:
        dict: The stored item with generated id and file paths
    """
    html_dir, metadata_dir = ensure_storage_directories()
    
    # Generate UUID for filenames
    file_uuid = str(uuid.uuid4())
    
    # Prepare metadata (everything except html_content)
    metadata = {
        'id': file_uuid,
        'url': item.get('url'),
        'title': item.get('title'),
        'lang': item.get('lang'),
        'last_crawled': item.get('last_crawled'),
        'last_updated': item.get('last_updated'),
        'html_file': f"{file_uuid}.html",
        'metadata_file': f"{file_uuid}.json"
    }
    
    # Write HTML file
    html_file_path = html_dir / f"{file_uuid}.html"
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(item.get('html_content', ''))
    
    # Write metadata JSON file
    metadata_file_path = metadata_dir / f"{file_uuid}.json"
    with open(metadata_file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Add file paths to metadata
    metadata['html_file_path'] = str(html_file_path)
    metadata['metadata_file_path'] = str(metadata_file_path)
    
    return metadata


def load_from_disk(file_uuid):
    """Load a CrawlItem from disk using its UUID.
    
    Args:
        file_uuid: UUID string for the files
        
    Returns:
        dict: The item data with html_content loaded, or None if not found
    """
    html_dir, metadata_dir = ensure_storage_directories()
    
    metadata_file_path = metadata_dir / f"{file_uuid}.json"
    html_file_path = html_dir / f"{file_uuid}.html"
    
    if not metadata_file_path.exists() or not html_file_path.exists():
        return None
    
    # Load metadata
    with open(metadata_file_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Load HTML content
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Combine metadata and HTML content
    result = metadata.copy()
    result['html_content'] = html_content
    
    return result


def list_stored_items():
    """List all stored items on disk.
    
    Returns:
        list: List of metadata dictionaries for all stored items
    """
    html_dir, metadata_dir = ensure_storage_directories()
    
    items = []
    for metadata_file in metadata_dir.glob('*.json'):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                items.append(metadata)
        except (json.JSONDecodeError, IOError):
            # Skip corrupted files
            continue
    
    return sorted(items, key=lambda x: x.get('last_crawled', 0), reverse=True)


def connect_db():
    """Connect to the PostgreSQL database.
    
    Returns:
        psycopg.Connection: Database connection object or None if not available
    """
    if not PSYCOPG_AVAILABLE:
        print("Warning: Cannot connect to database - psycopg not available")
        return None
    
    # Try to get database URL from environment variable first
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return psycopg.connect(database_url, row_factory=dict_row)
    
    # Fallback to individual environment variables or defaults
    dbname = os.getenv('POSTGRES_DB', 'louis')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    
    return psycopg.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
        row_factory=dict_row
    )


@contextmanager
def cursor(connection):
    """Context manager for database cursors.
    
    Args:
        connection: Database connection object
        
    Yields:
        psycopg.Cursor: Database cursor
    """
    with connection.cursor() as cur:
        yield cur


def create_tables(connection):
    """Create database tables if they don't exist.
    
    Args:
        connection: Database connection object
    """
    with cursor(connection) as cur:
        # Create crawl_items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crawl_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                lang VARCHAR(2),
                html_content TEXT,
                last_crawled INTEGER,
                last_updated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create chunk_items table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chunk_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url TEXT NOT NULL,
                title TEXT,
                text_content TEXT,
                token_count INTEGER,
                tokens JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create embedding_items table  
        cur.execute("""
            CREATE TABLE IF NOT EXISTS embedding_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                token_id UUID NOT NULL REFERENCES chunk_items(id),
                embedding FLOAT8[] NOT NULL,
                embedding_model TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create page_links table for tracking relationships
        cur.execute("""
            CREATE TABLE IF NOT EXISTS page_links (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_url TEXT NOT NULL,
                destination_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_url, destination_url)
            )
        """)
        
        # Create indexes for performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_crawl_items_url ON crawl_items(url)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_items_url ON chunk_items(url)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_embedding_items_token_id ON embedding_items(token_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_page_links_source ON page_links(source_url)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_page_links_dest ON page_links(destination_url)")
        
        connection.commit()


def store_crawl_item_to_database(cur, item):
    """Store a CrawlItem in the database.
    
    Args:
        cur: Database cursor
        item: CrawlItem object with fields: url, title, lang, html_content, 
              last_crawled, last_updated
              
    Returns:
        dict: The stored item with generated id
    """
    # Use INSERT ... ON CONFLICT to handle duplicates
    cur.execute("""
        INSERT INTO crawl_items (url, title, lang, html_content, last_crawled, last_updated)
        VALUES (%(url)s, %(title)s, %(lang)s, %(html_content)s, %(last_crawled)s, %(last_updated)s)
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            lang = EXCLUDED.lang,
            html_content = EXCLUDED.html_content,
            last_crawled = EXCLUDED.last_crawled,
            last_updated = EXCLUDED.last_updated
        RETURNING *
    """, dict(item))
    
    result = cur.fetchone()
    return result


def store_crawl_item(cur, item):
    """Store a CrawlItem using the configured storage mode.
    
    Args:
        cur: Database cursor (may be None if disk-only mode)
        item: CrawlItem object with fields: url, title, lang, html_content, 
              last_crawled, last_updated
              
    Returns:
        dict: The stored item with generated id
    """
    storage_mode = get_storage_mode()
    result = None
    
    if storage_mode in ['database', 'both']:
        # Store to database
        if cur is not None:
            result = store_crawl_item_to_database(cur, item)
        else:
            print("Warning: Database cursor is None but database storage is requested")
    
    if storage_mode in ['disk', 'both']:
        # Store to disk
        disk_result = store_to_disk(item)
        if result is None:
            result = disk_result
        else:
            # Merge results if storing to both
            result.update({
                'disk_id': disk_result['id'],
                'html_file_path': disk_result['html_file_path'],
                'metadata_file_path': disk_result['metadata_file_path']
            })
    
    if result is None:
        # Fallback to database if no valid storage mode
        print(f"Warning: Invalid storage mode '{storage_mode}', falling back to database")
        result = store_crawl_item_to_database(cur, item)
    
    return result


def store_chunk_item(cur, item):
    """Store a ChunkItem in the database.
    
    Args:
        cur: Database cursor
        item: ChunkItem object with fields: url, title, text_content, 
              token_count, tokens
              
    Returns:
        dict: The stored item with generated id
    """
    cur.execute("""
        INSERT INTO chunk_items (url, title, text_content, token_count, tokens)
        VALUES (%(url)s, %(title)s, %(text_content)s, %(token_count)s, %(tokens)s)
        RETURNING *
    """, {
        'url': item['url'],
        'title': item['title'],
        'text_content': item['text_content'],
        'token_count': item['token_count'],
        'tokens': json.dumps(item['tokens'])  # Convert list to JSON
    })
    
    result = cur.fetchone()
    return result


def store_embedding_item(cur, item):
    """Store an EmbeddingItem in the database.
    
    Args:
        cur: Database cursor
        item: EmbeddingItem object with fields: token_id, embedding, embedding_model
        
    Returns:
        dict: The stored item with generated id
    """
    cur.execute("""
        INSERT INTO embedding_items (token_id, embedding, embedding_model)
        VALUES (%(token_id)s, %(embedding)s, %(embedding_model)s)
        RETURNING *
    """, {
        'token_id': item['token_id'],
        'embedding': item['embedding'],  # PostgreSQL can handle Python lists as arrays
        'embedding_model': item['embedding_model']
    })
    
    result = cur.fetchone()
    return result


def fetch_crawl_row(cur, url):
    """Fetch a crawl item by URL.
    
    Args:
        cur: Database cursor
        url: URL to fetch
        
    Returns:
        dict: Crawl item data or None if not found
    """
    cur.execute("SELECT * FROM crawl_items WHERE url = %s", (url,))
    return cur.fetchone()


def fetch_chunk_token_row(cur, url):
    """Fetch chunk token data by URL (parsed from PostgreSQL URL format).
    
    Args:
        cur: Database cursor  
        url: PostgreSQL URL format (postgresql://...)
        
    Returns:
        dict: Chunk token data or None if not found
    """
    # Parse the PostgreSQL URL to extract chunk ID
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2 and path_parts[0] == 'chunk':
        chunk_id = path_parts[1]
        
        # Get query parameters for encoding info
        query_params = parse_qs(parsed.query)
        encoding = query_params.get('encoding', ['cl100k_base'])[0]
        
        cur.execute("""
            SELECT id as token_id, tokens, token_count, title, text_content, url
            FROM chunk_items 
            WHERE id = %s
        """, (chunk_id,))
        
        row = cur.fetchone()
        if row:
            # Parse tokens from JSON if it's stored as JSON
            if isinstance(row['tokens'], str):
                row['tokens'] = json.loads(row['tokens'])
            return row
    
    return None


def link_pages(cur, source_url, destination_url):
    """Store a link relationship between two pages.
    
    Args:
        cur: Database cursor
        source_url: Source page URL
        destination_url: Destination page URL
    """
    cur.execute("""
        INSERT INTO page_links (source_url, destination_url)
        VALUES (%s, %s)
        ON CONFLICT (source_url, destination_url) DO NOTHING
    """, (source_url, destination_url))


def fetch_chunk_id_without_embedding(cur):
    """Fetch chunk IDs that don't have embeddings yet.
    
    Args:
        cur: Database cursor
        
    Returns:
        list: List of chunk IDs (UUIDs as strings)
    """
    cur.execute("""
        SELECT c.id 
        FROM chunk_items c
        LEFT JOIN embedding_items e ON c.id = e.token_id
        WHERE e.token_id IS NULL
        ORDER BY c.created_at
    """)
    
    return [str(row['id']) for row in cur.fetchall()]


def create_postgresql_url(dbname, table, item_id, params=None):
    """Create a PostgreSQL URL for internal use.
    
    Args:
        dbname: Database name
        table: Table name
        item_id: Item ID
        params: Optional query parameters dict
        
    Returns:
        str: PostgreSQL URL
    """
    url = f"postgresql://localhost/{dbname}/{table}/{item_id}"
    
    if params:
        query_string = urlencode(params)
        url += f"?{query_string}"
    
    return url


def initialize_database():
    """Initialize the database with required tables.
    
    This function should be called once to set up the database schema.
    """
    storage_mode = get_storage_mode()
    
    if storage_mode in ['database', 'both']:
        if not PSYCOPG_AVAILABLE:
            print("❌ Database storage requested but psycopg not available")
            if storage_mode == 'database':
                print("💡 Hint: Install psycopg with 'uv pip install psycopg psycopg-binary' or use STORAGE_MODE=disk")
                return
        else:
            try:
                connection = connect_db()
                if connection:
                    try:
                        create_tables(connection)
                        print("✅ Database initialized successfully")
                    finally:
                        connection.close()
                else:
                    print("❌ Failed to connect to database")
            except Exception as e:
                print(f"❌ Database initialization failed: {e}")
                if storage_mode == 'database':
                    raise
    
    if storage_mode in ['disk', 'both']:
        try:
            ensure_storage_directories()
            storage_dir = get_storage_directory()
            print(f"✅ Disk storage directories initialized at: {storage_dir}")
        except Exception as e:
            print(f"❌ Disk storage initialization failed: {e}")
            raise
    
    print(f"Storage mode: {storage_mode}")


if __name__ == "__main__":
    # Allow running this module directly to initialize the database
    initialize_database() 