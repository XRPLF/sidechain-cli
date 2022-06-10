"""Utils for working with the config file."""

from sidechain_cli.utils.config_file import ConfigFile
from sidechain_cli.utils.types import ChainData


def _get_config() -> ConfigFile:
    return ConfigFile.from_file()


def add_chain(chain_data: ChainData) -> None:
    """
    Add a chain's data to the config file.

    Args:
        chain_data: The data of the chain to add.
    """
    conf = _get_config()
    conf.chains.append(chain_data)
    conf.write_to_file()


def check_chain_exists(chain_name: str, chain_config: str) -> bool:
    """
    Check if a chain with a given name or config is already running.

    Args:
        chain_name: The name of the chain to check.
        chain_config: The name of the config to check.

    Returns:
        Whether there is already a chain running with that name or config.
    """
    conf = _get_config()
    for chain in conf.chains:
        if chain["name"] == chain_name:
            return True
        if chain["config"] == chain_config:
            return True
    return False
