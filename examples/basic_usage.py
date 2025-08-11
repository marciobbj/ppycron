#!/usr/bin/env python3
"""
Basic usage examples for PPyCron library.

This example demonstrates how to use PPyCron to manage scheduled tasks
on both Linux (cron) and Windows (Task Scheduler) systems.
"""

import platform
import logging
from ppycron.src import UnixInterface, WindowsInterface, Cron

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_interface():
    """Get the appropriate interface based on the operating system."""
    system = platform.system().lower()
    
    if system == "windows":
        logger.info("Detected Windows system, using Windows Task Scheduler interface")
        return WindowsInterface()
    else:
        logger.info("Detected Unix/Linux system, using crontab interface")
        return UnixInterface()


def example_basic_operations():
    """Demonstrate basic CRUD operations."""
    logger.info("=== Basic Operations Example ===")
    
    try:
        interface = get_interface()
        
        # 1. Add a new scheduled task
        logger.info("Adding a new scheduled task...")
        cron = interface.add(
            command="echo 'Hello from PPyCron!'",
            interval="*/5 * * * *"  # Every 5 minutes
        )
        logger.info(f"Created task with ID: {cron.id}")
        
        # 2. List all tasks
        logger.info("Listing all scheduled tasks...")
        tasks = interface.get_all()
        logger.info(f"Found {len(tasks)} task(s):")
        for task in tasks:
            logger.info(f"  - ID: {task.id}, Command: {task.command}, Interval: {task.interval}")
        
        # 3. Get a specific task by ID
        logger.info(f"Getting task with ID: {cron.id}")
        retrieved_task = interface.get_by_id(cron.id)
        if retrieved_task:
            logger.info(f"Retrieved task: {retrieved_task.command}")
        else:
            logger.warning("Task not found")
        
        # 4. Edit the task
        logger.info("Editing the task...")
        success = interface.edit(
            cron_id=cron.id,
            command="echo 'Updated command from PPyCron!'",
            interval="*/10 * * * *"  # Every 10 minutes
        )
        if success:
            logger.info("Task updated successfully")
        else:
            logger.error("Failed to update task")
        
        # 5. List tasks again to see the changes
        logger.info("Listing tasks after update...")
        tasks = interface.get_all()
        for task in tasks:
            logger.info(f"  - ID: {task.id}, Command: {task.command}, Interval: {task.interval}")
        
        # 6. Delete the task
        logger.info("Deleting the task...")
        success = interface.delete(cron_id=cron.id)
        if success:
            logger.info("Task deleted successfully")
        else:
            logger.error("Failed to delete task")
        
        # 7. Verify deletion
        logger.info("Verifying deletion...")
        tasks = interface.get_all()
        logger.info(f"Remaining tasks: {len(tasks)}")
        
    except Exception as e:
        logger.error(f"Error in basic operations: {e}")


def example_multiple_tasks():
    """Demonstrate managing multiple tasks."""
    logger.info("=== Multiple Tasks Example ===")
    
    try:
        interface = get_interface()
        
        # Create multiple tasks with different schedules
        tasks = [
            ("echo 'Daily backup'", "0 2 * * *"),      # Daily at 2 AM
            ("echo 'Weekly cleanup'", "0 3 * * 0"),    # Weekly on Sunday at 3 AM
            ("echo 'Monthly report'", "0 4 1 * *"),    # Monthly on 1st at 4 AM
            ("echo 'Hourly check'", "0 * * * *"),      # Every hour
        ]
        
        created_tasks = []
        
        # Add all tasks
        for command, interval in tasks:
            logger.info(f"Adding task: {command}")
            cron = interface.add(command=command, interval=interval)
            created_tasks.append(cron)
            logger.info(f"  Created with ID: {cron.id}")
        
        # List all tasks
        logger.info("All scheduled tasks:")
        all_tasks = interface.get_all()
        for task in all_tasks:
            logger.info(f"  - {task.interval} {task.command} (ID: {task.id})")
        
        # Clear all tasks
        logger.info("Clearing all tasks...")
        success = interface.clear_all()
        if success:
            logger.info("All tasks cleared successfully")
        else:
            logger.error("Failed to clear all tasks")
        
        # Verify all tasks are gone
        remaining_tasks = interface.get_all()
        logger.info(f"Remaining tasks: {len(remaining_tasks)}")
        
    except Exception as e:
        logger.error(f"Error in multiple tasks example: {e}")


def example_validation():
    """Demonstrate input validation."""
    logger.info("=== Validation Example ===")
    
    try:
        interface = get_interface()
        
        # Test valid cron formats
        valid_intervals = [
            "* * * * *",      # Every minute
            "*/15 * * * *",   # Every 15 minutes
            "0 12 * * *",     # Daily at noon
            "0 0 1 * *",      # Monthly on 1st
            "0 0 * * 0",      # Weekly on Sunday
            "30 2 * * 1-5",   # Weekdays at 2:30 AM
        ]
        
        logger.info("Testing valid cron formats:")
        for interval in valid_intervals:
            is_valid = interface.is_valid_cron_format(interval)
            logger.info(f"  {interval}: {'✓' if is_valid else '✗'}")
        
        # Test invalid cron formats
        invalid_intervals = [
            "",               # Empty
            "invalid",        # Invalid format
            "* * * *",        # Missing field
            "* * * * * *",    # Too many fields
            "60 * * * *",     # Invalid minute
        ]
        
        logger.info("Testing invalid cron formats:")
        for interval in invalid_intervals:
            is_valid = interface.is_valid_cron_format(interval)
            logger.info(f"  {interval}: {'✓' if is_valid else '✗'}")
        
    except Exception as e:
        logger.error(f"Error in validation example: {e}")


def example_error_handling():
    """Demonstrate error handling."""
    logger.info("=== Error Handling Example ===")
    
    try:
        interface = get_interface()
        
        # Try to add task with invalid command
        logger.info("Testing invalid command...")
        try:
            interface.add(command="", interval="* * * * *")
        except ValueError as e:
            logger.info(f"Caught expected error: {e}")
        
        # Try to add task with invalid interval
        logger.info("Testing invalid interval...")
        try:
            interface.add(command="echo test", interval="invalid")
        except ValueError as e:
            logger.info(f"Caught expected error: {e}")
        
        # Try to get non-existent task
        logger.info("Testing non-existent task...")
        task = interface.get_by_id("non-existent-id")
        if task is None:
            logger.info("Correctly returned None for non-existent task")
        
        # Try to edit non-existent task
        logger.info("Testing edit non-existent task...")
        success = interface.edit(cron_id="non-existent-id", command="echo test")
        if not success:
            logger.info("Correctly failed to edit non-existent task")
        
    except Exception as e:
        logger.error(f"Error in error handling example: {e}")


def main():
    """Run all examples."""
    logger.info("Starting PPyCron examples...")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    
    # Run examples
    example_basic_operations()
    print()
    
    example_multiple_tasks()
    print()
    
    example_validation()
    print()
    
    example_error_handling()
    print()
    
    logger.info("Examples completed!")


if __name__ == "__main__":
    main()
