import os
import pytest
import logging
import subprocess
from unittest.mock import Mock, patch, call
from ppycron.src.base import Cron
from ppycron.src.windows import WindowsInterface


@pytest.fixture
def subprocess_run(mocker):
    yield mocker.patch("ppycron.src.windows.subprocess.run")


@pytest.fixture
def subprocess_check_output(mocker):
    return mocker.patch("ppycron.src.windows.subprocess.check_output")


@pytest.fixture
def windows_interface(mocker):
    """Create Windows interface with mocked subprocess."""
    # Mock the subprocess calls to avoid actual Windows commands
    mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
    mock_run.return_value.returncode = 0
    
    # Mock the initialization check
    with patch('ppycron.src.windows.subprocess.run') as mock_init:
        mock_init.return_value.returncode = 0
        return WindowsInterface()


class TestWindowsInterfaceInitialization:
    """Test Windows interface initialization."""
    
    def test_init_success(self, mocker):
        """Test successful initialization."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        interface = WindowsInterface()
        assert interface.operational_system == "windows"
        mock_run.assert_called()
    
    def test_init_schtasks_not_found(self, mocker):
        """Test initialization when schtasks command is not found."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.side_effect = FileNotFoundError("schtasks: command not found")
        
        with pytest.raises(RuntimeError, match="schtasks command not found"):
            WindowsInterface()


class TestWindowsInterfaceValidation:
    """Test validation methods."""
    
    def test_validate_interval_valid_formats(self, mocker):
        """Test valid cron interval formats."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
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
    
    def test_validate_interval_invalid_formats(self, mocker):
        """Test invalid cron interval formats."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
        invalid_intervals = [
            "",  # Empty
            "invalid",  # Not enough fields
        ]
        
        for interval in invalid_intervals:
            assert not interface._validate_interval(interval), f"Should not validate: {interval}"
    
    def test_validate_command_valid(self, mocker):
        """Test valid command validation."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
        valid_commands = [
            "echo hello",
            "python script.py",
            "C:\\path\\to\\command.exe",
            "echo 'hello world'"
        ]
        
        for command in valid_commands:
            assert interface._validate_command(command), f"Failed to validate: {command}"
    
    def test_validate_command_invalid(self, mocker):
        """Test invalid command validation."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
        invalid_commands = [
            "",  # Empty
            "   ",  # Whitespace only
            None,  # None
        ]
        
        for command in invalid_commands:
            assert not interface._validate_command(command), f"Should not validate: {command}"


class TestWindowsInterfaceCronToWindowsSchedule:
    """Test cron to Windows schedule conversion."""
    
    def test_cron_to_windows_schedule_daily(self, mocker):
        """Test daily schedule conversion."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
        schedule = interface._cron_to_windows_schedule("0 12 * * *")
        assert schedule['frequency'] == 'daily'
        assert schedule['start_time'] == '12:00'
    
    def test_cron_to_windows_schedule_minutes(self, mocker):
        """Test minute-based schedule conversion."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
        schedule = interface._cron_to_windows_schedule("*/15 * * * *")
        assert schedule['frequency'] == 'minute'
        assert schedule['interval'] == 15
    
    def test_cron_to_windows_schedule_weekly(self, mocker):
        """Test weekly schedule conversion."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
        schedule = interface._cron_to_windows_schedule("0 9 * * 1-5")
        assert schedule['frequency'] == 'weekly'
        assert schedule['days_of_week'] == '2,3,4,5,6'
    
    def test_cron_to_windows_schedule_monthly(self, mocker):
        """Test monthly schedule conversion."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        interface = WindowsInterface()
        
        schedule = interface._cron_to_windows_schedule("0 0 1 * *")
        assert schedule['frequency'] == 'monthly'
        assert schedule['days_of_month'] == '1'


