import json
import os
import shutil
import tempfile
import unittest
import unittest.mock
from typing import Any, Optional

import pytest
from click.testing import CliRunner

from sidechain_cli.main import main
from sidechain_cli.utils.config_file import _CONFIG_FILE

tempdir: Optional[tempfile.TemporaryDirectory] = None
env_vars: Optional[Any] = None


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    global tempdir, env_vars
    tempdir = tempfile.TemporaryDirectory()
    env_vars = unittest.mock.patch.dict(
        os.environ,
        {
            "XCHAIN_CONFIG_DIR": tempdir.name,
        },
    )
    env_vars.start()


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    shutil.rmtree(tempdir.name)
    env_vars.stop()


@pytest.fixture(autouse=True)
def runner():
    print("Hiiiiiiiasdufhas8dfoasdijfak")
    # reset CLI config file
    os.remove(_CONFIG_FILE)
    with open(_CONFIG_FILE, "w") as f:
        data = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)

    cli_runner = CliRunner()

    # create config files
    result = cli_runner.invoke(main, ["server", "create-config", "all"])
    assert result.exit_code == 0

    # start servers
    start_result = cli_runner.invoke(main, ["server", "start-all", "--verbose"])
    assert start_result.exit_code == 0, start_result.output

    yield cli_runner

    # stop servers
    stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
    assert stop_result.exit_code == 0, stop_result.output
