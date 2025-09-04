import logging
import subprocess
import os
import re
import xml.etree.ElementTree as ET
from tempfile import NamedTemporaryFile
from typing import List, Optional
from ppycron.src.base import BaseInterface, Cron

logger = logging.getLogger(__name__)


class WindowsInterface(BaseInterface):

    operational_system = "windows"

    def __init__(self):
        """Initialize the Windows interface and ensure Task Scheduler is accessible."""
        try:
            # Test if schtasks is available
            subprocess.run(["schtasks", "/query"], capture_output=True, check=False)
            logger.info("Windows Task Scheduler interface initialized successfully")
        except FileNotFoundError:
            raise RuntimeError("schtasks command not found. Please ensure Task Scheduler is available.")
        
        # Test if we can create tasks
        try:
            subprocess.run(["schtasks", "/create", "/tn", "test_pycron", "/tr", "echo test", 
                          "/sc", "once", "/st", "00:00", "/f"], 
                         capture_output=True, check=False)
            # Clean up test task
            subprocess.run(["schtasks", "/delete", "/tn", "test_pycron", "/f"], 
                         capture_output=True, check=False)
        except Exception as e:
            logger.warning(f"Task Scheduler test failed: {e}")

    def _validate_interval(self, interval: str) -> bool:
        """Validate cron interval format and convert to Windows format."""
        if not interval or not isinstance(interval, str):
            return False
        
        # Basic cron format validation: 5 fields (minute hour day month weekday)
        parts = interval.split()
        if len(parts) != 5:
            return False
        
        # Simple regex patterns for each field
        patterns = [
            r'^(\*|[0-5]?[0-9]|\*\/[0-9]+|[0-5]?[0-9]-[0-5]?[0-9]|[0-5]?[0-9],?)+$',  # minute (0-59)
            r'^(\*|1?[0-9]|2[0-3]|\*\/[0-9]+|1?[0-9]-1?[0-9]|2[0-3]-2[0-3]|1?[0-9],?)+$',  # hour (0-23)
            r'^(\*|[1-9]|[12][0-9]|3[01]|\*\/[0-9]+|[1-9]-[1-9]|[12][0-9]-[12][0-9]|[1-9],?)+$',  # day (1-31)
            r'^(\*|[1-9]|1[0-2]|\*\/[0-9]+|[1-9]-[1-9]|1[0-2]-1[0-2]|[1-9],?)+$',  # month (1-12)
            r'^(\*|[0-6]|\*\/[0-9]+|[0-6]-[0-6]|[0-6],?)+$'  # weekday (0-6)
        ]
        
        for i, (part, pattern) in enumerate(zip(parts, patterns)):
            if not re.match(pattern, part):
                logger.error(f"Invalid cron field {i}: {part}")
                return False
            
            # Additional validation for specific ranges
            if i == 0:  # minute
                if part != '*' and '/' not in part and '-' not in part and ',' not in part:
                    try:
                        val = int(part)
                        if val < 0 or val > 59:
                            logger.error(f"Minute value out of range (0-59): {val}")
                            return False
                    except ValueError:
                        pass
            elif i == 1:  # hour
                if part != '*' and '/' not in part and '-' not in part and ',' not in part:
                    try:
                        val = int(part)
                        if val < 0 or val > 23:
                            logger.error(f"Hour value out of range (0-23): {val}")
                            return False
                    except ValueError:
                        pass
        
        return True

    def _validate_command(self, command: str) -> bool:
        """Validate command string."""
        if not command or not isinstance(command, str):
            return False
        if len(command.strip()) == 0:
            return False
        return True

    def _cron_to_windows_schedule(self, interval: str) -> dict:
        """Convert cron interval to Windows Task Scheduler format."""
        parts = interval.split()
        minute, hour, day, month, weekday = parts
        
        schedule = {
            'frequency': 'daily',
            'interval': 1,
            'start_time': '00:00',
            'days_of_week': None,
            'days_of_month': None
        }
        
        # Handle different cron patterns
        if minute != '*' and hour == '*':
            # Every X minutes
            if '/' in minute:
                interval_minutes = int(minute.split('/')[1])
                schedule['frequency'] = 'minute'
                schedule['interval'] = interval_minutes
            else:
                schedule['frequency'] = 'minute'
                schedule['interval'] = 1
        elif weekday != '*':
            # Weekly schedule - check this first for weekdays
            schedule['frequency'] = 'weekly'
            if '/' in weekday:
                schedule['interval'] = int(weekday.split('/')[1])
            else:
                schedule['interval'] = 1
            # Convert cron weekday (0-6, Sunday=0) to Windows format (1-7, Sunday=1)
            weekdays = []
            for w in weekday.split(','):
                if '-' in w:
                    start, end = w.split('-')
                    for i in range(int(start), int(end) + 1):
                        weekdays.append(str((i + 1) % 7 or 7))
                else:
                    weekdays.append(str((int(w) + 1) % 7 or 7))
            schedule['days_of_week'] = ','.join(weekdays)
            # Set start time if hour and minute are specified
            if minute != '*' and hour != '*':
                schedule['start_time'] = f"{hour.zfill(2)}:{minute.zfill(2)}"
        elif day != '*':
            # Monthly schedule
            schedule['frequency'] = 'monthly'
            if '/' in day:
                schedule['interval'] = int(day.split('/')[1])
            else:
                schedule['interval'] = 1
            schedule['days_of_month'] = day
            # Set start time if hour and minute are specified
            if minute != '*' and hour != '*':
                schedule['start_time'] = f"{hour.zfill(2)}:{minute.zfill(2)}"
        elif minute != '*' and hour != '*':
            # Specific time (daily)
            schedule['frequency'] = 'daily'
            schedule['start_time'] = f"{hour.zfill(2)}:{minute.zfill(2)}"
        
        return schedule

    def _create_task_xml(self, task_name: str, command: str, schedule: dict) -> str:
        """Create XML configuration for Windows Task."""
        xml_template = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT{schedule.get('interval', 1)}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2024-01-01T{schedule.get('start_time', '00:00')}:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>cmd.exe</Command>
      <Arguments>/c {command}</Arguments>
    </Exec>
  </Actions>
