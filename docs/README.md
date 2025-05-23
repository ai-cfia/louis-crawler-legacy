# Louis Crawler Documentation

This directory contains documentation for the Louis Crawler project.

## Available Documentation

### [crawler-files.md](./crawler-files.md)
Comprehensive documentation explaining the purpose and functionality of each file in the `louis/crawler` directory. This includes:

- **Core crawler files**: Items, settings, middlewares, pipelines, and utilities
- **Spider files**: Individual spider documentation (goldie, hawn, kurt)
- **Data flow**: How the three-stage pipeline processes web content into AI-ready embeddings

## Quick Overview

The Louis Crawler is a Scrapy-based framework designed to:

1. **Crawl** Canadian government inspection websites (goldie spider)
2. **Chunk** HTML content into semantic text blocks (hawn spider)  
3. **Generate** AI embeddings for search and retrieval (kurt spider)

Each spider has a specific role in the pipeline, working together to transform web content into structured, searchable AI embeddings stored in a database.

## Getting Started

For detailed information about each component, start with [crawler-files.md](./crawler-files.md). 