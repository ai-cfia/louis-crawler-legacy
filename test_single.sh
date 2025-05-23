source .venv/bin/activate
# 1. Set up environment
export STORAGE_MODE=disk
export STORAGE_DIRECTORY=./test_storage

# 2. Initialize storage
python scripts/init_db.py

# 3. Run single page test
scrapy crawl test_goldie

# 4. View results
python scripts/storage_manager.py list
python scripts/storage_manager.py stats