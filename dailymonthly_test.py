# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.0.0",
#     "pytest>=8.0.0",
# ]
# ///

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from dailymonthly import get_daily_notes, merge_month_notes, main
from click.testing import CliRunner
from unittest.mock import patch
from datetime import date

def test_get_daily_notes():
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "2024-01-01.md").write_text("Day 1")
        (tmpdir_path / "2024-01-02.md").write_text("Day 2")
        (tmpdir_path / "2024-02-01.md").write_text("Next month")
        (tmpdir_path / "invalid.md").write_text("Not a daily note")

        # Test without month filter
        notes = get_daily_notes(tmpdir_path)
        assert set(notes.keys()) == {"2024-01", "2024-02"}
        assert len(notes["2024-01"]) == 2
        assert len(notes["2024-02"]) == 1

        # Test with month filter
        notes = get_daily_notes(tmpdir_path, "2024-01")
        assert set(notes.keys()) == {"2024-01"}
        assert len(notes["2024-01"]) == 2

def test_merge_month_notes():
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test daily notes
        (tmpdir_path / "2024-01-01.md").write_text("Day 1 content")
        (tmpdir_path / "2024-01-02.md").write_text("# 2024-01-02\nDay 2 content")

        daily_notes = sorted(tmpdir_path.glob("2024-01-*.md"))
        output_file = tmpdir_path / "2024-01.md"

        merge_month_notes(daily_notes, output_file, keep_empty=False)

        content = output_file.read_text()
        assert "# 2024-01-01" in content
        assert "Day 1 content" in content
        assert "# 2024-01-02" in content
        assert "Day 2 content" in content
        # Check that date header isn't duplicated
        assert content.count("# 2024-01-02") == 1

def test_merge_month_notes_existing_file():
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "2024-01-01.md").write_text("Day 1")
        output_file = tmpdir_path / "2024-01.md"
        output_file.write_text("Existing content")

        daily_notes = [tmpdir_path / "2024-01-01.md"]

        with pytest.raises(FileExistsError):
            merge_month_notes(daily_notes, output_file, keep_empty=False)

def test_days_to_keep():
    runner = CliRunner()
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files across multiple days
        (tmpdir_path / "2024-01-01.md").write_text("Day 1")
        (tmpdir_path / "2024-01-02.md").write_text("Day 2")
        (tmpdir_path / "2024-01-03.md").write_text("Day 3")
        (tmpdir_path / "2024-01-04.md").write_text("Day 4")
        (tmpdir_path / "2024-01-05.md").write_text("Day 5")
        (tmpdir_path / "2024-01-06.md").write_text("Day 6")
        (tmpdir_path / "2024-01-07.md").write_text("Day 7")
        (tmpdir_path / "2024-01-08.md").write_text("Day 8")

        # Mock current date to January 8, 2024
        with patch('dailymonthly.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 8)
            result = runner.invoke(main, [str(tmpdir_path), '--days-to-keep', '7'])
            assert result.exit_code == 0

        # Check that only the last 7 days are kept
        content = (tmpdir_path / "2024-01.md").read_text()
        assert "# 2024-01-02" not in content
        assert "# 2024-01-08" not in content
        assert "# 2024-01-01" in content
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test daily notes
        (tmpdir_path / "2024-01-01.md").write_text("Day 1 content")
        (tmpdir_path / "2024-01-02.md").write_text("# 2024-01-02\nDay 2 content")

        # Create an existing monthly note
        output_file = tmpdir_path / "2024-01.md"
        output_file.write_text("Existing content\n")

        daily_notes = sorted(tmpdir_path.glob("2024-01-*.md"))

        # Append to the existing monthly note
        merge_month_notes(daily_notes, output_file, keep_empty=False, append=True)

        content = output_file.read_text()
        assert "Existing content" in content
        assert "# 2024-01-01" in content
        assert "Day 1 content" in content
        assert "# 2024-01-02" in content
        assert "Day 2 content" in content
    runner = CliRunner()
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Test help text
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Merge Obsidian Daily Notes" in result.output
        assert "Default behavior" in result.output

        # Test invalid month format
        result = runner.invoke(main, [str(tmpdir_path), '--month', '2024'])
        assert result.exit_code == 2
        assert "Month must be in YYYY-MM format" in result.output

def test_cli_delete_options():
    runner = CliRunner()
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "2024-01-01.md").write_text("Day 1")
        (tmpdir_path / "2024-01-02.md").write_text("Day 2")

        # Test --delete
        result = runner.invoke(main, [str(tmpdir_path), '--month', '2024-01', '--delete'])
        assert result.exit_code == 0
        assert len(list(tmpdir_path.glob("2024-01-*.md"))) == 0

        # Clean up and test -rm alias
        (tmpdir_path / "2024-01.md").unlink()
        (tmpdir_path / "2024-01-01.md").write_text("Day 1")
        (tmpdir_path / "2024-01-02.md").write_text("Day 2")

        result = runner.invoke(main, [str(tmpdir_path), '--month', '2024-01', '-rm'])
        assert result.exit_code == 0
        assert len(list(tmpdir_path.glob("2024-01-*.md"))) == 0

