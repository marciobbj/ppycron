import pytest
import logging
from unittest.mock import Mock, patch
from ppycron.src.base import Cron, BaseInterface
from ppycron.src.unix import UnixInterface
from ppycron.src.windows import WindowsInterface


class TestCronObjectMethods:
    """Test Cron object methods."""
    
    def test_to_dict(self):
        """Test converting Cron object to dictionary."""
        cron = Cron(command="echo test", interval="* * * * *", id="test-id")
        cron_dict = cron.to_dict()
        
        expected = {
            'id': 'test-id',
            'command': 'echo test',
            'interval': '* * * * *'
        }
        assert cron_dict == expected
    
    def test_from_dict(self):
        """Test creating Cron object from dictionary."""
        data = {
            'id': 'test-id',
            'command': 'echo test',
            'interval': '* * * * *'
        }
        cron = Cron.from_dict(data)
        
        assert cron.id == 'test-id'
        assert cron.command == 'echo test'
        assert cron.interval == '* * * * *'
    
    def test_from_dict_without_id(self):
        """Test creating Cron object from dictionary without ID."""
        data = {
            'command': 'echo test',
            'interval': '* * * * *'
        }
        cron = Cron.from_dict(data)
        
        assert cron.id is not None
        assert cron.command == 'echo test'
        assert cron.interval == '* * * * *'
    
    def test_str_representation(self):
        """Test string representation of Cron object."""
        cron = Cron(command="echo test", interval="* * * * *", id="test-id")
        expected = "* * * * * echo test # id: test-id"
        assert str(cron) == expected


