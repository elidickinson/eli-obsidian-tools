#
# dailymonthly.py - Combine Obsidian daily notes into monthly summaries
#
# This script processes Obsidian daily notes (YYYY-MM-DD.md format) and combines them
# into monthly summary files (YYYY-MM.md). It preserves all content, adding headers
# for each day. By default, it:
#   - Processes all past months through the end of last month
#   - Skips empty/blank daily notes
#   - Preserves existing monthly files (won't overwrite)
#   - Maintains original daily notes (use --delete/-rm to remove)
#
# Empty notes can be included with --keep-empty. Process specific months with --month.
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.0.0",
# ]
# ///

import click
from pathlib import Path
from datetime import datetime, date
import shutil
from typing import Optional
import re

def get_daily_notes(notes_dir: Path, target_month: Optional[str] = None) -> dict[str, list[Path]]:
    """
    Get all daily notes organized by month (YYYY-MM).
    If target_month is specified, only return notes for that month.
    """
    daily_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.md$')

    notes = {}
    for file in notes_dir.glob('*.md'):
        if not daily_pattern.match(file.name):
            continue

        month = file.stem[:7]  # YYYY-MM
        if target_month and month != target_month:
            continue

        if month not in notes:
            notes[month] = []
        notes[month].append(file)

    return {k: sorted(v) for k, v in notes.items()}

def merge_month_notes(daily_notes: list[Path], output_file: Path, keep_empty: bool = False, append: bool = False) -> None:
    """Merge daily notes into a single monthly note with date headers."""
    if output_file.exists() and not append:
        raise FileExistsError(f"Monthly note {output_file} already exists")

    mode = 'a' if append else 'w'
    with output_file.open(mode, encoding='utf-8') as out:
        for note in daily_notes:
            content = note.read_text(encoding='utf-8').strip()
            if not keep_empty and not content:
                continue

            date_str = note.stem
            # Remove any existing date headers to avoid duplication
            content = re.sub(r'^#\s*' + date_str + r'\s*\n', '', content, flags=re.MULTILINE)

            out.write(f"# {date_str}\n\n")
            out.write(content + "\n\n")

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('notes_dir', type=click.Path(exists=True, path_type=Path))
@click.option('--month', help='Specific month to process (YYYY-MM format)')
@click.option('--delete', '-rm', is_flag=True, default=False,
              help='Delete daily notes after successful merge')
@click.option('--keep-empty/--no-keep-empty', default=False,
              help='Keep empty or whitespace-only notes in output (default: false)')
@click.option('--append', is_flag=True, default=False,
              help='Append to existing monthly notes if they exist')
def main(notes_dir: Path, month: Optional[str], delete: bool, keep_empty: bool, append: bool) -> None:
    """
    Merge Obsidian Daily Notes into monthly summary files.

    This script combines individual daily notes from your Obsidian vault into monthly
    summary files. It processes markdown files in the YYYY-MM-DD.md format and combines
    them into YYYY-MM.md files, preserving all content and adding date headers.

    \b
    Default behavior (no --month specified):
    - Processes ALL months that have daily notes, up through the end of last month
    - Example: If run in March 2024, processes every month from the earliest
      available through February 2024

    Notes are combined chronologically with headers for each day. If a monthly
    summary file already exists (e.g., 2024-01.md), that month is skipped with
    a warning to prevent accidental overwrites.

    If you store notes in iCloud Drive, you can find them in
     "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"

    \b
    Examples:
      Process all months through last month:
        $ python dailymonthly.py /path/to/Daily/Notes
        (or if you have uv you can let it handle dependcies automatically)
        $ uv run dailymonthly.py /path/to/Daily/Notes

      Process a specific month:
        $ python dailymonthly.py /path/to/Daily/Notes --month 2024-01

      Process and remove original daily notes:
        $ python dailymonthly.py /path/to/Daily/Notes -rm
    """
    if month:
        try:
            datetime.strptime(month, '%Y-%m')
            notes_by_month = get_daily_notes(notes_dir, month)
        except ValueError:
            raise click.BadParameter('Month must be in YYYY-MM format')
    else:
        # Process all months up through last month
        today = date.today()
        cutoff_month = f"{today.year}-{today.month-1:02d}" if today.month > 1 else f"{today.year-1}-12"
        notes_by_month = get_daily_notes(notes_dir)

        # Filter out future months and current month
        notes_by_month = {k: v for k, v in notes_by_month.items() if k <= cutoff_month}

    for month, daily_notes in notes_by_month.items():
        if not daily_notes:
            click.echo(f"No daily notes found for {month}")
            continue

        output_file = notes_dir / f"{month}.md"
        try:
            merge_month_notes(daily_notes, output_file, keep_empty, append)
            click.echo(f"Successfully merged {len(daily_notes)} notes for {month}")

            if delete:
                for note in daily_notes:
                    note.unlink()
                click.echo(f"Deleted {len(daily_notes)} daily notes for {month}")

        except FileExistsError as e:
            click.echo(f"Error: {e}", err=True)

if __name__ == '__main__':
    main()
