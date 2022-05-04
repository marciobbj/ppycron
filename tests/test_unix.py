import os

import pytest

from ppycron.src.base import Cron


@pytest.fixture(scope="function")
def config_file():
    # TODO: use temp file here
    cronfile = open(os.path.abspath("tests/fixtures/crontab_file"), "r")
    yield cronfile
    cronfile.close()


@pytest.fixture
def os_system(mocker):
    yield mocker.patch("ppycron.src.unix.os.system")


@pytest.fixture
def os_popen(mocker):
    yield mocker.patch("ppycron.src.unix.os.popen")


@pytest.fixture
def subprocess_check_output(mocker, config_file):
    data = bytes(config_file.read(), "utf8")
    yield mocker.patch(
        "ppycron.src.unix.subprocess.check_output",
        return_value=data,
    )


@pytest.fixture
def crontab(os_system):
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
    crontab, config_file, cron_line, interval, command, mocker, os_system, os_popen
):
    cron = crontab.add(command=command, interval=interval)

    assert isinstance(cron, Cron)
    assert cron.command == command
    assert cron.interval == interval
    os_system.assert_called()
    os_popen.assert_called()


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
    crontab, config_file, cron_line, interval, command, mocker, subprocess_check_output
):
    crontab.get_all()
    subprocess_check_output.assert_called()


def test_edit_cron(crontab, config_file, mocker, subprocess_check_output, os_popen):
    job = crontab.add(command='echo "hello"', interval="*/15 0 * * *")
    crontab.edit(
        cron_command=job.command, command="echo edited-command", interval="*/15 0 * * *"
    )
    assert subprocess_check_output.called
    assert os_popen.called


def test_delete_cron(crontab, config_file, mocker, os_popen, subprocess_check_output, os_system):
    crontab.add(
        command="echo job_to_be_deleted",
        interval="*/15 0 * * *",
    )
    crontab.delete(cron_command="echo job_to_be_deleted")

    os_popen.assert_called()
    subprocess_check_output.assert_called()
    os_system.assert_called()
