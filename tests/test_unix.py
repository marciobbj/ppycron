import os
import pytest
from ppycron.src.base import Cron


@pytest.fixture(scope="function")
def config_file(tmp_path):
    # Using a temporary file to simulate the crontab content
    cronfile = tmp_path / "crontab_file"
    cronfile.write_text("# Sample cron jobs for testing\n")
    return cronfile


@pytest.fixture
def subprocess_run(mocker):
    yield mocker.patch("ppycron.src.unix.subprocess.run")


@pytest.fixture
def subprocess_check_output(mocker, config_file):
    # Use the content of the temp file as mock data for check_output
    data = config_file.read_text()
    yield mocker.patch(
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
        (
            "1 * * * 1,2 echo this-is-a-test",
            "1 * * * 1,2",
            "echo this-is-a-test",
        ),
        (
            "*/2 * * * * echo for-this-test",
            "*/2 * * * *",
            "echo for-this-test",
        ),
        (
            "1 2 * * * echo we-will-need-tests",
            "1 2 * * *",
            "echo we-will-need-tests",
        ),
        (
            "1 3-4 * * * echo soon-this-test",
            "1 3-4 * * *",
            "echo soon-this-test",
        ),
        (
            "*/15 0 * * * sh /path/to/file.sh",
            "*/15 0 * * *",
            "sh /path/to/file.sh",
        ),
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
    # Ensure that the crontab command was executed
    subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True)


@pytest.mark.parametrize(
    "cron_line,interval,command",
    [
        (
            '*/15 0 * * * echo "hello"',
            "*/15 0 * * *",
            'echo "hello"',
        ),
        (
            "3 * * * 3,5 echo this-is-a-test",
            "3 * * * 3,5",
            "echo this-is-a-test",
        ),
        (
            "*/6 * * * * echo for-this-test",
            "*/6 * * * *",
            "echo for-this-test",
        ),
        (
            "9 3 * * * echo we-will-need-tests",
            "9 3 * * *",
            "echo we-will-need-tests",
        ),
        (
            "10 2-4 * * * echo soon-this-test",
            "10 2-4 * * *",
            "echo soon-this-test",
        ),
        (
            "*/15 0 * * * sh /path/to/file.sh",
            "*/15 0 * * *",
            "sh /path/to/file.sh",
        ),
    ],
)
def test_get_cron_jobs(
    crontab, config_file, cron_line, interval, command, subprocess_check_output
):
    crontab.get_all()
    subprocess_check_output.assert_called_with(["crontab", "-l"])


def test_edit_cron(
    crontab, config_file, subprocess_check_output, subprocess_run, mocker
):
    job = crontab.add(command='echo "hello"', interval="*/15 0 * * *")
    crontab.edit(
        cron_command=job.command, command="echo edited-command", interval="*/15 0 * * *"
    )

    subprocess_check_output.assert_called_with(["crontab", "-l"])
    subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True)


def test_delete_cron(
    crontab, config_file, subprocess_check_output, subprocess_run, mocker
):
    crontab.add(
        command="echo job_to_be_deleted",
        interval="*/15 0 * * *",
    )
    crontab.delete(cron_command="echo job_to_be_deleted")

    subprocess_check_output.assert_called_with(["crontab", "-l"])
    subprocess_run.assert_called_with(["crontab", mocker.ANY], check=True)
