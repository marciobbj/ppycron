# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-09-04

### Major Improvements

#### Fixed Issues
- **Inconsistency between `add()` and `get_all()`**: Fixed the problem where jobs created via `add()` were not appearing in `get_all()`
- **Crontab being cleared automatically**: Removed code that was clearing the crontab during initialization, causing loss of existing jobs
- **API inconsistency**: Standardized return types and improved error handling

#### New Features
- **Auxiliary Methods**: Added 9 new helper methods for common operations:
  - `count()` - Get total number of scheduled tasks
  - `exists(cron_id)` - Check if a task exists by ID
  - `get_by_command(command)` - Find tasks by command
  - `get_by_interval(interval)` - Find tasks by interval
  - `delete_by_command(command)` - Delete tasks by command
  - `delete_by_interval(interval)` - Delete tasks by interval
  - `update_command(cron_id, new_command)` - Update only command
  - `update_interval(cron_id, new_interval)` - Update only interval
  - `duplicate(cron_id, new_interval)` - Duplicate a task

#### Enhanced Cron Object
- **New Methods**:
  - `to_dict()` - Convert Cron object to dictionary
  - `from_dict(data)` - Create Cron object from dictionary
- **Improved string representation**

#### Better Error Handling
- **Robust validation**: Enhanced input validation for commands and intervals
- **Graceful error recovery**: Better handling of malformed crontab entries
- **Comprehensive logging**: Improved logging for debugging and monitoring

#### Testing Improvements
- **Increased test coverage**: From 97 to 138 tests (41 new tests)
- **New test categories**:
  - Auxiliary methods testing
  - Consistency and persistence testing
  - Cron object methods testing
- **100% test success rate**: All 138 tests passing

### Technical Improvements

#### UnixInterface
- **Persistent storage**: Jobs created via API now persist correctly in crontab
- **ID management**: Automatic ID generation for existing jobs without IDs
- **Better file handling**: Improved temporary file management
- **Enhanced parsing**: Better handling of existing crontab entries

#### WindowsInterface
- **Improved XML parsing**: Better handling of Windows Task Scheduler XML
- **Consistent error handling**: Unified error handling across all operations
- **Better task management**: Enhanced task creation, editing, and deletion

### Documentation Updates
- **Updated README**: Added comprehensive documentation for new auxiliary methods
- **Enhanced examples**: Updated examples to demonstrate new features
- **Better API reference**: Improved documentation with practical examples

### Benefits
- **Consistency**: `add()` and `get_all()` now work in perfect harmony
- **Persistência**: Jobs created via API persist correctly across operations
- **Robustez**: Better error handling and validation
- **Usabilidade**: More intuitive API with helper methods
- **Flexibilidade**: Auxiliary methods for common use cases

### Build Information
- **Version**: 1.1.0
- **Python compatibility**: 3.7+
- **Platforms**: Unix/Linux, Windows
- **Dependencies**: No new dependencies added

---

## [1.0.0] - 2024-09-04

### 🎉 Initial Release
- Cross-platform cron management library
- Support for Unix/Linux (crontab) and Windows (Task Scheduler)
- Basic CRUD operations for scheduled tasks
- Cron format validation
- Comprehensive logging
- 97 tests with 100% success rate
