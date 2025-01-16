# dailymonthly.py readme

A Python utility to merge Obsidian daily notes into monthly summaries. It can optionally delete the individual daily notes once they are merged.

## Installation

Requires Python ≥3.12 and the `click` library.

But if you use [uv](https://github.com/astral-sh/uv) it takes
care of that for you.

## Usage

Basic usage processes all past months through end of last month:
```bash
uv run dailymonthly.py /path/to/Daily/Notes
```

Process specific month:
```bash
uv run dailymonthly.py /path/to/Daily/Notes --month 2024-01
```

Options:
- `--month YYYY-MM`: Process specific month only (default is all months prior to the current one)
- `--delete` or `-rm`: Delete daily notes after successful merge
- `--keep-empty`: Include empty/blank daily notes (skipped by default)
- `--skip-duplicate-todos`: Skip duplicate To Dos in the monthly note. When used with `--keep-empty` set to false, it will also skip daily notes composed entirely of duplicate To Dos and whitespace.

## Behavior

- Processes markdown files named YYYY-MM-DD.md
- Creates monthly files named YYYY-MM.md
- Adds date headers (# YYYY-MM-DD) above each day's content
- Skips months where output file already exists
- Preserves all content including wiki links, tags, and formatting
