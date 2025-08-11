import pytest
import platform
import logging
from unittest.mock import patch, Mock
from ppycron.src.base import Cron
from ppycron.src.unix import UnixInterface
from ppycron.src.windows import WindowsInterface
import subprocess


class TestIntegrationBase:
    """Base class for integration tests."""
    
    def setup_method(self):
        """Set up logging for integration tests."""
        logging.basicConfig(level=logging.INFO)


class TestIntegrationUnixInterface(TestIntegrationBase):
    """Integration tests for Unix interface."""
    
    @pytest.fixture
    def unix_interface(self):
        """Create Unix interface with mocked subprocess."""
        with patch('ppycron.src.unix.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            return UnixInterface()
    
    def test_full_cron_lifecycle(self, unix_interface, mocker):
        """Test complete lifecycle: add, get, edit, delete."""
        # Mock subprocess calls
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        
        # Initial empty crontab
        mock_check_output.return_value = b""
        
        # 1. Add a cron job
        cron = unix_interface.add(command="echo 'hello world'", interval="*/5 * * * *")
        assert cron.command == "echo 'hello world'"
        assert cron.interval == "*/5 * * * *"
        assert cron.id
        
        # 2. Get all cron jobs
        mock_check_output.return_value = f"{cron.interval} {cron.command} # id: {cron.id}\n".encode()
        crons = unix_interface.get_all()
        assert len(crons) == 1
        assert crons[0].id == cron.id
        
        # 3. Get specific cron job by ID
        retrieved_cron = unix_interface.get_by_id(cron.id)
        assert retrieved_cron is not None
        assert retrieved_cron.id == cron.id
        
        # 4. Edit the cron job
        mock_check_output.return_value = f"{cron.interval} {cron.command} # id: {cron.id}\n".encode()
        success = unix_interface.edit(cron_id=cron.id, command="echo 'updated command'", interval="*/15 0 * * *")
        assert success is True
        
        # 5. Delete the cron job
        mock_check_output.return_value = f"{cron.interval} {cron.command} # id: {cron.id}\n".encode()
        success = unix_interface.delete(cron_id=cron.id)
        assert success is True
    
    def test_multiple_cron_jobs(self, unix_interface, mocker):
        """Test managing multiple cron jobs."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        
        # Mock initial empty crontab
        mock_check_output.return_value = b""
        
        # Add multiple cron jobs
        cron1 = unix_interface.add(command="echo 'job1'", interval="0 * * * *")
        cron2 = unix_interface.add(command="echo 'job2'", interval="0 0 * * *")
        cron3 = unix_interface.add(command="echo 'job3'", interval="0 0 * * 0")
        
        # Simulate crontab with multiple jobs
        crontab_content = f"""# Sample crontab
{cron1.interval} {cron1.command} # id: {cron1.id}
{cron2.interval} {cron2.command} # id: {cron2.id}
{cron3.interval} {cron3.command} # id: {cron3.id}
"""
        mock_check_output.return_value = crontab_content.encode()
        
        # Get all jobs
        crons = unix_interface.get_all()
        assert len(crons) == 3
        
        # Verify all jobs are present
        cron_ids = [c.id for c in crons]
        assert cron1.id in cron_ids
        assert cron2.id in cron_ids
        assert cron3.id in cron_ids
        
        # Delete one job
        mock_check_output.return_value = crontab_content.encode()
        success = unix_interface.delete(cron_id=cron2.id)
        assert success is True
    
    def test_cron_validation_integration(self, unix_interface):
        """Test cron validation in real scenarios."""
        # Valid cron formats
        valid_intervals = [
            "* * * * *",      # Every minute
            "*/15 * * * *",   # Every 15 minutes
            "0 12 * * *",     # Daily at noon
            "0 0 1 * *",      # Monthly on 1st
            "0 0 * * 0",      # Weekly on Sunday
            "30 2 * * 1-5",   # Weekdays at 2:30 AM
            "0 9,17 * * 1-5", # Weekdays at 9 AM and 5 PM
        ]
        
        for interval in valid_intervals:
            assert unix_interface.is_valid_cron_format(interval)
        
        # Invalid cron formats
        invalid_intervals = [
            "",               # Empty
            "invalid",        # Invalid format
            "* * * *",        # Missing field
            "* * * * * *",    # Too many fields
            "60 * * * *",     # Invalid minute (60 > 59)
            "* 25 * * *",     # Invalid hour (25 > 23)
        ]
        
        for interval in invalid_intervals:
            assert not unix_interface.is_valid_cron_format(interval)
    
    def test_error_handling_integration(self, unix_interface, mocker):
        """Test error handling in integration scenarios."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        
        # Test subprocess errors
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "crontab")
        
        # Should handle errors gracefully
        crons = unix_interface.get_all()
        assert crons == []
        
        # Test with malformed crontab content
        mock_check_output.side_effect = None
        mock_check_output.return_value = b"malformed line\ninvalid cron\n* * * * * echo test # id: test-id\n"
        
        crons = unix_interface.get_all()
        assert len(crons) == 1  # Should only parse valid lines


