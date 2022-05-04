import abc
import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class Cron:
    command: str
    interval: str

    def __str__(self):
        return f"{self.interval} {self.command}"


class BaseInterface(metaclass=abc.ABCMeta):

    operational_system = None

    def get_all(self) -> Optional[List[Cron]]:
        raise NotImplementedError

    def add(self, command, interval) -> Cron:
        raise NotImplementedError

    def delete(self, cron_name) -> bool:
        raise NotImplementedError

    def edit(self, cron_name, **kwargs) -> bool:
        raise NotImplementedError