class TestBaseInterfaceAuxiliaryMethods:
    """Test auxiliary methods in BaseInterface."""
    
    def test_count_empty(self, mocker):
        """Test count method with empty list."""
        mock_interface = Mock(spec=BaseInterface)
        mock_interface.get_all.return_value = []
        mock_interface.count = BaseInterface.count.__get__(mock_interface)
        
        count = mock_interface.count()
        assert count == 0
    
    def test_count_with_tasks(self, mocker):
        """Test count method with tasks."""
        mock_interface = Mock(spec=BaseInterface)
        mock_interface.get_all.return_value = [
            Cron("echo 1", "* * * * *", "id1"),
            Cron("echo 2", "0 * * * *", "id2"),
            Cron("echo 3", "0 0 * * *", "id3")
        ]
        mock_interface.count = BaseInterface.count.__get__(mock_interface)
        
        count = mock_interface.count()
        assert count == 3
    
    def test_exists_true(self, mocker):
        """Test exists method when task exists."""
        mock_interface = Mock(spec=BaseInterface)
        mock_interface.get_by_id.return_value = Cron("echo test", "* * * * *", "test-id")
        mock_interface.exists = BaseInterface.exists.__get__(mock_interface)
        
        exists = mock_interface.exists("test-id")
        assert exists is True
        mock_interface.get_by_id.assert_called_once_with("test-id")
    
    def test_exists_false(self, mocker):
        """Test exists method when task doesn't exist."""
        mock_interface = Mock(spec=BaseInterface)
        mock_interface.get_by_id.return_value = None
        mock_interface.exists = BaseInterface.exists.__get__(mock_interface)
        
        exists = mock_interface.exists("non-existent-id")
        assert exists is False
        mock_interface.get_by_id.assert_called_once_with("non-existent-id")
    
    def test_get_by_command(self, mocker):
        """Test get_by_command method."""
        mock_interface = Mock(spec=BaseInterface)
        all_tasks = [
            Cron("echo backup", "* * * * *", "id1"),
            Cron("echo test", "0 * * * *", "id2"),
            Cron("echo backup", "0 0 * * *", "id3")
        ]
        mock_interface.get_all.return_value = all_tasks
        mock_interface.get_by_command = BaseInterface.get_by_command.__get__(mock_interface)
        
        backup_tasks = mock_interface.get_by_command("echo backup")
        assert len(backup_tasks) == 2
        assert all(task.command == "echo backup" for task in backup_tasks)
    
    def test_get_by_interval(self, mocker):
        """Test get_by_interval method."""
        mock_interface = Mock(spec=BaseInterface)
        all_tasks = [
            Cron("echo 1", "* * * * *", "id1"),
            Cron("echo 2", "0 * * * *", "id2"),
            Cron("echo 3", "0 * * * *", "id3")
        ]
        mock_interface.get_all.return_value = all_tasks
        mock_interface.get_by_interval = BaseInterface.get_by_interval.__get__(mock_interface)
        
        hourly_tasks = mock_interface.get_by_interval("0 * * * *")
        assert len(hourly_tasks) == 2
        assert all(task.interval == "0 * * * *" for task in hourly_tasks)
    
    def test_delete_by_command(self, mocker):
        """Test delete_by_command method."""
        mock_interface = Mock(spec=BaseInterface)
        tasks_to_delete = [
            Cron("echo backup", "* * * * *", "id1"),
            Cron("echo backup", "0 * * * *", "id2")
        ]
        mock_interface.get_by_command.return_value = tasks_to_delete
        mock_interface.delete.return_value = True
        mock_interface.delete_by_command = BaseInterface.delete_by_command.__get__(mock_interface)
        
        deleted_count = mock_interface.delete_by_command("echo backup")
        assert deleted_count == 2
        assert mock_interface.delete.call_count == 2
    
    def test_delete_by_interval(self, mocker):
        """Test delete_by_interval method."""
        mock_interface = Mock(spec=BaseInterface)
        tasks_to_delete = [
            Cron("echo 1", "0 * * * *", "id1"),
            Cron("echo 2", "0 * * * *", "id2")
        ]
        mock_interface.get_by_interval.return_value = tasks_to_delete
        mock_interface.delete.return_value = True
        mock_interface.delete_by_interval = BaseInterface.delete_by_interval.__get__(mock_interface)
        
        deleted_count = mock_interface.delete_by_interval("0 * * * *")
        assert deleted_count == 2
        assert mock_interface.delete.call_count == 2
    
    def test_update_command(self, mocker):
        """Test update_command method."""
        mock_interface = Mock(spec=BaseInterface)
        mock_interface.edit.return_value = True
        mock_interface.update_command = BaseInterface.update_command.__get__(mock_interface)
        
        success = mock_interface.update_command("test-id", "new_command")
        assert success is True
        mock_interface.edit.assert_called_once_with("test-id", command="new_command")
    
    def test_update_interval(self, mocker):
        """Test update_interval method."""
        mock_interface = Mock(spec=BaseInterface)
        mock_interface.edit.return_value = True
        mock_interface.update_interval = BaseInterface.update_interval.__get__(mock_interface)
        
        success = mock_interface.update_interval("test-id", "0 3 * * *")
        assert success is True
        mock_interface.edit.assert_called_once_with("test-id", interval="0 3 * * *")
    
    def test_duplicate_success(self, mocker):
        """Test duplicate method success."""
        mock_interface = Mock(spec=BaseInterface)
        original_task = Cron("echo test", "* * * * *", "original-id")
        new_task = Cron("echo test", "0 3 * * *", "new-id")
        
        mock_interface.get_by_id.return_value = original_task
        mock_interface.add.return_value = new_task
        mock_interface.duplicate = BaseInterface.duplicate.__get__(mock_interface)
        
        duplicated = mock_interface.duplicate("original-id", "0 3 * * *")
        assert duplicated == new_task
        mock_interface.add.assert_called_once_with("echo test", "0 3 * * *")
    
    def test_duplicate_without_new_interval(self, mocker):
        """Test duplicate method without new interval."""
        mock_interface = Mock(spec=BaseInterface)
        original_task = Cron("echo test", "* * * * *", "original-id")
        new_task = Cron("echo test", "* * * * *", "new-id")
        
        mock_interface.get_by_id.return_value = original_task
        mock_interface.add.return_value = new_task
        mock_interface.duplicate = BaseInterface.duplicate.__get__(mock_interface)
        
        duplicated = mock_interface.duplicate("original-id")
        assert duplicated == new_task
        mock_interface.add.assert_called_once_with("echo test", "* * * * *")
    
    def test_duplicate_task_not_found(self, mocker):
        """Test duplicate method when task not found."""
        mock_interface = Mock(spec=BaseInterface)
        mock_interface.get_by_id.return_value = None
        mock_interface.duplicate = BaseInterface.duplicate.__get__(mock_interface)
        
        duplicated = mock_interface.duplicate("non-existent-id")
        assert duplicated is None
        mock_interface.add.assert_not_called()