class TestIntegrationWindowsInterface(TestIntegrationBase):
    """Integration tests for Windows interface."""
    
    @pytest.fixture
    def windows_interface(self):
        """Create Windows interface with mocked subprocess."""
        with patch('ppycron.src.windows.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            return WindowsInterface()
    
    def test_full_task_lifecycle(self, windows_interface, mocker):
        """Test complete lifecycle: add, get, edit, delete."""
        # Mock subprocess calls
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        
        # 1. Add a scheduled task
        cron = windows_interface.add(command="echo 'hello world'", interval="0 12 * * *")
        assert cron.command == "echo 'hello world'"
        assert cron.interval == "0 12 * * *"
        assert cron.id
        
        # 2. Get all tasks
        mock_check_output.return_value = f'"Pycron_{cron.id}","","Ready"\n'.encode()
        mock_xml.return_value = cron
        tasks = windows_interface.get_all()
        assert len(tasks) == 1
        assert tasks[0].id == cron.id
        
        # 3. Get specific task by ID
        retrieved_task = windows_interface.get_by_id(cron.id)
        assert retrieved_task is not None
        assert retrieved_task.id == cron.id
        
        # 4. Edit the task
        mock_xml.return_value = cron
        success = windows_interface.edit(cron_id=cron.id, command="echo 'updated command'")
        assert success is True
        
        # 5. Delete the task
        success = windows_interface.delete(cron_id=cron.id)
        assert success is True
    
    def test_multiple_tasks(self, windows_interface, mocker):
        """Test managing multiple scheduled tasks."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_xml = mocker.patch.object(windows_interface, '_get_task_details')
        
        # Add multiple tasks
        task1 = windows_interface.add(command="echo 'task1'", interval="0 * * * *")
        task2 = windows_interface.add(command="echo 'task2'", interval="0 0 * * *")
        task3 = windows_interface.add(command="echo 'task3'", interval="0 0 * * 0")
        
        # Simulate task list with multiple tasks
        task_list = f'"Pycron_{task1.id}","","Ready"\n"Pycron_{task2.id}","","Ready"\n"Pycron_{task3.id}","","Ready"\n'
        mock_check_output.return_value = task_list.encode()
        
        # Mock XML details for each task
        def mock_get_details(task_name):
            task_id = task_name.replace("Pycron_", "")
            if task_id == task1.id:
                return task1
            elif task_id == task2.id:
                return task2
            elif task_id == task3.id:
                return task3
            return None
        
        mock_xml.side_effect = mock_get_details
        
        # Get all tasks
        tasks = windows_interface.get_all()
        assert len(tasks) == 3
        
        # Verify all tasks are present
        task_ids = [t.id for t in tasks]
        assert task1.id in task_ids
        assert task2.id in task_ids
        assert task3.id in task_ids
        
        # Delete one task
        success = windows_interface.delete(cron_id=task2.id)
        assert success is True
    
    def test_schedule_conversion_integration(self, windows_interface):
        """Test cron to Windows schedule conversion."""
        # Test daily schedules
        schedule = windows_interface._cron_to_windows_schedule("0 12 * * *")
        assert schedule['frequency'] == 'daily'
        assert schedule['start_time'] == '12:00'
        
        # Test minute-based schedules
        schedule = windows_interface._cron_to_windows_schedule("*/15 * * * *")
        assert schedule['frequency'] == 'minute'
        assert schedule['interval'] == 15
        
        # Test weekly schedules
        schedule = windows_interface._cron_to_windows_schedule("0 9 * * 1-5")
        assert schedule['frequency'] == 'weekly'
        assert schedule['days_of_week'] == '2,3,4,5,6'
        
        # Test monthly schedules
        schedule = windows_interface._cron_to_windows_schedule("0 0 1 * *")
        assert schedule['frequency'] == 'monthly'
        assert schedule['days_of_month'] == '1'
        
        # Test complex schedules
        schedule = windows_interface._cron_to_windows_schedule("30 14 1,15 * *")
        assert schedule['frequency'] == 'monthly'
        assert schedule['days_of_month'] == '1,15'
    
    def test_clear_all_integration(self, windows_interface, mocker):
        """Test clearing all tasks."""
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        
        # Simulate multiple Pycron tasks
        task_list = '"Pycron_task1","","Ready"\n"Pycron_task2","","Ready"\n"OtherTask","","Ready"\n'
        mock_check_output.return_value = task_list.encode()
        
        success = windows_interface.clear_all()
        assert success is True
        
        # Should only delete Pycron tasks (2 calls)
        assert mock_run.call_count == 2
    
    def test_error_handling_integration(self, windows_interface, mocker):
        """Test error handling in integration scenarios."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        
        # Test subprocess errors
        mock_run.side_effect = subprocess.CalledProcessError(1, "schtasks")
        
        # Should handle errors gracefully
        crons = windows_interface.get_all()
        assert crons == []
        
        # Test with malformed CSV content
        mock_run.side_effect = None
        mock_run.return_value.stdout = b"TaskName,Status\nPycron_test,Ready\n"
        
        crons = windows_interface.get_all()
        assert len(crons) == 0  # Should handle parsing errors gracefully


class TestIntegrationCrossPlatform(TestIntegrationBase):
    """Cross-platform integration tests."""
    
    def test_interface_selection(self):
        """Test automatic interface selection based on platform."""
        system = platform.system().lower()
        
        if system == "windows":
            # Should be able to create Windows interface
            with patch('ppycron.src.windows.subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                interface = WindowsInterface()
                assert interface.operational_system == "windows"
        else:
            # Should be able to create Unix interface
            with patch('ppycron.src.unix.subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                interface = UnixInterface()
                assert interface.operational_system == "linux"
    
    def test_common_interface_methods(self, mocker):
        """Test that both interfaces implement the same methods."""
        # Mock subprocess for both interfaces
        with patch('ppycron.src.unix.subprocess.run') as mock_run_unix:
            with patch('ppycron.src.windows.subprocess.run') as mock_run_windows:
                mock_run_unix.return_value.returncode = 0
                mock_run_windows.return_value.returncode = 0
                
                unix_interface = UnixInterface()
                windows_interface = WindowsInterface()
                
                # Both should have the same basic methods
                common_methods = ['add', 'get_all', 'get_by_id', 'edit', 'delete', 'clear_all']
                
                for method in common_methods:
                    assert hasattr(unix_interface, method)
                    assert hasattr(windows_interface, method)
    
    def test_cron_object_consistency(self):
        """Test that Cron objects are consistent across platforms."""
        # Test Unix interface
        with patch('ppycron.src.unix.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            unix_interface = UnixInterface()
            
            # Mock check_output for add operation
            with patch('ppycron.src.unix.subprocess.check_output') as mock_check:
                mock_check.return_value = b""
                unix_cron = unix_interface.add(command="echo test", interval="* * * * *")
        
        # Test Windows interface
        with patch('ppycron.src.windows.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            windows_interface = WindowsInterface()
            
            # Mock check_output for add operation
            with patch('ppycron.src.windows.subprocess.check_output') as mock_check:
                mock_check.return_value = b""
                windows_cron = windows_interface.add(command="echo test", interval="* * * * *")
        
        # Verify both objects have the same structure
        assert hasattr(unix_cron, 'command')
        assert hasattr(unix_cron, 'interval')
        assert hasattr(unix_cron, 'id')
        
        assert hasattr(windows_cron, 'command')
        assert hasattr(windows_cron, 'interval')
        assert hasattr(windows_cron, 'id')
        
        # Verify they have the same command and interval
        assert unix_cron.command == windows_cron.command
        assert unix_cron.interval == windows_cron.interval


class TestIntegrationPerformance(TestIntegrationBase):
    """Performance and stress tests."""
    
    def test_multiple_operations_performance(self, mocker):
        """Test performance with multiple operations."""
        with patch('ppycron.src.unix.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            # Mock check_output
            mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
            mock_check_output.return_value = b""
            
            interface = UnixInterface()
            
            # Add multiple cron jobs quickly
            crons = []
            for i in range(10):
                cron = interface.add(command=f"echo 'job{i}'", interval="* * * * *")
                crons.append(cron)
            
            assert len(crons) == 10
            assert len(set(c.id for c in crons)) == 10  # All IDs should be unique
    
    def test_large_crontab_handling(self, mocker):
        """Test handling of large crontab files."""
        with patch('ppycron.src.unix.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            interface = UnixInterface()
            
            # Simulate large crontab content
            large_crontab = []
            for i in range(100):
                large_crontab.append(f"* * * * * echo 'job{i}' # id: job-{i}")
            
            mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
            mock_check_output.return_value = "\n".join(large_crontab).encode()
            
            crons = interface.get_all()
            assert len(crons) == 100
    
    def test_concurrent_operations(self, mocker):
        """Test handling of concurrent-like operations."""
        with patch('ppycron.src.unix.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            interface = UnixInterface()
            
            # Mock check_output for add operation
            mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
            mock_check_output.return_value = b""
            
            # Simulate rapid add/delete operations
            cron = interface.add(command="echo test", interval="* * * * *")
            
            # Mock the delete operation - simulate crontab with the job to be deleted
            mock_check_output.return_value = f"* * * * * echo test # id: {cron.id}\n".encode()
            
            # Immediately try to delete
            success = interface.delete(cron_id=cron.id)
            assert success is True
            
            # Mock get_by_id to return None (job was deleted)
            mock_check_output.return_value = b""
            
            # Try to get by ID (should return None since job was deleted)
            retrieved = interface.get_by_id(cron.id)
            assert retrieved is None