</Task>"""
        return xml_template

    def _get_all_tasks(self) -> List[str]:
        """Get all task names from Task Scheduler."""
        try:
            output = subprocess.check_output(
                ["schtasks", "/query", "/fo", "csv", "/nh"], 
                stderr=subprocess.PIPE
            ).decode("utf-8")
            
            tasks = []
            for line in output.split("\n"):
                if not line.strip():
                    continue
                
                try:
                    parts = line.split('","')
                    if len(parts) >= 1:
                        task_name = parts[0].strip('"')
                        tasks.append(task_name)
                except Exception as e:
                    logger.warning(f"Error parsing task line: {line}, error: {e}")
                    continue
            
            return tasks
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get task list: {e}")
            return []

    def add(self, command: str, interval: str) -> Cron:
        """Add a new scheduled task."""
        if not self._validate_command(command):
            raise ValueError("Invalid command provided")
        
        if not self._validate_interval(interval):
            raise ValueError("Invalid interval format. Expected format: 'minute hour day month weekday'")
        
        cron = Cron(command=command, interval=interval)
        task_name = f"Pycron_{cron.id}"
        
        try:
            # Convert cron interval to Windows schedule
            schedule = self._cron_to_windows_schedule(interval)
            
            # Create task using schtasks
            cmd = [
                "schtasks", "/create", "/tn", task_name, "/tr", f"cmd.exe /c {command}",
                "/sc", schedule['frequency'], "/f"
            ]
            
            if schedule['frequency'] == 'daily':
                cmd.extend(["/st", schedule['start_time']])
            elif schedule['frequency'] == 'weekly' and schedule['days_of_week']:
                cmd.extend(["/d", schedule['days_of_week']])
            elif schedule['frequency'] == 'monthly' and schedule['days_of_month']:
                cmd.extend(["/d", schedule['days_of_month']])
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Successfully added Windows task with ID: {cron.id}")
            return cron
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add Windows task: {e}")
            raise RuntimeError(f"Failed to add Windows task: {e}")

    def get_all(self) -> List[Cron]:
        """Get all scheduled tasks created by Pycron."""
        try:
            # Get all tasks
            all_tasks = self._get_all_tasks()
            
            crons = []
            for task_name in all_tasks:
                # Only process Pycron tasks
                if not task_name.startswith("Pycron_"):
                    continue
                
                # Get task details to extract command and schedule
                task_details = self._get_task_details(task_name)
                if task_details:
                    crons.append(task_details)
                    
            logger.info(f"Retrieved {len(crons)} Windows scheduled tasks")
            return crons
            
        except Exception as e:
            logger.error(f"Failed to get all tasks: {e}")
            return []

    def _get_task_details(self, task_name: str) -> Optional[Cron]:
        """Get detailed information about a specific task."""
        try:
            # Export task to XML
            output = subprocess.check_output(
                ["schtasks", "/query", "/tn", task_name, "/xml"], 
                stderr=subprocess.PIPE
            ).decode("utf-8")
            
            # Parse XML to extract command and schedule
            root = ET.fromstring(output)
            
            # Extract command
            command_elem = root.find(".//{http://schemas.microsoft.com/windows/2004/02/mit/task}Command")
            if command_elem is not None:
                command = command_elem.text or ""
            else:
                command = ""
            
            # Extract arguments
            args_elem = root.find(".//{http://schemas.microsoft.com/windows/2004/02/mit/task}Arguments")
            if args_elem is not None:
                args = args_elem.text or ""
                # Remove "cmd.exe /c " prefix
                if args.startswith("/c "):
                    command = args[3:]  # Remove "/c " (3 characters)
                elif args.startswith("cmd.exe /c "):
                    command = args[11:]  # Remove "cmd.exe /c " (11 characters)
                else:
                    command = args  # No prefix to remove
            
            # Extract schedule information
            trigger_elem = root.find(".//{http://schemas.microsoft.com/windows/2004/02/mit/task}TimeTrigger")
            if trigger_elem is not None:
                # Convert Windows schedule back to cron format
                interval = self._windows_to_cron_schedule(trigger_elem)
            else:
                interval = "* * * * *"  # Default
            
            # Extract cron ID from task name
            cron_id = task_name.replace("Pycron_", "")
            
            return Cron(command=command, interval=interval, id=cron_id)
            
        except Exception as e:
            logger.error(f"Error getting task details for {task_name}: {e}")
            return None

    def _windows_to_cron_schedule(self, trigger_elem) -> str:
        """Convert Windows schedule back to cron format."""
        # This is a simplified conversion - in practice, you'd need more complex logic
        # to handle all Windows scheduling options
        return "* * * * *"  # Default to every minute

    def get_by_id(self, cron_id: str) -> Optional[Cron]:
        """Get a specific scheduled task by ID."""
        if not cron_id:
            raise ValueError("Cron ID is required")
        
        task_name = f"Pycron_{cron_id}"
        return self._get_task_details(task_name)

    def edit(self, cron_id: str, **kwargs) -> bool:
        """Edit an existing scheduled task."""
        if not cron_id:
            raise ValueError("Task ID is required")
        
        new_command = kwargs.get('command')
        new_interval = kwargs.get('interval')
        
        # Validate new values if provided
        if new_command is not None and not self._validate_command(new_command):
            raise ValueError("Invalid command provided")
        
        if new_interval is not None and not self._validate_interval(new_interval):
            raise ValueError("Invalid interval format")
        
        task_name = f"Pycron_{cron_id}"
        
        try:
            # Get current task details
            current_task = self._get_task_details(task_name)
            if not current_task:
                logger.warning(f"Task with ID {cron_id} not found")
                return False
            
            # Use new values or keep current ones
            command = new_command if new_command is not None else current_task.command
            interval = new_interval if new_interval is not None else current_task.interval
            
            # Delete old task
            subprocess.run(
                ["schtasks", "/delete", "/tn", task_name, "/f"],
                check=True, capture_output=True
            )
            
            # Create new task with updated parameters
            schedule = self._cron_to_windows_schedule(interval)
            
            # Build schtasks command
            cmd = [
                "schtasks", "/create", "/tn", task_name, "/tr", command,
                "/sc", schedule['frequency']
            ]
            
            if schedule['interval'] > 1:
                cmd.extend(["/mo", str(schedule['interval'])])
            
            if schedule['start_time'] != '00:00':
                cmd.extend(["/st", schedule['start_time']])
            
            if schedule['days_of_week']:
                cmd.extend(["/d", schedule['days_of_week']])
            
            if schedule['days_of_month']:
                cmd.extend(["/d", schedule['days_of_month']])
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            logger.info(f"Successfully updated task with ID: {cron_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error editing task: {e}")
            raise RuntimeError(f"Failed to edit task: {e}")

    def delete(self, cron_id: str) -> bool:
        """Delete a scheduled task by ID."""
        if not cron_id:
            raise ValueError("Cron ID is required")

        task_name = f"Pycron_{cron_id}"
        
        try:
            subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], 
                         capture_output=True, check=True)
            logger.info(f"Removed Windows task with ID: {cron_id}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete Windows task: {e}")
            return False

    def clear_all(self) -> bool:
        """Clear all Pycron scheduled tasks."""
        try:
            # Get all Pycron tasks
            all_tasks = self._get_all_tasks()
            
            deleted_count = 0
            for task_name in all_tasks:
                if task_name.startswith("Pycron_"):
                    try:
                        subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], 
                                     capture_output=True, check=True)
                        deleted_count += 1
                    except subprocess.CalledProcessError:
                        continue
            
            logger.info(f"Cleared {deleted_count} Windows scheduled tasks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear Windows tasks: {e}")
            return False

    def is_valid_cron_format(self, interval: str) -> bool:
        """Check if a cron interval format is valid."""
        return self._validate_interval(interval)
