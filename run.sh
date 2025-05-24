#!/bin/bash

source .venv/bin/activate
export $(xargs < .env)
scrapy crawl goldie_playwright_parallel -a max_depth=1 -a num_workers=2 -a batch_size=2

