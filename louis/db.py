"""Database module for Louis crawler.

This module provides database connectivity and operations for storing
crawled data, chunks, and embeddings using PostgreSQL.
It also supports storing HTML content and metadata to disk as files,
and to S3-compatible object storage using MinIO.
"""
import os
import json
import uuid
import io
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

# Make MinIO import optional for non-S3 storage
try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    print("Warning: minio not available. S3 storage disabled.")


def get_storage_mode():
    """Get the storage mode from environment variables.
    
    Returns:
        str: 'database', 'disk', or 's3'
    """
    mode = os.getenv('STORAGE_MODE', 'database').lower()
    
    # Validate and fallback for unavailable dependencies
    if mode == 'database' and not PSYCOPG_AVAILABLE:
        print("Warning: psycopg not available, falling back to disk storage")
        return 'disk'
    
    if mode == 's3' and not MINIO_AVAILABLE:
        print("Warning: minio not available, falling back to disk storage")
        return 'disk'
    
    # Only allow simple storage modes
    if mode not in ['database', 'disk', 's3']:
        print(f"Warning: invalid storage mode '{mode}', falling back to disk")
        return 'disk'
    
    return mode


def get_storage_directory():
    """Get the directory for disk storage.
    
    Returns:
        Path: Path object for the storage directory
    """
    storage_dir = os.getenv('STORAGE_DIRECTORY', 'storage')
    return Path(storage_dir)


def get_s3_config():
    """Get S3 configuration from environment variables.
    
    Returns:
        dict: S3 configuration with endpoint, access_key, secret_key, bucket_name, secure
    """
    return {
        'endpoint': os.getenv('S3_ENDPOINT', 'localhost:9000'),
        'access_key': os.getenv('S3_ACCESS_KEY', 'minioadmin'),
        'secret_key': os.getenv('S3_SECRET_KEY', 'minioadmin'),
        'bucket_name': os.getenv('S3_BUCKET_NAME', 'louis-crawler'),
        'secure': os.getenv('S3_SECURE', 'false').lower() == 'true'
    }


def get_s3_client():
    """Create and return a MinIO client.
    
    Returns:
        Minio: MinIO client instance or None if not available
    """
    if not MINIO_AVAILABLE:
        print("Warning: Cannot create S3 client - minio not available")
        return None
    
    config = get_s3_config()
    
    try:
        client = Minio(
            config['endpoint'],
            access_key=config['access_key'],
            secret_key=config['secret_key'],
            secure=config['secure']
        )
        
        # Ensure bucket exists
        bucket_name = config['bucket_name']
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Created S3 bucket: {bucket_name}")
        
        return client
    except Exception as e:
        print(f"Warning: Failed to create S3 client: {e}")
        return None


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


def store_to_s3(item):
    """Store a CrawlItem to S3 as HTML and JSON files.
    
    Args:
        item: CrawlItem object with fields: url, title, lang, html_content, 
              last_crawled, last_updated
              
    Returns:
        dict: The stored item with generated id and S3 object names
    """
    client = get_s3_client()
    if not client:
        raise Exception("S3 client not available")
    
    config = get_s3_config()
    bucket_name = config['bucket_name']
    
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
        'html_object': f"html/{file_uuid}.html",
        'metadata_object': f"metadata/{file_uuid}.json",
        'bucket_name': bucket_name
    }
    
    # Store HTML content to S3
    html_content = item.get('html_content', '')
    html_data = io.BytesIO(html_content.encode('utf-8'))
    client.put_object(
        bucket_name,
        f"html/{file_uuid}.html",
        html_data,
        length=len(html_content.encode('utf-8')),
        content_type='text/html'
    )
    
    # Store metadata JSON to S3
    metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
    metadata_data = io.BytesIO(metadata_json.encode('utf-8'))
    client.put_object(
        bucket_name,
        f"metadata/{file_uuid}.json",
        metadata_data,
        length=len(metadata_json.encode('utf-8')),
        content_type='application/json'
    )
    
    return metadata


