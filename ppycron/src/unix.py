import logging
import subprocess
import os
from tempfile import NamedTemporaryFile
from typing import List, Union
from ppycron.src.base import BaseInterface, Cron

logger = logging.getLogger(__name__)


class UnixInterface(BaseInterface):

    operational_system = "linux"

    def __init__(self):
        with NamedTemporaryFile("w", delete=False) as f:
            f.write("# Created automatically by Pycron =)\n")
            f.flush()
            subprocess.run(["crontab", f.name], check=True)
            os.unlink(f.name)

    def add(self, command, interval) -> Cron:
        cron = Cron(command=command, interval=interval)
        try:
            current = subprocess.check_output(["crontab", "-l"]).decode("utf-8")
        except subprocess.CalledProcessError:
            current = ""  # If no crontab exists, start with an empty string

        current += str(cron) + "\n"

        with NamedTemporaryFile("w", delete=False) as f:
            f.write(current)
            f.flush()
            subprocess.run(["crontab", f.name], check=True)
            os.unlink(f.name)

        return cron

    def get_all(self) -> Union[List[Cron], List]:
        try:
            output = subprocess.check_output(["crontab", "-l"])
        except subprocess.CalledProcessError:
            return []  # No crontab available

        crons = []
        for line in output.decode("utf-8").split("\n"):
            if line.strip() == "" or line.startswith("#"):
                continue

            interval = " ".join(line.split()[:5])
            command = " ".join(line.split()[5:]).strip()

            if command:
                crons.append(Cron(command=command, interval=interval))

        return crons

    def edit(self, cron_command, **kwargs) -> bool:
        if not cron_command:
            raise ValueError("Cron command is required to edit an entry.")

        new_command = kwargs.get("command", cron_command)
        new_interval = kwargs.get("interval")

        try:
            output = subprocess.check_output(["crontab", "-l"]).decode("utf-8")
        except subprocess.CalledProcessError:
            return False

        lines = []
        modified = False
        for line in output.split("\n"):
            if line.strip() == "" or line.startswith("#"):
                lines.append(line)
                continue

            interval = " ".join(line.split()[:5])
            command = " ".join(line.split()[5:]).strip()

            if command == cron_command:
                if new_interval:
                    line = line.replace(interval, new_interval)
                if new_command:
                    line = line.replace(command, new_command)
                modified = True

            lines.append(line)

        if modified:
            current = "\n".join(lines) + "\n"
            with NamedTemporaryFile("w", delete=False) as f:
                f.write(current)
                f.flush()
                subprocess.run(["crontab", f.name], check=True)
                os.unlink(f.name)
            return True
        return False

    def delete(self, cron_command) -> bool:
        if not cron_command:
            raise ValueError("Cron command is required to delete an entry.")

        try:
            output = subprocess.check_output(["crontab", "-l"]).decode("utf-8")
        except subprocess.CalledProcessError:
            return False

        lines = []
        for line in output.split("\n"):
            if line.strip() == "" or line.startswith("#"):
                lines.append(line)
                continue

            command = " ".join(line.split()[5:]).strip()
            if command != cron_command:
                lines.append(line)

        current = "\n".join(lines) + "\n"
        with NamedTemporaryFile("w", delete=False) as f:
            f.write(current)
            f.flush()
            subprocess.run(["crontab", f.name], check=True)
            os.unlink(f.name)

        return True