class TestWindowsInterfaceAdd:
    """Test adding scheduled tasks."""
    
    def test_add_task_success(self, windows_interface, mocker):
        """Test successful task addition."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        cron = windows_interface.add(command="echo test", interval="0 12 * * *")
        
        assert isinstance(cron, Cron)
        assert cron.command == "echo test"
        assert cron.interval == "0 12 * * *"
        assert cron.id and isinstance(cron.id, str)
        
        # Verify schtasks command was called with correct parameters
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        
        # Check essential arguments
        assert "schtasks" in call_args
        assert "/create" in call_args
        assert "/tn" in call_args
        assert "/tr" in call_args
        assert "/sc" in call_args
        assert "daily" in call_args
        assert "cmd.exe /c echo test" in call_args
    
    def test_add_task_invalid_command(self, windows_interface):
        """Test adding task with invalid command."""
        with pytest.raises(ValueError, match="Invalid command provided"):
            windows_interface.add(command="", interval="* * * * *")
    
    def test_add_task_invalid_interval(self, windows_interface):
        """Test adding task with invalid interval."""
        with pytest.raises(ValueError, match="Invalid interval format"):
            windows_interface.add(command="echo test", interval="invalid")
    
    def test_add_task_subprocess_error(self, windows_interface, mocker):
        """Test adding task when subprocess fails."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        with pytest.raises(RuntimeError, match="Failed to add Windows task"):
            windows_interface.add(command="echo test", interval="* * * * *")


class TestWindowsInterfaceGetAll:
    """Test getting all scheduled tasks."""
    
    def test_get_all_success(self, windows_interface, mocker):
        """Test successful retrieval of tasks."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_test-id","","Ready"\n"OtherTask","","Ready"\n'
        
        # Mock XML export for task details
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        mock_xml.return_value = Cron(command="echo test", interval="* * * * *", id="test-id")
        
        tasks = windows_interface.get_all()
        
        assert len(tasks) == 1
        assert tasks[0].id == "test-id"
        mock_check_output.assert_called_with(["schtasks", "/query", "/fo", "csv", "/nh"], stderr=subprocess.PIPE)
    
    def test_get_all_empty(self, windows_interface, mocker):
        """Test getting tasks when none exist."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        tasks = windows_interface.get_all()
        assert tasks == []
    
    def test_get_all_no_pycron_tasks(self, windows_interface, mocker):
        """Test getting tasks when no Pycron tasks exist."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"OtherTask","","Ready"\n"AnotherTask","","Ready"\n'
        
        tasks = windows_interface.get_all()
        assert tasks == []


class TestWindowsInterfaceGetById:
    """Test getting task by ID."""
    
    def test_get_by_id_success(self, windows_interface, mocker):
        """Test successful retrieval by ID."""
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        mock_xml.return_value = Cron(command="echo test", interval="* * * * *", id="test-id")
        
        task = windows_interface.get_by_id("test-id")
        assert task is not None
        assert task.id == "test-id"
        assert task.command == "echo test"
    
    def test_get_by_id_not_found(self, windows_interface, mocker):
        """Test getting non-existent ID."""
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        mock_xml.return_value = None
        
        task = windows_interface.get_by_id("non-existent")
        assert task is None
    
    def test_get_by_id_empty(self, windows_interface):
        """Test getting by ID with empty ID."""
        with pytest.raises(ValueError, match="Cron ID is required"):
            windows_interface.get_by_id("")


class TestWindowsInterfaceEdit:
    """Test editing scheduled tasks."""
    
    def test_edit_task_success(self, windows_interface, mocker):
        """Test successful task editing."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        # Mock getting current task details
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        mock_xml.return_value = Cron(command="echo old", interval="0 12 * * *", id="test-id")
        
        result = windows_interface.edit(cron_id="test-id", command="echo new")
        
        assert result is True
        # Verify delete and create were called
        assert mock_run.call_count == 2
    
    def test_edit_task_not_found(self, windows_interface, mocker):
        """Test editing non-existent task."""
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        mock_xml.return_value = None
        
        result = windows_interface.edit(cron_id="non-existent", command="echo new")
        assert result is False
    
    def test_edit_task_invalid_id(self, windows_interface):
        """Test editing with invalid ID."""
        with pytest.raises(ValueError, match="Task ID is required"):
            windows_interface.edit(cron_id="", command="echo test")
    
    def test_edit_task_invalid_command(self, windows_interface, mocker):
        """Test editing with invalid command."""
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        mock_xml.return_value = Cron(command="echo old", interval="* * * * *", id="test-id")
        
        with pytest.raises(ValueError, match="Invalid command provided"):
            windows_interface.edit(cron_id="test-id", command="")


