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
            return []  # Nenhum crontab disponível

        crons = []
        for line in output.decode("utf-8").split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            cron_id = ""
            # Verifica se a linha contém o identificador no formato "# id: <uuid>"
            if "# id:" in line:
                cron_line, id_comment = line.split("# id:", 1)
                cron_id = id_comment.strip()
            else:
                cron_line = line

            # Divide a parte do crontab para obter o intervalo e comando
            splitted = cron_line.strip().split()
            if len(splitted) < 6:
                continue  # Linha com formato inesperado, ignora

            interval = " ".join(splitted[:5])
            command = " ".join(splitted[5:]).strip()

            # Cria a instância do Cron com o id extraído (ou vazio, se não existir)
            crons.append(Cron(command=command, interval=interval, id=cron_id))

        return crons

    def edit(self, cron_id, **kwargs) -> bool:
        """
        Edita uma entrada do crontab usando o identificador único `cron_id`.
        Parâmetros opcionais:
            command: novo comando a ser executado.
            interval: novo intervalo no formato do crontab.
        Retorna True se a edição for realizada, caso contrário False.
        """
        if not cron_id:
            raise ValueError("É necessário informar o identificador da entrada de cron.")

        new_command = kwargs.get("command")
        new_interval = kwargs.get("interval")

        try:
            output = subprocess.check_output(["crontab", "-l"]).decode("utf-8")
        except subprocess.CalledProcessError:
            return False

        lines = []
        modified = False

        for line in output.split("\n"):
            # Se a linha estiver vazia ou for comentário genérico, mantemos inalterada
            if line.strip() == "" or (line.strip().startswith("#") and f"id: {cron_id}" not in line):
                lines.append(line)
                continue

            # Verifica se o identificador está na linha
            if f"id: {cron_id}" in line:
                # Separa a linha em duas partes: o cron em si e o comentário do id
                try:
                    cron_part, comment_part = line.split("# id:", 1)
                except ValueError:
                    cron_part = line
                    comment_part = f" id: {cron_id}"

                # Separa a parte cron para extrair o intervalo e comando antigos
                splitted = cron_part.strip().split()
                if len(splitted) < 6:
                    # Formato inesperado, pula a edição
                    lines.append(line)
                    continue

                old_interval = " ".join(splitted[:5])
                old_command = " ".join(splitted[5:])

                # Define os novos valores (caso não sejam informados, mantém os antigos)
                updated_interval = new_interval if new_interval else old_interval
                updated_command = new_command if new_command else old_command

                # Recompõe a linha mantendo o comentário com o id
                line = f"{updated_interval} {updated_command} # id: {cron_id}"
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

    def delete(self, cron_id) -> bool:
        if not cron_id:
            raise ValueError("É necessário informar o identificador da entrada de cron.")

        try:
            output = subprocess.check_output(["crontab", "-l"]).decode("utf-8")
        except subprocess.CalledProcessError:
            return False

        lines = []
        removed = False

        for line in output.split("\n"):
            # Mantém as linhas que não contêm o identificador
            if f"id: {cron_id}" in line:
                removed = True
                continue
            lines.append(line)

        if removed:
            current = "\n".join(lines) + "\n"
            with NamedTemporaryFile("w", delete=False) as f:
                f.write(current)
                f.flush()
                subprocess.run(["crontab", f.name], check=True)
                os.unlink(f.name)
            return True

        return False

