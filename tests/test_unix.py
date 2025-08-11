import os
import pytest
import logging
from unittest.mock import Mock, patch, call
from ppycron.src.base import Cron
from ppycron.src.unix import UnixInterface
import subprocess


@pytest.fixture(scope="function")
def config_file(tmp_path):
    # Usando um arquivo temporário para simular o conteúdo do crontab
    cronfile = tmp_path / "crontab_file"
    cronfile.write_text("# Sample cron jobs for testing\n")
    return cronfile


@pytest.fixture
def subprocess_run(mocker):
    yield mocker.patch("ppycron.src.unix.subprocess.run")


@pytest.fixture
def subprocess_check_output(mocker, config_file):
    # Inicialmente, usa o conteúdo do arquivo temporário como dado para check_output.
    data = config_file.read_text()
    return mocker.patch(
        "ppycron.src.unix.subprocess.check_output",
        return_value=data.encode("utf-8"),
    )


@pytest.fixture
def crontab(subprocess_run):
    from ppycron.src.unix import UnixInterface
    return UnixInterface()


class TestUnixInterfaceInitialization:
    """Test Unix interface initialization."""
    
    def test_init_success(self, mocker):
        """Test successful initialization."""
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        interface = UnixInterface()
        assert interface.operational_system == "linux"
        mock_run.assert_called()
    
    def test_init_crontab_not_found(self, mocker):
        """Test initialization when crontab command is not found."""
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.side_effect = FileNotFoundError("crontab: command not found")
        
        with pytest.raises(RuntimeError, match="crontab command not found"):
            UnixInterface()


class TestUnixInterfaceValidation:
    """Test validation methods."""
    
    def test_validate_interval_valid_formats(self):
        """Test valid cron interval formats."""
        interface = UnixInterface()
        
        valid_intervals = [
            "* * * * *",
            "*/15 * * * *",
            "0 12 * * *",
            "0 0 1 * *",
            "0 0 * * 0",
            "30 2 * * 1-5",
            "0 9,17 * * 1-5",
            "0 0 1,15 * *"
        ]
        
        for interval in valid_intervals:
            assert interface._validate_interval(interval), f"Failed to validate: {interval}"
    
    def test_validate_interval_invalid_formats(self):
        """Test invalid cron interval formats."""
        interface = UnixInterface()
        
        invalid_intervals = [
            "",  # Empty
            "invalid",  # Not enough fields
        ]
        
        for interval in invalid_intervals:
            assert not interface._validate_interval(interval), f"Should not validate: {interval}"
    
    def test_validate_command_valid(self):
        """Test valid command validation."""
        interface = UnixInterface()
        
        valid_commands = [
            "echo hello",
            "python script.py",
            "/usr/bin/command",
            "echo 'hello world'"
        ]
        
        for command in valid_commands:
            assert interface._validate_command(command), f"Failed to validate: {command}"
    
    def test_validate_command_invalid(self):
        """Test invalid command validation."""
        interface = UnixInterface()
        
        invalid_commands = [
            "",  # Empty
            "   ",  # Whitespace only
            None,  # None
        ]
        
        for command in invalid_commands:
            assert not interface._validate_command(command), f"Should not validate: {command}"


