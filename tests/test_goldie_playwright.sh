#!/bin/bash

echo "🕷️  Testing Goldie Playwright Spider - Single Page Test"
echo "=================================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Set up environment variables
echo "⚙️  Setting up environment..."
export STORAGE_MODE=disk
export STORAGE_DIRECTORY=./test_storage

# Create test storage directory
mkdir -p ./test_storage/html
mkdir -p ./test_storage/metadata

# Initialize storage if needed
echo "🗄️  Initializing storage..."
python scripts/init_db.py 2>/dev/null || echo "   (Storage initialization skipped)"

echo ""
echo "🚀 Running single page test with Playwright..."
echo "📄 Target: https://inspection.canada.ca/en"
echo "💾 Storage: ./test_storage"
echo ""

# Run the test
python test_simple_playwright.py

echo ""
echo "📊 Test Results:"
echo "=================="

# Check if files were created
if [ -d "./test_storage" ]; then
    html_count=$(find ./test_storage/html -name "*.html" 2>/dev/null | wc -l)
    json_count=$(find ./test_storage/metadata -name "*.json" 2>/dev/null | wc -l)
    
    echo "📁 HTML files: $html_count"
    echo "📋 Metadata files: $json_count"
    
    if [ "$html_count" -gt 0 ]; then
        echo "✅ Test successful - content was scraped and stored!"
        echo ""
        echo "🔍 To inspect results:"
        echo "   ls -la ./test_storage/html/"
        echo "   ls -la ./test_storage/metadata/"
    else
        echo "⚠️  No files were created - check for errors above"
    fi
else
    echo "❌ Test storage directory not found"
fi

echo ""
echo "�� Test completed!"