class TestUnixInterfaceAuxiliaryMethods:
    """Test auxiliary methods in UnixInterface."""
    
    @pytest.fixture
    def unix_interface(self, mocker):
        """Create UnixInterface with mocked subprocess."""
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        return UnixInterface()
    
    def test_count_method(self, unix_interface, mocker):
        """Test count method."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test1 # id: id1\n* * * * * echo test2 # id: id2\n"
        
        count = unix_interface.count()
        assert count == 2
    
    def test_exists_method_true(self, unix_interface, mocker):
        """Test exists method when task exists."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        exists = unix_interface.exists("test-id")
        assert exists is True
    
    def test_exists_method_false(self, unix_interface, mocker):
        """Test exists method when task doesn't exist."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: other-id\n"
        
        exists = unix_interface.exists("test-id")
        assert exists is False
    
    def test_get_by_command(self, unix_interface, mocker):
        """Test get_by_command method."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo backup # id: id1\n0 * * * * echo test # id: id2\n0 0 * * * echo backup # id: id3\n"
        
        backup_tasks = unix_interface.get_by_command("echo backup")
        assert len(backup_tasks) == 2
        assert all(task.command == "echo backup" for task in backup_tasks)
    
    def test_get_by_interval(self, unix_interface, mocker):
        """Test get_by_interval method."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test1 # id: id1\n0 * * * * echo test2 # id: id2\n0 * * * * echo test3 # id: id3\n"
        
        hourly_tasks = unix_interface.get_by_interval("0 * * * *")
        assert len(hourly_tasks) == 2
        assert all(task.interval == "0 * * * *" for task in hourly_tasks)
    
    def test_delete_by_command(self, unix_interface, mocker):
        """Test delete_by_command method."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo backup # id: id1\n0 * * * * echo test # id: id2\n0 0 * * * echo backup # id: id3\n"
        
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        deleted_count = unix_interface.delete_by_command("echo backup")
        assert deleted_count == 2
    
    def test_delete_by_interval(self, unix_interface, mocker):
        """Test delete_by_interval method."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test1 # id: id1\n0 * * * * echo test2 # id: id2\n0 * * * * echo test3 # id: id3\n"
        
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        deleted_count = unix_interface.delete_by_interval("0 * * * *")
        assert deleted_count == 2
    
    def test_update_command(self, unix_interface, mocker):
        """Test update_command method."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        success = unix_interface.update_command("test-id", "new_command")
        assert success is True
    
    def test_update_interval(self, unix_interface, mocker):
        """Test update_interval method."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: test-id\n"
        
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        success = unix_interface.update_interval("test-id", "0 3 * * *")
        assert success is True
    
    def test_duplicate_success(self, unix_interface, mocker):
        """Test duplicate method success."""
        # Mock get_by_id
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: original-id\n"
        
        # Mock add operation
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        duplicated = unix_interface.duplicate("original-id", "0 3 * * *")
        assert duplicated is not None
        assert duplicated.command == "echo test"
        assert duplicated.interval == "0 3 * * *"
    
    def test_duplicate_task_not_found(self, unix_interface, mocker):
        """Test duplicate method when task not found."""
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b"* * * * * echo test # id: other-id\n"
        
        duplicated = unix_interface.duplicate("non-existent-id")
        assert duplicated is None


class TestWindowsInterfaceAuxiliaryMethods:
    """Test auxiliary methods in WindowsInterface."""
    
    @pytest.fixture
    def windows_interface(self, mocker):
        """Create WindowsInterface with mocked subprocess."""
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        return WindowsInterface()
    
    def test_count_method(self, windows_interface, mocker):
        """Test count method."""
        # Mock _get_all_tasks to return task names
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_id1","",""\n"Pycron_id2","",""\n'
        
        # Mock _get_task_details to return valid Cron objects
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.side_effect = [
            Cron("echo test1", "* * * * *", "id1"),
            Cron("echo test2", "0 * * * *", "id2")
        ]
        
        count = windows_interface.count()
        assert count == 2
    
    def test_exists_method_true(self, windows_interface, mocker):
        """Test exists method when task exists."""
        # Mock _get_task_details to return a valid Cron object
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.return_value = Cron("echo test", "* * * * *", "test-id")
        
        exists = windows_interface.exists("test-id")
        assert exists is True
    
    def test_exists_method_false(self, windows_interface, mocker):
        """Test exists method when task doesn't exist."""
        # Mock _get_task_details to return None
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.return_value = None
        
        exists = windows_interface.exists("test-id")
        assert exists is False
    
    def test_get_by_command(self, windows_interface, mocker):
        """Test get_by_command method."""
        # Mock _get_all_tasks
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_id1","",""\n"Pycron_id2","",""\n"Pycron_id3","",""\n'
        
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.side_effect = [
            Cron("echo backup", "* * * * *", "id1"),
            Cron("echo test", "0 * * * *", "id2"),
            Cron("echo backup", "0 0 * * *", "id3")
        ]
        
        backup_tasks = windows_interface.get_by_command("echo backup")
        assert len(backup_tasks) == 2
        assert all(task.command == "echo backup" for task in backup_tasks)
    
    def test_get_by_interval(self, windows_interface, mocker):
        """Test get_by_interval method."""
        # Mock _get_all_tasks
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_id1","",""\n"Pycron_id2","",""\n"Pycron_id3","",""\n'
        
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.side_effect = [
            Cron("echo test1", "* * * * *", "id1"),
            Cron("echo test2", "0 * * * *", "id2"),
            Cron("echo test3", "0 * * * *", "id3")
        ]
        
        hourly_tasks = windows_interface.get_by_interval("0 * * * *")
        assert len(hourly_tasks) == 2
        assert all(task.interval == "0 * * * *" for task in hourly_tasks)
    
    def test_delete_by_command(self, windows_interface, mocker):
        """Test delete_by_command method."""
        # Mock _get_all_tasks
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_id1","",""\n"Pycron_id2","",""\n"Pycron_id3","",""\n'
        
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.side_effect = [
            Cron("echo backup", "* * * * *", "id1"),
            Cron("echo test", "0 * * * *", "id2"),
            Cron("echo backup", "0 0 * * *", "id3")
        ]
        
        # Mock delete
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        deleted_count = windows_interface.delete_by_command("echo backup")
        assert deleted_count == 2
    
    def test_delete_by_interval(self, windows_interface, mocker):
        """Test delete_by_interval method."""
        # Mock _get_all_tasks
        mock_check_output = mocker.patch("ppycron.src.windows.subprocess.check_output")
        mock_check_output.return_value = b'"Pycron_id1","",""\n"Pycron_id2","",""\n"Pycron_id3","",""\n'
        
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.side_effect = [
            Cron("echo test1", "* * * * *", "id1"),
            Cron("echo test2", "0 * * * *", "id2"),
            Cron("echo test3", "0 * * * *", "id3")
        ]
        
        # Mock delete
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        deleted_count = windows_interface.delete_by_interval("0 * * * *")
        assert deleted_count == 2
    
    def test_update_command(self, windows_interface, mocker):
        """Test update_command method."""
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.return_value = Cron("echo test", "* * * * *", "test-id")
        
        # Mock delete and create operations
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        success = windows_interface.update_command("test-id", "new_command")
        assert success is True
    
    def test_update_interval(self, windows_interface, mocker):
        """Test update_interval method."""
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.return_value = Cron("echo test", "* * * * *", "test-id")
        
        # Mock delete and create operations
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        success = windows_interface.update_interval("test-id", "0 3 * * *")
        assert success is True
    
    def test_duplicate_success(self, windows_interface, mocker):
        """Test duplicate method success."""
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.return_value = Cron("echo test", "* * * * *", "original-id")
        
        # Mock add operation
        mock_run = mocker.patch("ppycron.src.windows.subprocess.run")
        mock_run.return_value.returncode = 0
        
        duplicated = windows_interface.duplicate("original-id", "0 3 * * *")
        assert duplicated is not None
        assert duplicated.command == "echo test"
        assert duplicated.interval == "0 3 * * *"
    
    def test_duplicate_task_not_found(self, windows_interface, mocker):
        """Test duplicate method when task not found."""
        # Mock _get_task_details
        windows_interface._get_task_details = Mock()
        windows_interface._get_task_details.return_value = None
        
        duplicated = windows_interface.duplicate("non-existent-id")
        assert duplicated is None