class TestUnixInterfaceAdd:
    """Test adding cron jobs."""
    
    @pytest.mark.parametrize(
        "cron_line,interval,command",
        [
            ('*/15 0 * * * echo "hello"', "*/15 0 * * *", 'echo "hello"'),
            ("1 * * * 1,2 echo this-is-a-test", "1 * * * 1,2", "echo this-is-a-test"),
            ("*/2 * * * * echo for-this-test", "*/2 * * * *", "echo for-this-test"),
            ("1 2 * * * echo we-will-need-tests", "1 2 * * *", "echo we-will-need-tests"),
            ("1 3-4 * * * echo soon-this-test", "1 3-4 * * *", "echo soon-this-test"),
            ("*/15 0 * * * sh /path/to/file.sh", "*/15 0 * * *", "sh /path/to/file.sh"),
        ],
    )
    def test_add_cron_success(
        self,
        crontab,
        mocker,
        config_file,
        cron_line,
        interval,
        command,
        subprocess_run,
        subprocess_check_output,
    ):
        """Test successful cron job addition."""
        # Mock the check_output to return empty string initially
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b""
        
        cron = crontab.add(command=command, interval=interval)

        assert isinstance(cron, Cron)
        assert cron.command == command
        assert cron.interval == interval
        # Verifica se o id foi gerado e é uma string não vazia
        assert cron.id and isinstance(cron.id, str)
        subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True, capture_output=True)
    
    def test_add_cron_invalid_command(self, crontab):
        """Test adding cron with invalid command."""
        with pytest.raises(ValueError, match="Invalid command provided"):
            crontab.add(command="", interval="* * * * *")
    
    def test_add_cron_invalid_interval(self, crontab):
        """Test adding cron with invalid interval."""
        with pytest.raises(ValueError, match="Invalid interval format"):
            crontab.add(command="echo test", interval="invalid")
    
    def test_add_cron_subprocess_error(self, crontab, mocker):
        """Test adding cron when subprocess fails."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b""
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "crontab")
        
        with pytest.raises(RuntimeError, match="Failed to add cron job"):
            crontab.add(command="echo test", interval="* * * * *")


class TestUnixInterfaceGetAll:
    """Test getting all cron jobs."""
    
    @pytest.mark.parametrize(
        "cron_line,interval,command",
        [
            ('*/15 0 * * * echo "hello"', "*/15 0 * * *", 'echo "hello"'),
            ("3 * * * 3,5 echo this-is-a-test", "3 * * * 3,5", "echo this-is-a-test"),
            ("*/6 * * * * echo for-this-test", "*/6 * * * *", "echo for-this-test"),
            ("9 3 * * * echo we-will-need-tests", "9 3 * * *", "echo we-will-need-tests"),
            ("10 2-4 * * * echo soon-this-test", "10 2-4 * * *", "echo soon-this-test"),
            ("*/15 0 * * * sh /path/to/file.sh", "*/15 0 * * *", "sh /path/to/file.sh"),
        ],
    )
    def test_get_cron_jobs_success(
        self, crontab, config_file, cron_line, interval, command, subprocess_check_output
    ):
        """Test successful retrieval of cron jobs."""
        # Ajusta o arquivo de configuração para conter uma linha com o identificador
        fake_cron_line = f"{cron_line} # id: test-cron-id"
        config_file.write_text(fake_cron_line + "\n")
        # Atualiza o valor de retorno do mock para refletir o conteúdo atualizado do arquivo
        subprocess_check_output.return_value = config_file.read_text().encode("utf-8")
        crons = crontab.get_all()
        # Verifica se pelo menos uma das entradas possui o id esperado
        assert any(c.id == "test-cron-id" for c in crons)
        subprocess_check_output.assert_called_with(["crontab", "-l"], stderr=subprocess.PIPE)
    
    def test_get_cron_jobs_empty(self, crontab, mocker):
        """Test getting cron jobs when crontab is empty."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "crontab")
        
        crons = crontab.get_all()
        assert crons == []
    
    def test_get_cron_jobs_malformed_lines(self, crontab, mocker):
        """Test handling of malformed cron lines."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"malformed line\n* * * * * echo test # id: test-id\n"
        
        crons = crontab.get_all()
        assert len(crons) == 1
        assert crons[0].id == "test-id"
    
    def test_get_cron_jobs_with_comments(self, crontab, mocker):
        """Test handling of comments in crontab."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"# This is a comment\n* * * * * echo test # id: test-id\n"
        
        crons = crontab.get_all()
        assert len(crons) == 1
        assert crons[0].command == "echo test"


class TestUnixInterfaceGetById:
    """Test getting cron job by ID."""
    
    def test_get_by_id_success(self, crontab, mocker):
        """Test successful retrieval by ID."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        cron = crontab.get_by_id("test-id")
        assert cron is not None
        assert cron.id == "test-id"
        assert cron.command == "echo test"
    
    def test_get_by_id_not_found(self, crontab, mocker):
        """Test getting non-existent ID."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: other-id\n"
        
        cron = crontab.get_by_id("test-id")
        assert cron is None
    
    def test_get_by_id_empty(self, crontab):
        """Test getting by ID with empty crontab."""
        with pytest.raises(ValueError, match="Cron ID is required"):
            crontab.get_by_id("")


