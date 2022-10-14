import json
import os
import shutil
import tempfile
import time
import unittest
import unittest.mock
from typing import Any, Dict, List, Optional

import pytest
from click.testing import CliRunner

from sidechain_cli.main import main

config_dir: Optional[tempfile.TemporaryDirectory] = None
home_dir: Optional[tempfile.TemporaryDirectory] = None
mocked_vars: List[Any] = []


def pytest_configure(config):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    global home_dir, config_dir, mocked_vars
    runner = CliRunner()
    runner.invoke(main, ["server", "stop", "--all"])

    config_dir = tempfile.TemporaryDirectory()
    env_vars = unittest.mock.patch.dict(
        os.environ,
        {
            "XCHAIN_CONFIG_DIR": config_dir.name,
        },
    )
    env_vars.start()

    home_dir = tempfile.TemporaryDirectory()
    config_var = unittest.mock.patch(
        "sidechain_cli.utils.config_file.CONFIG_FOLDER",
        home_dir.name,
    )
    config_var.start()

    config_file = os.path.join(home_dir.name, "config.json")
    with open(config_file, "w") as f:
        data: Dict[str, List[Any]] = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)
    config_var2 = unittest.mock.patch(
        "sidechain_cli.utils.config_file._CONFIG_FILE",
        config_file,
    )

    config_var2.start()
    mocked_vars.extend([env_vars, config_var, config_var2])


def pytest_unconfigure(config):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    for var in mocked_vars:
        var.stop()
    shutil.rmtree(home_dir.name)
    shutil.rmtree(config_dir.name)


@pytest.fixture(scope="class")
def runner():
    # reset CLI config file
    config_file = os.path.join(home_dir.name, "config.json")
    os.remove(config_file)
    with open(config_file, "w") as f:
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


@pytest.fixture(scope="class")
def create_bridge():
    # reset CLI config file
    config_file = os.path.join(home_dir.name, "config.json")
    os.remove(config_file)
    with open(config_file, "w") as f:
        data = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)

    cli_runner = CliRunner()

    # create config files
    result = cli_runner.invoke(main, ["server", "create-config", "all"])
    assert result.exit_code == 0

    # start rippled servers
    start_result = cli_runner.invoke(
        main, ["server", "start-all", "--rippled-only", "--verbose"]
    )
    assert start_result.exit_code == 0, start_result.output
    time.sleep(1.5)

    # fund locking door
    config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
    with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
        bootstrap = json.load(f)

    locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]

    # fund needed accounts on the locking chain
    accounts_locking_fund = set(
        [locking_door]
        + bootstrap["LockingChain"]["WitnessRewardAccounts"]
        + bootstrap["LockingChain"]["WitnessSubmitAccounts"]
    )
    for account in accounts_locking_fund:
        fund_result = cli_runner.invoke(
            main, ["fund", f"--account={account}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

    # build bridge
    build_result = cli_runner.invoke(
        main,
        [
            "bridge",
            "build",
            "--name=test_bridge",
            "--chains",
            "locking_chain",
            "issuing_chain",
            "--verbose",
        ],
    )
    assert build_result.exit_code == 0, build_result.output

    # start witness servers
    start_result = cli_runner.invoke(
        main, ["server", "start-all", "--witness-only", "--verbose"]
    )
    assert start_result.exit_code == 0, start_result.output
    time.sleep(0.2)

    yield

    # stop servers
    stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
    assert stop_result.exit_code == 0, stop_result.output


@pytest.fixture(scope="class")
def bridge_build_setup():
    # reset CLI config file
    config_file = os.path.join(home_dir.name, "config.json")
    os.remove(config_file)
    with open(config_file, "w") as f:
        data = {"chains": [], "witnesses": [], "bridges": []}
        json.dump(data, f, indent=4)

    cli_runner = CliRunner()

    # create config files
    result = cli_runner.invoke(main, ["server", "create-config", "all"])
    assert result.exit_code == 0

    # start rippled servers
    start_result = cli_runner.invoke(
        main, ["server", "start-all", "--rippled-only", "--verbose"]
    )
    assert start_result.exit_code == 0, start_result.output
    time.sleep(1.5)

    # fund locking door
    config_dir = os.path.abspath(os.getenv("XCHAIN_CONFIG_DIR"))
    with open(os.path.join(config_dir, "bridge_bootstrap.json")) as f:
        bootstrap = json.load(f)

    locking_door = bootstrap["LockingChain"]["DoorAccount"]["Address"]

    # fund needed accounts on the locking chain
    accounts_locking_fund = set(
        [locking_door]
        + bootstrap["LockingChain"]["WitnessRewardAccounts"]
        + bootstrap["LockingChain"]["WitnessSubmitAccounts"]
    )
    for account in accounts_locking_fund:
        fund_result = cli_runner.invoke(
            main, ["fund", f"--account={account}", "--chain=locking_chain"]
        )
        assert fund_result.exit_code == 0, fund_result.output

    yield

    # stop servers
    stop_result = cli_runner.invoke(main, ["server", "stop", "--all"])
    assert stop_result.exit_code == 0, stop_result.output
