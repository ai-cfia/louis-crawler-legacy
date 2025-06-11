#!/bin/bash

source .venv/bin/activate
export $(xargs < .env)
scrapy crawl goldie_playwright_parallel -a max_depth=4 -a num_workers=16 -a batch_size=64

