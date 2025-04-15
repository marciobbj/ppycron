import os
import pytest
from ppycron.src.base import Cron


@pytest.fixture(scope="function")
def config_file(tmp_path):
    # Usando um arquivo temporário para simular o conteúdo do crontab
    cronfile = tmp_path / "crontab_file"
    cronfile.write_text("# Sample cron jobs for testing\n")
    return cronfile


@pytest.fixture
def subprocess_run(mocker):
    yield mocker.patch("ppycron.src.unix.subprocess.run")


@pytest.fixture
def subprocess_check_output(mocker, config_file):
    # Inicialmente, usa o conteúdo do arquivo temporário como dado para check_output.
    data = config_file.read_text()
    return mocker.patch(
        "ppycron.src.unix.subprocess.check_output",
        return_value=data.encode("utf-8"),
    )


@pytest.fixture
def crontab(subprocess_run):
    from ppycron.src.unix import UnixInterface
    return UnixInterface()


@pytest.mark.parametrize(
    "cron_line,interval,command",
    [
        ('*/15 0 * * * echo "hello"', "*/15 0 * * *", 'echo "hello"'),
        ("1 * * * 1,2 echo this-is-a-test", "1 * * * 1,2", "echo this-is-a-test"),
        ("*/2 * * * * echo for-this-test", "*/2 * * * *", "echo for-this-test"),
        ("1 2 * * * echo we-will-need-tests", "1 2 * * *", "echo we-will-need-tests"),
        ("1 3-4 * * * echo soon-this-test", "1 3-4 * * *", "echo soon-this-test"),
        ("*/15 0 * * * sh /path/to/file.sh", "*/15 0 * * *", "sh /path/to/file.sh"),
    ],
)
def test_add_cron(
    crontab,
    mocker,
    config_file,
    cron_line,
    interval,
    command,
    subprocess_run,
    subprocess_check_output,
):
    cron = crontab.add(command=command, interval=interval)

    assert isinstance(cron, Cron)
    assert cron.command == command
    assert cron.interval == interval
    # Verifica se o id foi gerado e é uma string não vazia
    assert cron.id and isinstance(cron.id, str)
    subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True)


@pytest.mark.parametrize(
    "cron_line,interval,command",
    [
        ('*/15 0 * * * echo "hello"', "*/15 0 * * *", 'echo "hello"'),
        ("3 * * * 3,5 echo this-is-a-test", "3 * * * 3,5", "echo this-is-a-test"),
        ("*/6 * * * * echo for-this-test", "*/6 * * * *", "echo for-this-test"),
        ("9 3 * * * echo we-will-need-tests", "9 3 * * *", "echo we-will-need-tests"),
        ("10 2-4 * * * echo soon-this-test", "10 2-4 * * *", "echo soon-this-test"),
        ("*/15 0 * * * sh /path/to/file.sh", "*/15 0 * * *", "sh /path/to/file.sh"),
    ],
)
def test_get_cron_jobs(
    crontab, config_file, cron_line, interval, command, subprocess_check_output
):
    # Ajusta o arquivo de configuração para conter uma linha com o identificador
    fake_cron_line = f"{cron_line} # id: test-cron-id"
    config_file.write_text(fake_cron_line + "\n")
    # Atualiza o valor de retorno do mock para refletir o conteúdo atualizado do arquivo
    subprocess_check_output.return_value = config_file.read_text().encode("utf-8")
    crons = crontab.get_all()
    # Verifica se pelo menos uma das entradas possui o id esperado
    assert any(c.id == "test-cron-id" for c in crons)
    subprocess_check_output.assert_called_with(["crontab", "-l"])


def test_edit_cron(
    crontab, config_file, subprocess_check_output, subprocess_run, mocker
):
    # Adiciona um job, que terá seu id gerado automaticamente
    job = crontab.add(command='echo "hello"', interval="*/15 0 * * *")
    # Realiza a edição utilizando o identificador único do job
    crontab.edit(
        cron_id=job.id, command="echo edited-command", interval="*/15 0 * * *"
    )

    subprocess_check_output.assert_called_with(["crontab", "-l"])
    subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True)


def test_delete_cron(
    crontab, config_file, subprocess_check_output, subprocess_run, mocker
):
    # Adiciona um job e utiliza seu id para realizar a deleção
    job = crontab.add(
        command="echo job_to_be_deleted",
        interval="*/15 0 * * *",
    )
    crontab.delete(cron_id=job.id)

    subprocess_check_output.assert_called_with(["crontab", "-l"])
    subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True)
