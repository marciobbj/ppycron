import logging
from tempfile import NamedTemporaryFile
from typing import List, Union
from ppycron.src.base import BaseInterface, Cron
import subprocess
import os

logger = logging.getLogger(__name__)


class UnixInterface(BaseInterface):

    operational_system = "linux"

    def __init__(self):
        with NamedTemporaryFile("w") as f:
            f.write("# Created automatically by Pycron =)\n")
            f.flush()
            os.system(f"crontab {f.name}")

    def add(self, command, interval) -> Cron:
        cron = Cron(command=command, interval=interval)
        pipe = os.popen("crontab -l")
        current = pipe.read()
        current += str(cron) + "\n"
        with NamedTemporaryFile("w") as f:
            f.write(str(current))
            f.flush()
            os.system(f"crontab {f.name}")
        return cron

    def get_all(self) -> Union[List[Cron], List]:
        output = subprocess.check_output(["crontab", "-l"])
        crons = []
        for line in output.decode("utf8").split("\n"):
            is_comment = line.startswith("#")
            if is_comment:
                continue
            interval = " ".join(
                line.split(" ")[:5]
            )  # get all characters between spaces until its fifth element
            command = " ".join(
                line.split(" ")[5:]
            ).strip()  # join the last elements, they are the command
            name = " ".join(line.split(" ")[-1:])  # gets the name of the crontab
            if name:
                crons.append(Cron(command=command, interval=interval))
        return crons

    def edit(self, cron_command, **kwargs) -> bool:
        class NotEnoughInformation(Exception):
            pass

        if not cron_command:
            raise NotEnoughInformation()

        new_command = cron_command
        new_interval = kwargs.get("interval")
        if not all([new_interval, new_command]):
            raise NotEnoughInformation("Cannot edit without information")
        output = subprocess.check_output(["crontab", "-l"])
        lines = []
        for line in output.decode("utf8").split("\n"):
            is_comment = line.startswith("#")
            if is_comment:
                lines.append(line + "\n")
                continue
            interval = " ".join(
                line.split(" ")[:5]
            )  # get all characters between spaces until its fifth element
            command = " ".join(
                line.split(" ")[5:]
            ).strip()  # join the last elements, they are the command
            # name = " ".join(line.split(" ")[-1:])  # gets the name of the crontab
            if command == cron_command:
                # if we find the line, we replace the contents
                if new_interval:
                    line = line.replace(interval, new_interval)
                if new_command:
                    line = line.replace(command, new_command)
            lines.append(line + "\n")
        current = ""
        for line in lines:
            current += line
        with NamedTemporaryFile("w") as f:
            f.write(str(current))
            f.flush()
            os.system(f"crontab {f.name}")
        return True

    def delete(self, cron_command) -> bool:
        class NotEnoughInformation(Exception):
            pass

        if not cron_command:
            raise NotEnoughInformation("You should try pass the cron name")

        output = subprocess.check_output(["crontab", "-l"])
        lines = []
        for line in output.decode("utf8").split("\n"):
            is_comment = line.startswith("#")
            if is_comment:
                lines.append(line + "\n")
                continue
            command = " ".join(line.split(" ")[5:])  # gets the command of the crontab
            if command == cron_command:
                # Delete line
                line = ""
            lines.append(line + "\n")
        current = ""
        for line in lines:
            current += line
        with NamedTemporaryFile("w") as f:
            f.write(str(current))
            f.flush()
            os.system(f"crontab {f.name}")
        return True
