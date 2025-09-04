#!/usr/bin/env python3
"""
Scheduled Task Service Example using PPyCron
A general-purpose service template for creating scheduled tasks with PPyCron

This example demonstrates how to:
- Create a configurable scheduled task service
- Manage task scheduling with PPyCron
- Handle different types of tasks (backup, cleanup, monitoring, etc.)
- Provide a command-line interface for task management
- Implement proper logging and error handling
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduled_task_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ScheduledTaskService:
    """
    A general-purpose scheduled task service using PPyCron.
    
    This class provides a framework for creating and managing scheduled tasks
    that can be easily adapted for different use cases like:
    - Database backups
    - File cleanup
    - System monitoring
    - Data synchronization
    - Report generation
    """
    
    def __init__(self, config_file: str = "task_service_config.json"):
        self.config_file = config_file
        self.project_dir = Path(__file__).parent.absolute()
        self.config = self.load_config()
        self.interface = self._get_interface()
        
    def _get_interface(self):
        """Get the appropriate PPyCron interface for the current platform"""
        try:
            from ppycron.src import UnixInterface, WindowsInterface
            
            if platform.system() == "Windows":
                return WindowsInterface()
            else:
                return UnixInterface()
        except ImportError:
            logger.error("PPyCron not found. Install with: pip install ppycron")
            return None
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        default_config = {
            "task_name": "scheduled_task",
            "cron_schedule": "0 0 * * *",  # Daily at midnight
            "max_retention": 30,
            "enabled": True,
            "task_type": "backup",  # backup, cleanup, monitor, custom
            "task_config": {
                "source_path": "data/",
                "backup_path": "backups/",
                "file_pattern": "*",
                "exclude_patterns": ["*.tmp", "*.log"]
            },
            "logging": {
                "level": "INFO",
                "file": "task_service.log"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with default configuration
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                return default_config
        else:
            # Create default configuration file
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def execute_task(self) -> bool:
        """
        Execute the scheduled task based on its type.
        
        This method can be customized for different task types:
        - backup: Create backups of files/databases
        - cleanup: Remove old files/logs
        - monitor: Check system status
        - custom: Execute custom scripts
        """
        task_type = self.config.get("task_type", "backup")
        
        try:
            if task_type == "backup":
                return self._execute_backup_task()
            elif task_type == "cleanup":
                return self._execute_cleanup_task()
            elif task_type == "monitor":
                return self._execute_monitor_task()
            elif task_type == "custom":
                return self._execute_custom_task()
            else:
                logger.error(f"Unknown task type: {task_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return False
    
    def _execute_backup_task(self) -> bool:
        """Execute a backup task"""
        try:
            import shutil
            
            task_config = self.config.get("task_config", {})
            source_path = Path(task_config.get("source_path", "data/"))
            backup_path = Path(task_config.get("backup_path", "backups/"))
            
            # Create backup directory if it doesn't exist
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}"
            
            if source_path.is_file():
                # Single file backup
                backup_file = backup_path / f"{backup_filename}{source_path.suffix}"
                shutil.copy2(source_path, backup_file)
                logger.info(f"File backup created: {backup_file}")
            elif source_path.is_dir():
                # Directory backup
                backup_dir = backup_path / backup_filename
                shutil.copytree(source_path, backup_dir)
                logger.info(f"Directory backup created: {backup_dir}")
            else:
                logger.error(f"Source path does not exist: {source_path}")
                return False
            
            # Cleanup old backups
            self._cleanup_old_backups()
            return True
            
        except Exception as e:
            logger.error(f"Error in backup task: {e}")
            return False
    
    def _execute_cleanup_task(self) -> bool:
        """Execute a cleanup task"""
        try:
            import glob
            
            task_config = self.config.get("task_config", {})
            cleanup_path = Path(task_config.get("source_path", "logs/"))
            file_pattern = task_config.get("file_pattern", "*.log")
            max_age_days = task_config.get("max_age_days", 7)
            
            if not cleanup_path.exists():
                logger.warning(f"Cleanup path does not exist: {cleanup_path}")
                return True
            
            # Find files matching pattern
            pattern = cleanup_path / file_pattern
            files_to_clean = glob.glob(str(pattern))
            
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            cleaned_count = 0
            
            for file_path in files_to_clean:
                file_stat = os.stat(file_path)
                if file_stat.st_mtime < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"Cleaned old file: {file_path}")
            
            logger.info(f"Cleanup completed: {cleaned_count} files removed")
            return True
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            return False
    
    def _execute_monitor_task(self) -> bool:
        """Execute a monitoring task"""
        try:
            import psutil
            
            # Basic system monitoring
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            logger.info(f"System Monitor - CPU: {cpu_percent}%, "
                       f"Memory: {memory.percent}%, "
                       f"Disk: {disk.percent}%")
            
            # Check for high resource usage
            if cpu_percent > 80:
                logger.warning(f"High CPU usage detected: {cpu_percent}%")
            
            if memory.percent > 80:
                logger.warning(f"High memory usage detected: {memory.percent}%")
            
            if disk.percent > 90:
                logger.warning(f"High disk usage detected: {disk.percent}%")
            
            return True
            
        except ImportError:
            logger.warning("psutil not available for monitoring")
            return True
        except Exception as e:
            logger.error(f"Error in monitor task: {e}")
            return False
    
    def _execute_custom_task(self) -> bool:
        """Execute a custom task"""
        try:
            task_config = self.config.get("task_config", {})
            script_path = task_config.get("script_path")
            
            if not script_path:
                logger.error("No script path specified for custom task")
                return False
            
            # Execute custom script
            result = os.system(script_path)
            
            if result == 0:
                logger.info(f"Custom script executed successfully: {script_path}")
                return True
            else:
                logger.error(f"Custom script failed with exit code {result}: {script_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error in custom task: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Remove old backups keeping only the most recent ones"""
        try:
            task_config = self.config.get("task_config", {})
            backup_path = Path(task_config.get("backup_path", "backups/"))
            max_retention = self.config.get("max_retention", 30)
            
            if not backup_path.exists():
                return
            
            # List backup files/directories
            backup_items = []
            for item in backup_path.iterdir():
                if item.name.startswith("backup_"):
                    backup_items.append(item)
            
            backup_items.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            if len(backup_items) > max_retention:
                for old_item in backup_items[max_retention:]:
                    if old_item.is_file():
                        old_item.unlink()
                    else:
                        import shutil
                        shutil.rmtree(old_item)
                    logger.info(f"Removed old backup: {old_item}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def add_scheduled_task(self) -> bool:
        """Add the scheduled task using PPyCron"""
        if not self.interface:
            return False
            
        try:
            # Command to execute the task
            script_path = str(self.project_dir / "scheduled_task_service.py")
            command = f"cd {self.project_dir} && python3 {script_path} --execute"
            
            # Check if task already exists
            existing_tasks = self.interface.get_all()
            for task in existing_tasks:
                if self.config["task_name"] in task.command:
                    logger.info("Scheduled task already exists")
                    return True
            
            # Add new task
            cron_task = self.interface.add(
                command=command,
                interval=self.config["cron_schedule"]
            )
            
            logger.info(f"Scheduled task added: {self.config['cron_schedule']}")
            logger.info(f"Task ID: {cron_task.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding scheduled task: {e}")
            return False
    
    def remove_scheduled_task(self) -> bool:
        """Remove the scheduled task"""
        if not self.interface:
            return False
            
        try:
            # Find and remove the task
            existing_tasks = self.interface.get_all()
            for task in existing_tasks:
                if self.config["task_name"] in task.command:
                    self.interface.delete(task.id)
                    logger.info("Scheduled task removed")
                    return True
            
            logger.info("No scheduled task found to remove")
            return True
            
        except Exception as e:
            logger.error(f"Error removing scheduled task: {e}")
            return False
    
    def list_scheduled_tasks(self):
        """List all active scheduled tasks"""
        if not self.interface:
            return
            
        try:
            tasks = self.interface.get_all()
            
            if not tasks:
                logger.info("No scheduled tasks found")
                return
            
            logger.info("Active scheduled tasks:")
            for task in tasks:
                logger.info(f"  - ID: {task.id}")
                logger.info(f"    Schedule: {task.interval}")
                logger.info(f"    Command: {task.command}")
                logger.info("")
                
        except Exception as e:
            logger.error(f"Error listing scheduled tasks: {e}")
    
    def edit_schedule(self, new_schedule: str) -> bool:
        """Edit the task schedule"""
        if not self.interface:
            return False
            
        try:
            # Validate cron format
            if not self.interface.is_valid_cron_format(new_schedule):
                logger.error("Invalid cron format")
                return False
            
            # Remove old task
            self.remove_scheduled_task()
            
            # Update configuration
            self.config["cron_schedule"] = new_schedule
            self.save_config(self.config)
            
            # Add task with new schedule
            self.add_scheduled_task()
            
            logger.info(f"Schedule updated to: {new_schedule}")
            return True
                
        except Exception as e:
            logger.error(f"Error editing schedule: {e}")
            return False
    
    def show_status(self):
        """Show current system status"""
        logger.info("=== Scheduled Task Service Status ===")
        logger.info(f"Configuration: {self.config_file}")
        logger.info(f"Task Type: {self.config.get('task_type', 'backup')}")
        logger.info(f"Schedule: {self.config['cron_schedule']}")
        logger.info(f"Enabled: {self.config.get('enabled', True)}")
        
        # Check if scheduled task exists
        if self.interface:
            try:
                existing_tasks = self.interface.get_all()
                task_exists = any(self.config["task_name"] in task.command for task in existing_tasks)
                logger.info(f"Scheduled Task Active: {'Yes' if task_exists else 'No'}")
            except:
                logger.info("Scheduled Task Active: Unable to check")
        else:
            logger.info("Scheduled Task Active: PPyCron not available")
        
        # Show next execution time
        logger.info(f"Next execution: Based on cron schedule {self.config['cron_schedule']}")

def main():
    parser = argparse.ArgumentParser(
        description="Scheduled Task Service using PPyCron",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a scheduled task
  python scheduled_task_service.py --add
  
  # Execute task manually
  python scheduled_task_service.py --execute
  
  # Remove scheduled task
  python scheduled_task_service.py --remove
  
  # List all scheduled tasks
  python scheduled_task_service.py --list-tasks
  
  # Show status
  python scheduled_task_service.py --status
  
  # Edit schedule (daily at 2 AM)
  python scheduled_task_service.py --edit-schedule "0 2 * * *"
  
  # Use custom config file
  python scheduled_task_service.py --config my_config.json --add
        """
    )
    
    parser.add_argument("--add", action="store_true", 
                       help="Add scheduled task")
    parser.add_argument("--remove", action="store_true", 
                       help="Remove scheduled task")
    parser.add_argument("--execute", action="store_true", 
                       help="Execute task manually")
    parser.add_argument("--list-tasks", action="store_true", 
                       help="List all scheduled tasks")
    parser.add_argument("--status", action="store_true", 
                       help="Show service status")
    parser.add_argument("--edit-schedule", 
                       help="Edit task schedule (cron format)")
    parser.add_argument("--config", 
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize service
    config_file = args.config or "task_service_config.json"
    service = ScheduledTaskService(config_file)
    
    if args.add:
        service.add_scheduled_task()
    elif args.remove:
        service.remove_scheduled_task()
    elif args.execute:
        service.execute_task()
    elif args.list_tasks:
        service.list_scheduled_tasks()
    elif args.status:
        service.show_status()
    elif args.edit_schedule:
        service.edit_schedule(args.edit_schedule)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