class TestConsistencyAndPersistence:
    """Test consistency between add() and get_all() methods."""
    
    @pytest.fixture
    def unix_interface(self, mocker):
        """Create UnixInterface with mocked subprocess."""
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        return UnixInterface()
    
    def test_add_get_all_consistency(self, unix_interface, mocker):
        """Test that add() and get_all() work consistently."""
        # Mock initial empty crontab
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b""
        
        # Mock run for add operation
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        # Add a task
        cron = unix_interface.add("echo test", "* * * * *")
        
        # Mock get_all to return the task we just added
        mock_check_output.return_value = f"{cron.interval} {cron.command} # id: {cron.id}\n".encode()
        
        # Get all tasks
        all_tasks = unix_interface.get_all()
        
        # Verify consistency
        assert len(all_tasks) == 1
        assert all_tasks[0].id == cron.id
        assert all_tasks[0].command == cron.command
        assert all_tasks[0].interval == cron.interval
    
    def test_persistence_across_operations(self, unix_interface, mocker):
        """Test that tasks persist across multiple operations."""
        # Mock initial empty crontab
        mock_check_output = mocker.patch("ppycron.src.unix.subprocess.check_output")
        mock_check_output.return_value = b""
        
        # Mock run for operations
        mock_run = mocker.patch("ppycron.src.unix.subprocess.run")
        mock_run.return_value.returncode = 0
        
        # Add multiple tasks
        tasks = []
        for i in range(3):
            cron = unix_interface.add(f"echo task{i}", f"{i} * * * *")
            tasks.append(cron)
        
        # Mock get_all to return all tasks
        crontab_content = ""
        for task in tasks:
            crontab_content += f"{task.interval} {task.command} # id: {task.id}\n"
        mock_check_output.return_value = crontab_content.encode()
        
        # Get all tasks
        all_tasks = unix_interface.get_all()
        
        # Verify all tasks are present
        assert len(all_tasks) == 3
        for i, task in enumerate(tasks):
            assert any(t.id == task.id for t in all_tasks)
            assert any(t.command == task.command for t in all_tasks)
            assert any(t.interval == task.interval for t in all_tasks)

