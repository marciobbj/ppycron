"""
Tests for the PPyCron CLI module.

Tests cover all CLI commands using click.testing.CliRunner with mocked
platform interfaces so no real crontab/schtasks operations are performed.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from ppycron.cli import cli, _format_cron, _format_cron_list, _get_interface
from ppycron.src.base import Cron


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    """Click CliRunner for invoking commands."""
    return CliRunner()


@pytest.fixture
def mock_interface():
    """A fully mocked interface with default return values."""
    interface = MagicMock()
    interface.get_all.return_value = []
    interface.count.return_value = 0
    interface.is_valid_cron_format.return_value = True
    return interface


@pytest.fixture
def sample_cron():
    """A sample Cron object for testing."""
    return Cron(command="echo hello", interval="*/5 * * * *", id="test-id-123")


@pytest.fixture
def sample_crons():
    """Multiple sample Cron objects."""
    return [
        Cron(command="echo hello", interval="*/5 * * * *", id="id-1"),
        Cron(command="backup.sh", interval="0 2 * * *", id="id-2"),
        Cron(command="python script.py", interval="0 9 * * 1-5", id="id-3"),
    ]


# ---------------------------------------------------------------------------
# Helper formatting tests
# ---------------------------------------------------------------------------

class TestFormatCron:
    """Tests for _format_cron helper."""

    def test_format_table(self, sample_cron):
        result = _format_cron(sample_cron, "table")
        assert "test-id-123" in result
        assert "echo hello" in result
        assert "*/5 * * * *" in result

    def test_format_json(self, sample_cron):
        result = _format_cron(sample_cron, "json")
        data = json.loads(result)
        assert data["id"] == "test-id-123"
        assert data["command"] == "echo hello"
        assert data["interval"] == "*/5 * * * *"


class TestFormatCronList:
    """Tests for _format_cron_list helper."""

    def test_empty_list(self):
        result = _format_cron_list([], "table")
        assert "No cronjobs found" in result

    def test_table_format(self, sample_crons):
        result = _format_cron_list(sample_crons, "table")
        assert "id-1" in result
        assert "id-2" in result
        assert "id-3" in result
        assert "echo hello" in result
        assert "backup.sh" in result

    def test_json_format(self, sample_crons):
        result = _format_cron_list(sample_crons, "json")
        data = json.loads(result)
        assert len(data) == 3
        assert data[0]["id"] == "id-1"
        assert data[2]["command"] == "python script.py"


# ---------------------------------------------------------------------------
# CLI: ppycron (root group)
# ---------------------------------------------------------------------------

class TestCLIRoot:
    """Tests for the root CLI group."""

    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "PPyCron" in result.output
        assert "Cross-platform" in result.output

    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.1.0" in result.output

    def test_verbose_flag(self, runner, mock_interface):
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["-v", "count"])
            assert result.exit_code == 0


# ---------------------------------------------------------------------------
# CLI: ppycron add
# ---------------------------------------------------------------------------

class TestCLIAdd:
    """Tests for the 'add' command."""

    def test_add_success_table(self, runner, mock_interface, sample_cron):
        mock_interface.add.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["add", "-c", "echo hello", "-i", "*/5 * * * *"])
        assert result.exit_code == 0
        assert "Cronjob created successfully" in result.output
        assert "test-id-123" in result.output
        mock_interface.add.assert_called_once_with(command="echo hello", interval="*/5 * * * *")

    def test_add_success_json(self, runner, mock_interface, sample_cron):
        mock_interface.add.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["add", "-c", "echo hello", "-i", "*/5 * * * *", "-f", "json"])
        assert result.exit_code == 0
        # Check that it contains valid JSON
        lines = result.output.split("\n")
        # Find the JSON block (after the success message)
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith("{"):
                json_start = i
                break
        assert json_start is not None

    def test_add_validation_error(self, runner, mock_interface):
        mock_interface.add.side_effect = ValueError("Invalid command provided")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["add", "-c", "", "-i", "* * * * *"])
        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_add_runtime_error(self, runner, mock_interface):
        mock_interface.add.side_effect = RuntimeError("Failed to add cron job")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["add", "-c", "echo test", "-i", "* * * * *"])
        assert result.exit_code == 1
        assert "Runtime error" in result.output

    def test_add_missing_command(self, runner):
        result = runner.invoke(cli, ["add", "-i", "* * * * *"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_add_missing_interval(self, runner):
        result = runner.invoke(cli, ["add", "-c", "echo hello"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()


# ---------------------------------------------------------------------------
# CLI: ppycron list
# ---------------------------------------------------------------------------

class TestCLIList:
    """Tests for the 'list' command."""

    def test_list_empty(self, runner, mock_interface):
        mock_interface.get_all.return_value = []
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "No cronjobs found" in result.output

    def test_list_with_jobs(self, runner, mock_interface, sample_crons):
        mock_interface.get_all.return_value = sample_crons
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Found 3 cronjob(s)" in result.output
        assert "id-1" in result.output
        assert "id-2" in result.output
        assert "id-3" in result.output

    def test_list_json_format(self, runner, mock_interface, sample_crons):
        mock_interface.get_all.return_value = sample_crons
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["list", "-f", "json"])
        assert result.exit_code == 0
        # Output includes the header line + JSON
        assert "id-1" in result.output

    def test_list_runtime_error(self, runner, mock_interface):
        mock_interface.get_all.side_effect = RuntimeError("Failed")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI: ppycron get
# ---------------------------------------------------------------------------

class TestCLIGet:
    """Tests for the 'get' command."""

    def test_get_success(self, runner, mock_interface, sample_cron):
        mock_interface.get_by_id.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["get", "-i", "test-id-123"])
        assert result.exit_code == 0
        assert "test-id-123" in result.output
        assert "echo hello" in result.output

    def test_get_not_found(self, runner, mock_interface):
        mock_interface.get_by_id.return_value = None
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["get", "-i", "non-existent"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_get_json_format(self, runner, mock_interface, sample_cron):
        mock_interface.get_by_id.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["get", "-i", "test-id-123", "-f", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output.strip())
        assert data["id"] == "test-id-123"

    def test_get_validation_error(self, runner, mock_interface):
        mock_interface.get_by_id.side_effect = ValueError("Cron ID is required")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["get", "-i", ""])
        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_get_missing_id(self, runner):
        result = runner.invoke(cli, ["get"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI: ppycron edit
# ---------------------------------------------------------------------------

class TestCLIEdit:
    """Tests for the 'edit' command."""

    def test_edit_command_success(self, runner, mock_interface, sample_cron):
        mock_interface.edit.return_value = True
        mock_interface.get_by_id.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["edit", "-i", "test-id-123", "-c", "echo updated"])
        assert result.exit_code == 0
        assert "updated successfully" in result.output
        mock_interface.edit.assert_called_once_with(cron_id="test-id-123", command="echo updated")

    def test_edit_interval_success(self, runner, mock_interface, sample_cron):
        mock_interface.edit.return_value = True
        mock_interface.get_by_id.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["edit", "-i", "test-id-123", "-I", "0 3 * * *"])
        assert result.exit_code == 0
        assert "updated successfully" in result.output
        mock_interface.edit.assert_called_once_with(cron_id="test-id-123", interval="0 3 * * *")

    def test_edit_both_success(self, runner, mock_interface, sample_cron):
        mock_interface.edit.return_value = True
        mock_interface.get_by_id.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["edit", "-i", "test-id-123", "-c", "new cmd", "-I", "0 3 * * *"])
        assert result.exit_code == 0
        mock_interface.edit.assert_called_once_with(cron_id="test-id-123", command="new cmd", interval="0 3 * * *")

    def test_edit_not_found(self, runner, mock_interface):
        mock_interface.edit.return_value = False
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["edit", "-i", "non-existent", "-c", "echo test"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_edit_no_option(self, runner, mock_interface):
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["edit", "-i", "test-id-123"])
        assert result.exit_code == 1
        assert "At least one" in result.output

    def test_edit_validation_error(self, runner, mock_interface):
        mock_interface.edit.side_effect = ValueError("Invalid command")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["edit", "-i", "test-id-123", "-c", ""])
        assert result.exit_code == 1

    def test_edit_json_format(self, runner, mock_interface, sample_cron):
        mock_interface.edit.return_value = True
        mock_interface.get_by_id.return_value = sample_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["edit", "-i", "test-id-123", "-c", "echo updated", "-f", "json"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# CLI: ppycron delete
# ---------------------------------------------------------------------------

class TestCLIDelete:
    """Tests for the 'delete' command."""

    def test_delete_success_with_yes(self, runner, mock_interface):
        mock_interface.delete.return_value = True
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["delete", "-i", "test-id-123", "-y"])
        assert result.exit_code == 0
        assert "deleted successfully" in result.output
        mock_interface.delete.assert_called_once_with(cron_id="test-id-123")

    def test_delete_with_confirmation(self, runner, mock_interface):
        mock_interface.delete.return_value = True
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["delete", "-i", "test-id-123"], input="y\n")
        assert result.exit_code == 0
        assert "deleted successfully" in result.output

    def test_delete_abort(self, runner, mock_interface):
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["delete", "-i", "test-id-123"], input="n\n")
        assert result.exit_code != 0
        mock_interface.delete.assert_not_called()

    def test_delete_not_found(self, runner, mock_interface):
        mock_interface.delete.return_value = False
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["delete", "-i", "non-existent", "-y"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_delete_validation_error(self, runner, mock_interface):
        mock_interface.delete.side_effect = ValueError("Cron ID is required")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["delete", "-i", "", "-y"])
        assert result.exit_code == 1

    def test_delete_missing_id(self, runner):
        result = runner.invoke(cli, ["delete", "-y"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI: ppycron clear
# ---------------------------------------------------------------------------

class TestCLIClear:
    """Tests for the 'clear' command."""

    def test_clear_success_with_yes(self, runner, mock_interface):
        mock_interface.clear_all.return_value = True
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["clear", "-y"])
        assert result.exit_code == 0
        assert "cleared successfully" in result.output

    def test_clear_with_confirmation(self, runner, mock_interface):
        mock_interface.clear_all.return_value = True
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["clear"], input="y\n")
        assert result.exit_code == 0
        assert "cleared successfully" in result.output

    def test_clear_abort(self, runner, mock_interface):
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["clear"], input="n\n")
        assert result.exit_code != 0
        mock_interface.clear_all.assert_not_called()

    def test_clear_failure(self, runner, mock_interface):
        mock_interface.clear_all.return_value = False
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["clear", "-y"])
        assert result.exit_code == 1
        assert "Failed to clear" in result.output

    def test_clear_runtime_error(self, runner, mock_interface):
        mock_interface.clear_all.side_effect = RuntimeError("Permission denied")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["clear", "-y"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI: ppycron validate
# ---------------------------------------------------------------------------

class TestCLIValidate:
    """Tests for the 'validate' command."""

    def test_validate_valid_format(self, runner, mock_interface):
        mock_interface.is_valid_cron_format.return_value = True
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["validate", "-i", "*/5 * * * *"])
        assert result.exit_code == 0
        assert "valid cron format" in result.output

    def test_validate_invalid_format(self, runner, mock_interface):
        mock_interface.is_valid_cron_format.return_value = False
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["validate", "-i", "60 * * * *"])
        assert result.exit_code == 1
        assert "NOT a valid" in result.output

    def test_validate_missing_interval(self, runner):
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI: ppycron count
# ---------------------------------------------------------------------------

class TestCLICount:
    """Tests for the 'count' command."""

    def test_count_zero(self, runner, mock_interface):
        mock_interface.count.return_value = 0
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["count"])
        assert result.exit_code == 0
        assert "Total cronjobs: 0" in result.output

    def test_count_multiple(self, runner, mock_interface):
        mock_interface.count.return_value = 42
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["count"])
        assert result.exit_code == 0
        assert "Total cronjobs: 42" in result.output

    def test_count_runtime_error(self, runner, mock_interface):
        mock_interface.count.side_effect = RuntimeError("Failed")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["count"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI: ppycron search
# ---------------------------------------------------------------------------

class TestCLISearch:
    """Tests for the 'search' command."""

    def test_search_by_command(self, runner, mock_interface, sample_crons):
        mock_interface.get_by_command.return_value = [sample_crons[0]]
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["search", "-c", "echo hello"])
        assert result.exit_code == 0
        assert "Found 1 matching" in result.output
        assert "id-1" in result.output

    def test_search_by_interval(self, runner, mock_interface, sample_crons):
        mock_interface.get_by_interval.return_value = [sample_crons[1]]
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["search", "-i", "0 2 * * *"])
        assert result.exit_code == 0
        assert "Found 1 matching" in result.output
        assert "id-2" in result.output

    def test_search_no_results(self, runner, mock_interface):
        mock_interface.get_by_command.return_value = []
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["search", "-c", "nonexistent"])
        assert result.exit_code == 0
        assert "No cronjobs found" in result.output

    def test_search_no_option(self, runner, mock_interface):
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["search"])
        assert result.exit_code == 1
        assert "At least one" in result.output

    def test_search_json_format(self, runner, mock_interface, sample_crons):
        mock_interface.get_by_command.return_value = sample_crons[:2]
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["search", "-c", "echo", "-f", "json"])
        assert result.exit_code == 0

    def test_search_both_deduplicates(self, runner, mock_interface, sample_crons):
        """Searching by both command and interval should deduplicate results."""
        mock_interface.get_by_command.return_value = [sample_crons[0]]
        mock_interface.get_by_interval.return_value = [sample_crons[0]]  # same cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["search", "-c", "echo hello", "-i", "*/5 * * * *"])
        assert result.exit_code == 0
        assert "Found 1 matching" in result.output


# ---------------------------------------------------------------------------
# CLI: ppycron duplicate
# ---------------------------------------------------------------------------

class TestCLIDuplicate:
    """Tests for the 'duplicate' command."""

    def test_duplicate_success(self, runner, mock_interface):
        new_cron = Cron(command="echo hello", interval="*/5 * * * *", id="new-id")
        mock_interface.duplicate.return_value = new_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["duplicate", "-i", "test-id-123"])
        assert result.exit_code == 0
        assert "duplicated successfully" in result.output
        assert "new-id" in result.output
        mock_interface.duplicate.assert_called_once_with("test-id-123", new_interval=None)

    def test_duplicate_with_new_interval(self, runner, mock_interface):
        new_cron = Cron(command="echo hello", interval="0 4 * * *", id="new-id")
        mock_interface.duplicate.return_value = new_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["duplicate", "-i", "test-id-123", "-I", "0 4 * * *"])
        assert result.exit_code == 0
        assert "duplicated successfully" in result.output
        mock_interface.duplicate.assert_called_once_with("test-id-123", new_interval="0 4 * * *")

    def test_duplicate_not_found(self, runner, mock_interface):
        mock_interface.duplicate.return_value = None
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["duplicate", "-i", "non-existent"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_duplicate_json_format(self, runner, mock_interface):
        new_cron = Cron(command="echo hello", interval="*/5 * * * *", id="new-id")
        mock_interface.duplicate.return_value = new_cron
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["duplicate", "-i", "test-id-123", "-f", "json"])
        assert result.exit_code == 0
        assert "new-id" in result.output

    def test_duplicate_validation_error(self, runner, mock_interface):
        mock_interface.duplicate.side_effect = ValueError("Invalid interval")
        with patch("ppycron.cli._get_interface", return_value=mock_interface):
            result = runner.invoke(cli, ["duplicate", "-i", "test-id-123", "-I", "invalid"])
        assert result.exit_code == 1

    def test_duplicate_missing_id(self, runner):
        result = runner.invoke(cli, ["duplicate"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

class TestPlatformDetection:
    """Tests for _get_interface platform detection."""

    def test_get_interface_unix(self):
        with patch("ppycron.cli.platform.system", return_value="Linux"):
            with patch("ppycron.src.unix.subprocess.run"):
                interface = _get_interface()
        from ppycron.src.unix import UnixInterface
        assert isinstance(interface, UnixInterface)

    def test_get_interface_darwin(self):
        with patch("ppycron.cli.platform.system", return_value="Darwin"):
            with patch("ppycron.src.unix.subprocess.run"):
                interface = _get_interface()
        from ppycron.src.unix import UnixInterface
        assert isinstance(interface, UnixInterface)

    def test_get_interface_windows(self):
        with patch("ppycron.cli.platform.system", return_value="Windows"):
            with patch("ppycron.src.windows.subprocess.run"):
                interface = _get_interface()
        from ppycron.src.windows import WindowsInterface
        assert isinstance(interface, WindowsInterface)