class TestWindowsInterfaceDelete:
    """Test deleting scheduled tasks."""
    
    def test_delete_task_success(self, windows_interface, mocker):
        """Test successful task deletion."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        result = windows_interface.delete(cron_id="test-id")
        
        assert result is True
        mock_run.assert_called_with(
            ["schtasks", "/delete", "/tn", "Pycron_test-id", "/f"],
            capture_output=True, check=True
        )
    
    def test_delete_task_subprocess_error(self, windows_interface, mocker):
        """Test deleting task when subprocess fails."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        result = windows_interface.delete(cron_id="test-id")
        assert result is False
    
    def test_delete_task_invalid_id(self, windows_interface):
        """Test deleting with invalid ID."""
        with pytest.raises(ValueError, match="Cron ID is required"):
            windows_interface.delete(cron_id="")


class TestWindowsInterfaceClearAll:
    """Test clearing all scheduled tasks."""
    
    def test_clear_all_success(self, windows_interface, mocker):
        """Test successful clearing of all tasks."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_task1","","Ready"\n"Pycron_task2","","Ready"\n'
        
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        result = windows_interface.clear_all()
        
        assert result is True
        # Verify delete was called for each Pycron task
        assert mock_run.call_count == 2
    
    def test_clear_all_no_tasks(self, windows_interface, mocker):
        """Test clearing when no Pycron tasks exist."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"OtherTask","","Ready"\n'
        
        result = windows_interface.clear_all()
        assert result is True
    
    def test_clear_all_subprocess_error(self, windows_interface, mocker):
        """Test clearing when subprocess fails."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        result = windows_interface.clear_all()
        assert result is False


class TestWindowsInterfaceGetTaskDetails:
    """Test getting task details from XML."""
    
    def test_get_task_details_success(self, windows_interface, mocker):
        """Test successful XML parsing."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>/c echo test</Arguments>
    </Exec>
  </Actions>
</Task>'''
        
        task = windows_interface._get_task_details("Pycron_test-id")
        
        assert task is not None
        assert task.command == "echo test"
        assert task.id == "test-id"
    
    def test_get_task_details_xml_error(self, windows_interface, mocker):
        """Test XML parsing error."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b"Invalid XML"
        
        task = windows_interface._get_task_details("Pycron_test-id")
        assert task is None
    
    def test_get_task_details_subprocess_error(self, windows_interface, mocker):
        """Test subprocess error when getting task details."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        task = windows_interface._get_task_details("Pycron_test-id")
        assert task is None


class TestWindowsInterfaceValidationMethods:
    """Test validation utility methods."""
    
    def test_is_valid_cron_format_valid(self, windows_interface):
        """Test valid cron format validation."""
        valid_formats = [
            "* * * * *",
            "*/15 * * * *",
            "0 12 * * *",
            "0 0 1 * *"
        ]
        
        for format_str in valid_formats:
            assert windows_interface.is_valid_cron_format(format_str)
    
    def test_is_valid_cron_format_invalid(self, windows_interface):
        """Test invalid cron format validation."""
        invalid_formats = [
            "",
            "invalid",
            "* * * *",  # Missing field
            "* * * * * *"  # Too many fields
        ]
        
        for format_str in invalid_formats:
            assert not windows_interface.is_valid_cron_format(format_str)


class TestWindowsInterfaceErrorHandling:
    """Test error handling scenarios."""
    
    def test_get_all_subprocess_error(self, windows_interface, mocker):
        """Test handling of subprocess errors in get_all."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        tasks = windows_interface.get_all()
        assert tasks == []
    
    def test_edit_subprocess_error(self, windows_interface, mocker):
        """Test handling of subprocess errors in edit."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        # The method returns False when task is not found due to subprocess error
        result = windows_interface.edit(cron_id="test-id", command="echo new")
        assert result is False


class TestWindowsInterfaceLogging:
    """Test logging functionality."""
    
    def test_logging_on_add(self, windows_interface, mocker, caplog):
        """Test logging when adding task."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        with caplog.at_level(logging.INFO):
            cron = windows_interface.add(command="echo test", interval="* * * * *")
        
        assert f"Successfully added Windows task with ID: {cron.id}" in caplog.text
    
    def test_logging_on_get_all(self, windows_interface, mocker, caplog):
        """Test logging when getting all tasks."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_test-id","","Ready"\n'
        
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        mock_xml.return_value = Cron(command="echo test", interval="* * * * *", id="test-id")
        
        with caplog.at_level(logging.INFO):
            tasks = windows_interface.get_all()
        
        assert "Retrieved 1 Windows scheduled tasks" in caplog.text