def test_empty_note_handling():
    """Test handling of empty notes with keep-empty flag."""
    runner = CliRunner()
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        (tmpdir_path / "2024-01-01.md").write_text("Content")
        (tmpdir_path / "2024-01-02.md").write_text("")
        (tmpdir_path / "2024-01-03.md").write_text("  \n  ")  # Whitespace only

        # Test default behavior (skip empty)
        result = runner.invoke(main, [str(tmpdir_path), '--month', '2024-01'])
        assert result.exit_code == 0
        content = (tmpdir_path / "2024-01.md").read_text()
        assert "# 2024-01-01" in content
        assert "2024-01-02" not in content
        assert "2024-01-03" not in content

        # Clean up
        (tmpdir_path / "2024-01.md").unlink()

        # Test with keep-empty
        result = runner.invoke(main, [str(tmpdir_path), '--month', '2024-01', '--keep-empty'])
        assert result.exit_code == 0
        content = (tmpdir_path / "2024-01.md").read_text()
        assert "# 2024-01-01" in content
        assert "# 2024-01-02" in content
        assert "# 2024-01-03" in content

def test_cli_default_behavior():
    """Test that default behavior processes all months through last month."""
    runner = CliRunner()
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files across multiple months
        (tmpdir_path / "2023-01-01.md").write_text("Old note")
        (tmpdir_path / "2024-01-01.md").write_text("Recent note")
        (tmpdir_path / "2024-02-01.md").write_text("Last month")
        (tmpdir_path / "2024-03-01.md").write_text("Current month")

        # Mock current date to March 2024
        with patch('dailymonthly.date') as mock_date:
            mock_date.today.return_value = date(2024, 3, 1)
            result = runner.invoke(main, [str(tmpdir_path)])
            assert result.exit_code == 0

        # Should create notes for all months through last month
        assert (tmpdir_path / "2023-01.md").exists()
        assert (tmpdir_path / "2024-01.md").exists()
        assert (tmpdir_path / "2024-02.md").exists()
        # Should not create note for current month
        assert not (tmpdir_path / "2024-03.md").exists()

def test_no_duplicate_content():
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test daily notes
        (tmpdir_path / "2024-01-01.md").write_text("Day 1 content")
        (tmpdir_path / "2024-01-02.md").write_text("Day 2 content")

        daily_notes = sorted(tmpdir_path.glob("2024-01-*.md"))
        output_file = tmpdir_path / "2024-01.md"

        merge_month_notes(daily_notes, output_file, keep_empty=False)

        content = output_file.read_text()
        # Check that content is not duplicated
        assert content.count("Day 1 content") == 1
        assert content.count("Day 2 content") == 1

def test_skip_duplicate_todos():
    """Test that duplicate todos are skipped when --skip-duplicate-todos is used."""
    runner = CliRunner()
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test daily notes with duplicate todos
        (tmpdir_path / "2024-01-01.md").write_text("- [ ] Task 1\n- [ ] Task 2")
        (tmpdir_path / "2024-01-02.md").write_text("- [ ] Task 1\n- [ ] Task 3")

        # Run the CLI with --skip-duplicate-todos
        result = runner.invoke(main, [str(tmpdir_path), '--month', '2024-01', '--skip-duplicate-todos'])
        assert result.exit_code == 0

        content = (tmpdir_path / "2024-01.md").read_text()
        # Check that duplicate todos are skipped
        assert content.count("- [ ] Task 1") == 1
        assert content.count("- [ ] Task 2") == 1
        assert content.count("- [ ] Task 3") == 1
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test daily notes
        (tmpdir_path / "2024-01-01.md").write_text("Day 1 content")
        (tmpdir_path / "2024-01-02.md").write_text("- [ ] Task 1\nDay 2 content")

        daily_notes = sorted(tmpdir_path.glob("2024-01-*.md"))
        output_file = tmpdir_path / "2024-01.md"

        merge_month_notes(daily_notes, output_file, keep_empty=False)

        content = output_file.read_text()
        # Check that content is not duplicated
        assert content.count("Day 1 content") == 1
        assert content.count("Day 2 content") == 1
        assert content.count("- [ ] Task 1") == 1

pytest.main([__file__, "-v"])