def load_from_s3(file_uuid):
    """Load a CrawlItem from S3 using its UUID.
    
    Args:
        file_uuid: UUID string for the objects
        
    Returns:
        dict: The item data with html_content loaded, or None if not found
    """
    client = get_s3_client()
    if not client:
        print("Warning: S3 client not available")
        return None
    
    config = get_s3_config()
    bucket_name = config['bucket_name']
    
    try:
        # Load metadata from S3
        metadata_obj = client.get_object(bucket_name, f"metadata/{file_uuid}.json")
        metadata_content = metadata_obj.read().decode('utf-8')
        metadata = json.loads(metadata_content)
        
        # Load HTML content from S3
        html_obj = client.get_object(bucket_name, f"html/{file_uuid}.html")
        html_content = html_obj.read().decode('utf-8')
        
        # Combine metadata and HTML content
        result = metadata.copy()
        result['html_content'] = html_content
        
        return result
        
    except S3Error as e:
        if e.code == 'NoSuchKey':
            return None
        else:
            print(f"S3 error loading {file_uuid}: {e}")
            return None
    except Exception as e:
        print(f"Error loading from S3: {e}")
        return None


def list_s3_items():
    """List all stored items in S3.
    
    Returns:
        list: List of metadata dictionaries for all stored items
    """
    client = get_s3_client()
    if not client:
        print("Warning: S3 client not available")
        return []
    
    config = get_s3_config()
    bucket_name = config['bucket_name']
    
    items = []
    try:
        # List all metadata objects (which contain the full metadata)
        for obj in client.list_objects(bucket_name, prefix='metadata/', recursive=True):
            if obj.object_name.endswith('.json'):
                try:
                    # Load metadata
                    metadata_obj = client.get_object(bucket_name, obj.object_name)
                    metadata_content = metadata_obj.read().decode('utf-8')
                    metadata = json.loads(metadata_content)
                    items.append(metadata)
                except (json.JSONDecodeError, S3Error) as e:
                    # Skip corrupted or inaccessible objects
                    print(f"Warning: Failed to load metadata from {obj.object_name}: {e}")
                    continue
                    
    except S3Error as e:
        print(f"Error listing S3 objects: {e}")
        return []
    
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
        cur: Database cursor (may be None for non-database modes)
        item: CrawlItem object with fields: url, title, lang, html_content, 
              last_crawled, last_updated
              
    Returns:
        dict: The stored item with generated id
    """
    storage_mode = get_storage_mode()
    
    if storage_mode == 'database':
        if cur is not None:
            return store_crawl_item_to_database(cur, item)
        else:
            print("Warning: Database cursor is None but database storage is requested")
            # Fallback to disk
            return store_to_disk(item)
    
    elif storage_mode == 'disk':
        return store_to_disk(item)
    
    elif storage_mode == 's3':
        try:
            return store_to_s3(item)
        except Exception as e:
            print(f"Warning: Failed to store to S3: {e}")
            # Fallback to disk
            return store_to_disk(item)
    
    else:
        # This shouldn't happen due to validation in get_storage_mode()
        print(f"Warning: Unknown storage mode '{storage_mode}', falling back to disk")
        return store_to_disk(item)


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
    """Initialize the storage system based on the configured mode.
    
    This function should be called once to set up the storage system.
    """
    storage_mode = get_storage_mode()
    
    if storage_mode == 'database':
        if not PSYCOPG_AVAILABLE:
            print("❌ Database storage requested but psycopg not available")
            print("💡 Hint: Install psycopg with 'uv pip install psycopg psycopg-binary' or use STORAGE_MODE=disk or STORAGE_MODE=s3")
            return
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
                raise Exception("Database connection failed")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            raise
    
    elif storage_mode == 'disk':
        try:
            ensure_storage_directories()
            storage_dir = get_storage_directory()
            print(f"✅ Disk storage directories initialized at: {storage_dir}")
        except Exception as e:
            print(f"❌ Disk storage initialization failed: {e}")
            raise
    
    elif storage_mode == 's3':
        if not MINIO_AVAILABLE:
            print("❌ S3 storage requested but minio not available")
            print("💡 Hint: Install minio with 'uv pip install minio' or use STORAGE_MODE=disk or STORAGE_MODE=database")
            return
        try:
            client = get_s3_client()
            if client:
                config = get_s3_config()
                print(f"✅ S3 storage initialized successfully (bucket: {config['bucket_name']})")
            else:
                print("❌ Failed to initialize S3 client")
                raise Exception("S3 client initialization failed")
        except Exception as e:
            print(f"❌ S3 storage initialization failed: {e}")
            raise
    
    else:
        print(f"❌ Unknown storage mode: {storage_mode}")
        raise Exception(f"Invalid storage mode: {storage_mode}")
    
    print(f"Storage mode: {storage_mode}")


if __name__ == "__main__":
    # Allow running this module directly to initialize the database
    initialize_database() 