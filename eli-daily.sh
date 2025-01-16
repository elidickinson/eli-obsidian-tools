#!/bin/bash
set -e
uv run dailymonthly.py ~/Obsidian/Notes/Daily\ Notes --delete --append --days-to-keep 4 --skip-duplicate-todos
