import abc
import dataclasses
import uuid
from typing import List, Optional, Dict, Any


@dataclasses.dataclass
class Cron:
    command: str
    interval: str
    id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self):
        return f"{self.interval} {self.command} # id: {self.id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Cron object to dictionary."""
        return {
            'id': self.id,
            'command': self.command,
            'interval': self.interval
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cron':
        """Create Cron object from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            command=data['command'],
            interval=data['interval']
        )


class BaseInterface(metaclass=abc.ABCMeta):

    operational_system = None

    def get_all(self) -> List[Cron]:
        """Get all scheduled tasks."""
        raise NotImplementedError

    def add(self, command: str, interval: str) -> Cron:
        """Add a new scheduled task."""
        raise NotImplementedError

    def delete(self, cron_id: str) -> bool:
        """Delete a scheduled task by ID."""
        raise NotImplementedError

    def edit(self, cron_id: str, **kwargs) -> bool:
        """Edit an existing scheduled task."""
        raise NotImplementedError
    
    def get_by_id(self, cron_id: str) -> Optional[Cron]:
        """Get a specific scheduled task by ID."""
        raise NotImplementedError
    
    def clear_all(self) -> bool:
        """Clear all scheduled tasks."""
        raise NotImplementedError
    
    def is_valid_cron_format(self, interval: str) -> bool:
        """Validate cron interval format."""
        raise NotImplementedError
    
    # Métodos auxiliares
    def count(self) -> int:
        """Get the total number of scheduled tasks."""
        return len(self.get_all())
    
    def exists(self, cron_id: str) -> bool:
        """Check if a scheduled task exists by ID."""
        return self.get_by_id(cron_id) is not None
    
    def get_by_command(self, command: str) -> List[Cron]:
        """Get all scheduled tasks with a specific command."""
        return [cron for cron in self.get_all() if cron.command == command]
    
    def get_by_interval(self, interval: str) -> List[Cron]:
        """Get all scheduled tasks with a specific interval."""
        return [cron for cron in self.get_all() if cron.interval == interval]
    
    def delete_by_command(self, command: str) -> int:
        """Delete all scheduled tasks with a specific command. Returns number of deleted tasks."""
        tasks_to_delete = self.get_by_command(command)
        deleted_count = 0
        for task in tasks_to_delete:
            if self.delete(task.id):
                deleted_count += 1
        return deleted_count
    
    def delete_by_interval(self, interval: str) -> int:
        """Delete all scheduled tasks with a specific interval. Returns number of deleted tasks."""
        tasks_to_delete = self.get_by_interval(interval)
        deleted_count = 0
        for task in tasks_to_delete:
            if self.delete(task.id):
                deleted_count += 1
        return deleted_count
    
    def update_command(self, cron_id: str, new_command: str) -> bool:
        """Update only the command of a scheduled task."""
        return self.edit(cron_id, command=new_command)
    
    def update_interval(self, cron_id: str, new_interval: str) -> bool:
        """Update only the interval of a scheduled task."""
        return self.edit(cron_id, interval=new_interval)
    
    def duplicate(self, cron_id: str, new_interval: str = None) -> Optional[Cron]:
        """Duplicate a scheduled task with optional new interval."""
        original = self.get_by_id(cron_id)
        if not original:
            return None
        
        new_interval = new_interval or original.interval
        return self.add(original.command, new_interval)
