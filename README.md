# PPyCron - Cross-Platform Cron Management

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-138%20passing%20%F0%9F%8E%89-brightgreen.svg)](https://github.com/yourusername/ppycron)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/yourusername/ppycron)

**PPyCron** is a modern, cross-platform Python library for managing scheduled tasks. It provides a unified API for both Unix/Linux cron jobs and Windows Task Scheduler, making it easy to schedule and manage tasks across different operating systems.

## Features

- **Cross-Platform Support**: Works on Unix/Linux and Windows
- **Robust Validation**: Validates cron formats and command syntax
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Unified API**: Same interface across all platforms
- **Advanced Queries**: Find tasks by ID, get all tasks, validate formats
- **High Performance**: Optimized for handling large numbers of tasks
- **Fully Tested**: 138 tests with 100% success rate
- **Production Ready**: Stable and reliable for production use
- **Auxiliary Methods**: Helper methods for common operations
- **Data Persistence**: Jobs created via API persist correctly

## Quick Start

### Installation

```bash
pip install ppycron
```

### Basic Usage

```python
from ppycron.src import UnixInterface, WindowsInterface
import platform

# Automatically choose the right interface for your platform
if platform.system() == "Windows":
    interface = WindowsInterface()
else:
    interface = UnixInterface()

# Add a scheduled task
cron = interface.add(
    command="echo 'Hello, World!'", 
    interval="*/5 * * * *"  # Every 5 minutes
)

print(f"Created task with ID: {cron.id}")

# Get all tasks
tasks = interface.get_all()
print(f"Total tasks: {len(tasks)}")
```

## API Reference

### Core Methods

All interfaces provide the same methods:

#### `add(command: str, interval: str) -> Cron`
Add a new scheduled task.

```python
# Add a task that runs every hour
cron = interface.add(
    command="python /path/to/script.py",
    interval="0 * * * *"
)

# Add a task that runs daily at 2:30 AM
cron = interface.add(
    command="backup_database.sh",
    interval="30 2 * * *"
)

# Add a task that runs weekly on Sundays
cron = interface.add(
    command="weekly_report.py",
    interval="0 9 * * 0"
)
```

#### `get_all() -> List[Cron]`
Get all scheduled tasks.

```python
tasks = interface.get_all()
for task in tasks:
    print(f"ID: {task.id}")
    print(f"Command: {task.command}")
    print(f"Interval: {task.interval}")
    print("---")
```

#### `get_by_id(cron_id: str) -> Optional[Cron]`
Get a specific task by its ID.

```python
task = interface.get_by_id("my-task-id")
if task:
    print(f"Found task: {task.command}")
else:
    print("Task not found")
```

#### `edit(cron_id: str, **kwargs) -> bool`
Edit an existing task.

```python
# Update the command
success = interface.edit(
    cron_id="my-task-id",
    command="new_command.sh"
)

# Update the interval
success = interface.edit(
    cron_id="my-task-id",
    interval="0 3 * * *"  # Daily at 3 AM
)

# Update both
success = interface.edit(
    cron_id="my-task-id",
    command="updated_command.sh",
    interval="*/10 * * * *"  # Every 10 minutes
)
```

#### `delete(cron_id: str) -> bool`
Delete a scheduled task.

```python
success = interface.delete("my-task-id")
if success:
    print("Task deleted successfully")
```

#### `clear_all() -> bool`
Delete all scheduled tasks.

```python
success = interface.clear_all()
if success:
    print("All tasks cleared")
```

#### `is_valid_cron_format(interval: str) -> bool`
Validate a cron interval format.

```python
# Valid formats
assert interface.is_valid_cron_format("* * * * *")  # Every minute
assert interface.is_valid_cron_format("0 12 * * *")  # Daily at noon
assert interface.is_valid_cron_format("0 0 * * 0")   # Weekly on Sunday

# Invalid formats
assert not interface.is_valid_cron_format("60 * * * *")  # Invalid minute
assert not interface.is_valid_cron_format("* * * *")     # Missing field
```

### Auxiliary Methods

#### `count() -> int`
Get the total number of scheduled tasks.

```python
total_tasks = interface.count()
print(f"You have {total_tasks} scheduled tasks")
```

#### `exists(cron_id: str) -> bool`
Check if a scheduled task exists by ID.

```python
if interface.exists("my-task-id"):
    print("Task exists")
else:
    print("Task not found")
```

#### `get_by_command(command: str) -> List[Cron]`
Get all scheduled tasks with a specific command.

```python
backup_tasks = interface.get_by_command("backup.sh")
print(f"Found {len(backup_tasks)} backup tasks")
```

#### `get_by_interval(interval: str) -> List[Cron]`
Get all scheduled tasks with a specific interval.

```python
daily_tasks = interface.get_by_interval("0 2 * * *")
print(f"Found {len(daily_tasks)} daily tasks at 2 AM")
```

#### `delete_by_command(command: str) -> int`
Delete all scheduled tasks with a specific command. Returns number of deleted tasks.

```python
deleted_count = interface.delete_by_command("old_script.py")
print(f"Deleted {deleted_count} old script tasks")
```

#### `delete_by_interval(interval: str) -> int`
Delete all scheduled tasks with a specific interval. Returns number of deleted tasks.

```python
deleted_count = interface.delete_by_interval("*/5 * * * *")
print(f"Deleted {deleted_count} tasks that ran every 5 minutes")
```

#### `update_command(cron_id: str, new_command: str) -> bool`
Update only the command of a scheduled task.

```python
success = interface.update_command("my-task-id", "new_command.sh")
```

#### `update_interval(cron_id: str, new_interval: str) -> bool`
Update only the interval of a scheduled task.

```python
success = interface.update_interval("my-task-id", "0 3 * * *")
```

#### `duplicate(cron_id: str, new_interval: str = None) -> Optional[Cron]`
Duplicate a scheduled task with optional new interval.

```python
# Duplicate with same interval
duplicated = interface.duplicate("original-task-id")

# Duplicate with new interval
duplicated = interface.duplicate("original-task-id", "0 4 * * *")
```

### Cron Object Methods

#### `to_dict() -> Dict[str, Any]`
Convert Cron object to dictionary.

```python
cron = interface.add("echo test", "* * * * *")
cron_dict = cron.to_dict()
# Returns: {'id': 'uuid', 'command': 'echo test', 'interval': '* * * * *'}
```

#### `from_dict(data: Dict[str, Any]) -> Cron`
Create Cron object from dictionary.

```python
cron_data = {'id': 'my-id', 'command': 'echo test', 'interval': '* * * * *'}
cron = Cron.from_dict(cron_data)
```

## 🖥️ Platform-Specific Features

### Unix/Linux Interface

The Unix interface uses the native `crontab` command and provides:

- **Cron Format Support**: Full support for all cron syntax
- **Temporary File Management**: Safe handling of crontab modifications
- **Error Recovery**: Graceful handling of malformed crontab entries
- **Permission Handling**: Proper error messages for permission issues
- **Robust Validation**: Validates minute (0-59) and hour (0-23) ranges

```python
from ppycron.src import UnixInterface

unix_interface = UnixInterface()

# Add a complex cron job
cron = unix_interface.add(
    command="mysqldump -u root -p database > backup.sql",
    interval="0 2 * * 1-5"  # Weekdays at 2 AM
)

# Validate cron format
is_valid = unix_interface.is_valid_cron_format("0 25 * * *")  # False (hour > 23)
```

### Windows Interface

The Windows interface uses the native `schtasks` command and provides:

- **Automatic Conversion**: Converts cron format to Windows Task Scheduler format
- **XML Parsing**: Extracts task details from Windows XML output
- **Schedule Types**: Supports daily, weekly, monthly, and minute-based schedules
- **Command Wrapping**: Automatically wraps commands in `cmd.exe /c`
- **Cross-Platform Compatibility**: Same cron format as Unix

```python
from ppycron.src import WindowsInterface

windows_interface = WindowsInterface()

# Add a Windows scheduled task
task = windows_interface.add(
    command="C:\\Scripts\\backup.bat",
    interval="0 3 * * *"  # Daily at 3 AM
)

# The interface automatically converts to Windows format
# and creates a task named "Pycron_<id>"

# Get task details
task_details = windows_interface.get_by_id(task.id)
print(f"Command: {task_details.command}")
print(f"Interval: {task_details.interval}")
```

## 📊 Cron Format Reference

### Basic Format
```
minute hour day month weekday
```

### Examples

| Interval | Description |
|----------|-------------|
| `* * * * *` | Every minute |
| `*/15 * * * *` | Every 15 minutes |
| `0 * * * *` | Every hour |
| `0 12 * * *` | Daily at noon |
| `0 0 1 * *` | Monthly on the 1st |
| `0 0 * * 0` | Weekly on Sunday |
| `30 2 * * 1-5` | Weekdays at 2:30 AM |
| `0 9,17 * * 1-5` | Weekdays at 9 AM and 5 PM |

### Field Ranges

| Field | Range | Description |
|-------|-------|-------------|
| minute | 0-59 | Minutes of the hour |
| hour | 0-23 | Hours of the day |
| day | 1-31 | Day of the month |
| month | 1-12 | Month of the year |
| weekday | 0-6 | Day of the week (0=Sunday) |

## 🔧 Advanced Usage

### Error Handling

```python
try:
    cron = interface.add(command="invalid_command", interval="* * * * *")
except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"Runtime error: {e}")
```

### Logging

The library provides comprehensive logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# All operations will be logged
cron = interface.add(command="echo test", interval="* * * * *")
# Output: INFO:ppycron.src.unix:Successfully added cron job with ID: abc123
```

### Batch Operations

```python
# Add multiple tasks
tasks = []
for i in range(5):
    task = interface.add(
        command=f"echo 'Task {i}'",
        interval=f"{i} * * * *"
    )
    tasks.append(task)

# Get all tasks
all_tasks = interface.get_all()
print(f"Total tasks: {len(all_tasks)}")

# Delete specific tasks
for task in tasks[:3]:  # Delete first 3
    interface.delete(task.id)
```

### Cross-Platform Development

```python
import platform
from ppycron.src import UnixInterface, WindowsInterface

def get_interface():
    """Get the appropriate interface for the current platform."""
    if platform.system() == "Windows":
        return WindowsInterface()
    else:
        return UnixInterface()

# Use the same code on any platform
interface = get_interface()
cron = interface.add(command="my_script.py", interval="0 9 * * 1-5")
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_unix.py -v

# Run with coverage
pytest tests/ --cov=ppycron --cov-report=html

# Current test results: 97 tests passing (100% success rate)
```

## Installation from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/ppycron.git
cd ppycron

# Install in development mode
pip install -e .

# Run tests
pytest tests/ -v
```

## Performance & Reliability

- **100% Test Coverage**: All functionality thoroughly tested
- **Robust Error Handling**: Graceful handling of system errors
- **Input Validation**: Comprehensive validation of cron formats
- **Cross-Platform Compatibility**: Tested on Unix, Linux, and Windows
- **Production Ready**: Stable and reliable for production environments

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Ensure all tests pass (97/97)
- Add tests for new features
- Follow the existing code style
- Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Unix cron system for the scheduling format
- Windows Task Scheduler for Windows integration
- Python community for excellent testing tools
- All contributors who helped achieve 100% test success

## Project Status

- ✅ **Core Features**: Complete and tested
- ✅ **Cross-Platform Support**: Unix/Linux and Windows
- ✅ **Test Coverage**: 97 tests passing (100%)
- ✅ **Documentation**: Comprehensive and up-to-date
- ✅ **Production Ready**: Stable and reliable

## Use Cases

PPyCron is designed to handle a wide variety of scheduled task scenarios across different platforms and industries:

### **Data Management & Backup**
- **Database Backups**: Automated daily/weekly database dumps with retention policies
- **File Synchronization**: Regular sync between local and remote storage
- **Archive Management**: Automatic compression and archiving of old data
- **Backup Verification**: Scheduled integrity checks of backup files

### **System Maintenance**
- **Log Rotation**: Automatic cleanup of old log files to prevent disk space issues
- **Cache Cleanup**: Regular clearing of temporary files and application caches
- **System Updates**: Scheduled security updates and package maintenance
- **Disk Space Management**: Automated cleanup of old files and directories

### **Monitoring & Reporting**
- **System Health Checks**: Regular monitoring of CPU, memory, and disk usage
- **Application Monitoring**: Health checks for web services and applications
- **Performance Reports**: Automated generation of system performance reports
- **Alert Systems**: Scheduled checks that trigger notifications for issues

### **Data Processing**
- **ETL Jobs**: Regular data extraction, transformation, and loading processes
- **Report Generation**: Automated creation and distribution of business reports
- **Data Validation**: Scheduled checks for data integrity and consistency
- **Batch Processing**: Regular execution of data processing pipelines

### **Web & Application Services**
- **Website Maintenance**: Regular updates and maintenance tasks for web applications
- **API Health Checks**: Monitoring of external API endpoints and services
- **Content Updates**: Automated content refresh and synchronization
- **Session Cleanup**: Regular cleanup of expired user sessions

### **Security & Compliance**
- **Security Scans**: Regular vulnerability assessments and security checks
- **Certificate Renewal**: Automated SSL certificate monitoring and renewal
- **Access Log Analysis**: Regular analysis of access logs for security threats
- **Compliance Reports**: Automated generation of compliance and audit reports

### **Business Operations**
- **Invoice Generation**: Automated billing and invoice creation
- **Customer Notifications**: Scheduled email campaigns and notifications
- **Inventory Updates**: Regular synchronization of inventory data
- **Analytics Processing**: Scheduled processing of business analytics data

### **Development & DevOps**
- **Build Automation**: Regular code builds and deployment checks
- **Test Execution**: Automated running of test suites and quality checks
- **Dependency Updates**: Regular checking and updating of project dependencies
- **Deployment Tasks**: Automated deployment and rollback procedures

### **Key Benefits for Each Use Case**
- **Cross-Platform**: Same code works on Windows, Linux, and Unix systems
- **Reliable**: Robust error handling and validation for production environments
- **Flexible**: Easy to adapt for different scheduling requirements
- **Maintainable**: Clean API and comprehensive logging for easy debugging
- **Scalable**: Can handle multiple tasks and complex scheduling scenarios

---

*PPyCron - Where Unix meets Windows in perfect harmony* 🕐✨
