# Louis Crawler Documentation

This directory contains documentation for the Louis Crawler project.

## Available Documentation

### [crawler-files.md](./crawler-files.md)
Comprehensive documentation explaining the purpose and functionality of each file in the `louis/crawler` directory. This includes:

- **Core crawler files**: Items, settings, middlewares, pipelines, and utilities
- **Spider files**: Individual spider documentation (goldie, hawn, kurt)
- **Data flow**: How the three-stage pipeline processes web content into AI-ready embeddings

### [parallel_spider_guide.md](./parallel_spider_guide.md)
Complete guide for the `goldie_playwright_parallel` spider with parallel processing capabilities:

- **Parallel processing**: Multi-core URL processing with configurable workers
- **Advanced logging**: Shared logging with unique task IDs for debugging
- **Resume capability**: URL tracking and resumable crawls
- **Monitoring & analysis**: Real-time monitoring and log analysis tools

### [README_depth_control.md](./README_depth_control.md)  
Depth control and URL tracking features for goldie spiders:

- **Depth control**: Control crawl depth (0=start URLs only, 1=direct links, etc.)
- **URL tracking**: Persistent URL tracking and deduplication
- **Resume functionality**: Skip previously scraped URLs across runs

### [playwright_integration.md](./playwright_integration.md)
Playwright integration for handling JavaScript-rendered content:

- **Browser automation**: Handle dynamic content with JavaScript execution
- **Multiple spider types**: Full Playwright, smart detection, and hybrid approaches
- **Configuration options**: Browser settings, wait conditions, and performance optimization

## Quick Overview

The Louis Crawler is a Scrapy-based framework designed to:

1. **Crawl** Canadian government inspection websites (goldie spider)
2. **Chunk** HTML content into semantic text blocks (hawn spider)  
3. **Generate** AI embeddings for search and retrieval (kurt spider)

Each spider has a specific role in the pipeline, working together to transform web content into structured, searchable AI embeddings stored in a database.

## Getting Started

For detailed information about each component, start with [crawler-files.md](./crawler-files.md).