class TestUnixInterfaceEdit:
    """Test editing cron jobs."""
    
    def test_edit_cron_success(
        self, crontab, config_file, subprocess_check_output, subprocess_run, mocker
    ):
        """Test successful cron job editing."""
        # Mock the initial add operation
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        # Realiza a edição utilizando o identificador único do job
        result = crontab.edit(cron_id="test-id", command="echo edited-command", interval="*/15 0 * * *")
        
        assert result is True
        mock_check_output.assert_called_with(["crontab", "-l"], stderr=subprocess.PIPE)
        subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True, capture_output=True)
    
    def test_edit_cron_not_found(self, crontab, mocker):
        """Test editing non-existent cron job."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: other-id\n"
        
        result = crontab.edit(cron_id="non-existent", command="echo new")
        assert result is False
    
    def test_edit_cron_invalid_id(self, crontab):
        """Test editing with invalid ID."""
        with pytest.raises(ValueError, match="Cron ID is required"):
            crontab.edit(cron_id="", command="echo test")
    
    def test_edit_cron_invalid_command(self, crontab, mocker):
        """Test editing with invalid command."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        with pytest.raises(ValueError, match="Invalid command provided"):
            crontab.edit(cron_id="test-id", command="")


class TestUnixInterfaceDelete:
    """Test deleting cron jobs."""
    
    def test_delete_cron_success(
        self, crontab, config_file, subprocess_check_output, subprocess_run, mocker
    ):
        """Test successful cron job deletion."""
        # Mock the crontab content
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        result = crontab.delete(cron_id="test-id")

        assert result is True
        mock_check_output.assert_called_with(["crontab", "-l"], stderr=subprocess.PIPE)
        subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True, capture_output=True)
    
    def test_delete_cron_not_found(self, crontab, mocker):
        """Test deleting non-existent cron job."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: other-id\n"
        
        result = crontab.delete(cron_id="non-existent")
        assert result is False
    
    def test_delete_cron_invalid_id(self, crontab):
        """Test deleting with invalid ID."""
        with pytest.raises(ValueError, match="Cron ID is required"):
            crontab.delete(cron_id="")


class TestUnixInterfaceClearAll:
    """Test clearing all cron jobs."""
    
    def test_clear_all_success(self, crontab, mocker):
        """Test successful clearing of all cron jobs."""
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        result = crontab.clear_all()
        assert result is True
        mock_run.assert_called_with(["crontab", mocker.ANY], check=True, capture_output=True)
    
    def test_clear_all_failure(self, crontab, mocker):
        """Test clearing all cron jobs when subprocess fails."""
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "crontab")
        
        result = crontab.clear_all()
        assert result is False


class TestUnixInterfaceValidationMethods:
    """Test validation utility methods."""
    
    def test_is_valid_cron_format_valid(self, crontab):
        """Test valid cron format validation."""
        valid_formats = [
            "* * * * *",
            "*/15 * * * *",
            "0 12 * * *",
            "0 0 1 * *"
        ]
        
        for format_str in valid_formats:
            assert crontab.is_valid_cron_format(format_str)
    
    def test_is_valid_cron_format_invalid(self, crontab):
        """Test invalid cron format validation."""
        invalid_formats = [
            "",
            "invalid",
            "* * * *",  # Missing field
            "* * * * * *"  # Too many fields
        ]
        
        for format_str in invalid_formats:
            assert not crontab.is_valid_cron_format(format_str)


class TestUnixInterfaceErrorHandling:
    """Test error handling scenarios."""
    
    def test_get_all_subprocess_error(self, crontab, mocker):
        """Test handling of subprocess errors in get_all."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "crontab")
        
        crons = crontab.get_all()
        assert crons == []
    
    def test_edit_subprocess_error(self, crontab, mocker):
        """Test handling of subprocess errors in edit."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "crontab")
        
        with pytest.raises(RuntimeError, match="Failed to edit cron job"):
            crontab.edit(cron_id="test-id", command="echo new")
    
    def test_delete_subprocess_error(self, crontab, mocker):
        """Test handling of subprocess errors in delete."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "crontab")
        
        result = crontab.delete(cron_id="test-id")
        assert result is False


class TestUnixInterfaceLogging:
    """Test logging functionality."""
    
    def test_logging_on_add(self, crontab, mocker, caplog):
        """Test logging when adding cron job."""
        # Mock the subprocess calls
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b""
        
        with caplog.at_level(logging.INFO):
            cron = crontab.add(command="echo test", interval="* * * * *")
        
        assert f"Successfully added cron job with ID: {cron.id}" in caplog.text
    
    def test_logging_on_get_all(self, crontab, mocker, caplog):
        """Test logging when getting all cron jobs."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        with caplog.at_level(logging.INFO):
            crons = crontab.get_all()
        
        assert "Retrieved 1 cron jobs" in caplog.text
