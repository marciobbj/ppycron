import logging
import subprocess
import os
import re
from tempfile import NamedTemporaryFile
from typing import List, Union, Optional
from ppycron.src.base import BaseInterface, Cron

logger = logging.getLogger(__name__)


class UnixInterface(BaseInterface):

    operational_system = "linux"

    def __init__(self):
        """Initialize the Unix interface and ensure crontab is accessible."""
        try:
            # Test if crontab is available
            subprocess.run(["crontab", "-l"], capture_output=True, check=False)
            logger.info("Unix crontab interface initialized successfully")
        except FileNotFoundError:
            raise RuntimeError("crontab command not found. Please ensure cron is installed.")
        
        # Initialize with empty crontab if needed
        try:
            with NamedTemporaryFile("w", delete=False) as f:
                f.write("# Created automatically by Pycron =)\n")
                f.flush()
                subprocess.run(["crontab", f.name], check=True, capture_output=True)
                os.unlink(f.name)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to initialize crontab: {e}")

    def _validate_interval(self, interval: str) -> bool:
        """Validate cron interval format."""
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

    def add(self, command: str, interval: str) -> Cron:
        """Add a new cron job."""
        if not self._validate_command(command):
            raise ValueError("Invalid command provided")
        
        if not self._validate_interval(interval):
            raise ValueError("Invalid interval format. Expected format: 'minute hour day month weekday'")
        
        cron = Cron(command=command, interval=interval)
        
        try:
            # Get current crontab
            try:
                current = subprocess.check_output(["crontab", "-l"], 
                                                stderr=subprocess.PIPE).decode("utf-8")
            except subprocess.CalledProcessError:
                current = ""  # If no crontab exists, start with an empty string

            # Add new cron job
            current += str(cron) + "\n"

            # Write back to crontab
            with NamedTemporaryFile("w", delete=False) as f:
                f.write(current)
                f.flush()
                subprocess.run(["crontab", f.name], check=True, capture_output=True)
                os.unlink(f.name)

            logger.info(f"Successfully added cron job with ID: {cron.id}")
            return cron
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add cron job: {e}")
            raise RuntimeError(f"Failed to add cron job: {e}")

    def get_all(self) -> List[Cron]:
        """Get all cron jobs."""
        try:
            output = subprocess.check_output(["crontab", "-l"], 
                                           stderr=subprocess.PIPE).decode("utf-8")
        except subprocess.CalledProcessError:
            logger.info("No crontab found, returning empty list")
            return []

        crons = []
        for line_num, line in enumerate(output.split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                cron_id = ""
                # Check if line contains identifier in format "# id: <uuid>"
                if "# id:" in line:
                    cron_line, id_comment = line.split("# id:", 1)
                    cron_id = id_comment.strip()
                else:
                    cron_line = line

                # Split cron part to get interval and command
                splitted = cron_line.strip().split()
                if len(splitted) < 6:
                    logger.warning(f"Skipping malformed cron line {line_num}: {line}")
                    continue

                interval = " ".join(splitted[:5])
                command = " ".join(splitted[5:]).strip()

                # Validate the parsed cron entry
                if not self._validate_interval(interval):
                    logger.warning(f"Skipping invalid interval in line {line_num}: {interval}")
                    continue

                if not self._validate_command(command):
                    logger.warning(f"Skipping invalid command in line {line_num}: {command}")
                    continue

                crons.append(Cron(command=command, interval=interval, id=cron_id))
                
            except Exception as e:
                logger.error(f"Error parsing cron line {line_num}: {line}, error: {e}")
                continue

        logger.info(f"Retrieved {len(crons)} cron jobs")
        return crons

    def get_by_id(self, cron_id: str) -> Optional[Cron]:
        """Get a specific cron job by ID."""
        if not cron_id:
            raise ValueError("Cron ID is required")
        
        crons = self.get_all()
        for cron in crons:
            if cron.id == cron_id:
                return cron
        return None

    def edit(self, cron_id: str, **kwargs) -> bool:
        """Edit an existing cron job."""
        if not cron_id:
            raise ValueError("Cron ID is required")
        
        new_command = kwargs.get('command')
        new_interval = kwargs.get('interval')
        
        # Validate new values if provided
        if new_command is not None and not self._validate_command(new_command):
            raise ValueError("Invalid command provided")
        
        if new_interval is not None and not self._validate_interval(new_interval):
            raise ValueError("Invalid interval format")
        
        try:
            # Get current crontab
            current_crontab = subprocess.check_output(
                ["crontab", "-l"], 
                stderr=subprocess.PIPE
            ).decode("utf-8")
            
            lines = current_crontab.strip().split('\n') if current_crontab.strip() else []
            updated_lines = []
            found = False
            
            for line in lines:
                if f"# id: {cron_id}" in line:
                    found = True
                    # Parse existing line
                    parts = line.split('# id:')[0].strip().split(' ', 5)
                    if len(parts) >= 6:
                        interval = ' '.join(parts[:5])
                        command = parts[5]
                        
                        # Update with new values
                        if new_interval is not None:
                            interval = new_interval
                        if new_command is not None:
                            command = new_command
                        
                        updated_line = f"{interval} {command} # id: {cron_id}"
                        updated_lines.append(updated_line)
                        logger.info(f"Updated cron job with ID: {cron_id}")
                    else:
                        # Keep original line if parsing fails
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            if not found:
                logger.warning(f"Cron job with ID {cron_id} not found")
                return False
            
            # Write updated crontab
            with NamedTemporaryFile(mode='w', delete=False) as f:
                f.write('\n'.join(updated_lines) + '\n')
                temp_file = f.name
            
            subprocess.run(["crontab", temp_file], check=True, capture_output=True)
            os.unlink(temp_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Error editing cron job: {e}")
            raise RuntimeError(f"Failed to edit cron job: {e}")

    def delete(self, cron_id: str) -> bool:
        """Delete a cron job by ID."""
        if not cron_id:
            raise ValueError("Cron ID is required")

        try:
            output = subprocess.check_output(["crontab", "-l"], 
                                           stderr=subprocess.PIPE).decode("utf-8")
        except subprocess.CalledProcessError:
            logger.error("Failed to read crontab")
            return False

        lines = []
        removed = False

        for line in output.split("\n"):
            # Keep lines that don't contain the identifier
            if f"id: {cron_id}" in line:
                removed = True
                logger.info(f"Removing cron job with ID: {cron_id}")
                continue
            lines.append(line)

        if removed:
            try:
                current = "\n".join(lines) + "\n"
                with NamedTemporaryFile("w", delete=False) as f:
                    f.write(current)
                    f.flush()
                    subprocess.run(["crontab", f.name], check=True, capture_output=True)
                    os.unlink(f.name)
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to update crontab: {e}")
                return False

        logger.warning(f"No cron job found with ID: {cron_id}")
        return False

    def clear_all(self) -> bool:
        """Clear all cron jobs."""
        try:
            with NamedTemporaryFile("w", delete=False) as f:
                f.write("# Cleared by Pycron\n")
                f.flush()
                subprocess.run(["crontab", f.name], check=True, capture_output=True)
                os.unlink(f.name)
            logger.info("All cron jobs cleared successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clear crontab: {e}")
            return False

    def is_valid_cron_format(self, interval: str) -> bool:
        """Check if a cron interval format is valid."""
        return self._validate_interval(interval)

