"""CLI functions for starting/stopping a rippled node."""

import os
import subprocess
import time
from typing import Optional

import click

from sidechain_cli.utils import (
    CONFIG_FOLDER,
    ChainData,
    add_chain,
    check_chain_exists,
    get_config,
    remove_chain,
)


@click.command(name="start")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the chain (used for differentiation purposes).",
)
@click.option(
    "--rippled",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the rippled executable.",
)
@click.option(
    "--config",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the rippled config file.",
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def start_chain(name: str, rippled: str, config: str, verbose: bool = False) -> None:
    """
    Start a standalone node of rippled.
    \f

    Args:
        name: The name of the chain (used for differentiation purposes).
        rippled: The filepath to the rippled executable.
        config: The filepath to the rippled config file.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    rippled = os.path.abspath(rippled)
    config = os.path.abspath(config)
    if check_chain_exists(name, config):
        print("Error: Chain already running with that name or config.")
        return
    to_run = [rippled, "--conf", config, "-a", "--silent"]
    if verbose:
        print(f"Starting server {name}...")

    # create output file for easier debug purposes
    output_file = f"{CONFIG_FOLDER}/{name}.out"
    if not os.path.exists(output_file):
        # initialize file if it doesn't exist
        with open(output_file, "w") as f:
            f.write("")
    fout = open(output_file, "w")

    process = subprocess.Popen(
        to_run, stdout=fout, stderr=subprocess.STDOUT, close_fds=True
    )
    pid = process.pid

    chain_data: ChainData = {
        "name": name,
        "rippled": rippled,
        "config": config,
        "pid": pid,
    }

    # check if rippled actually started up correctly
    time.sleep(0.3)
    if process.poll() is not None:
        print("ERROR")
        with open(output_file) as f:
            print(f.read())
        return

    # add chain to config file
    add_chain(chain_data)
    if verbose:
        print(f"started rippled at `{rippled}` with config `{config}`", flush=True)
        print(f"PID: {pid}", flush=True)


@click.command(name="stop")
@click.option("--name", help="The name of the chain to stop.")
@click.option(
    "--all", "stop_all", is_flag=True, help="Whether to stop all of the chains."
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
def stop_chain(
    name: Optional[str] = None, stop_all: bool = False, verbose: bool = False
) -> None:
    """
    Stop a rippled node(s).
    \f

    Args:
        name: The name of the chain to stop.
        stop_all: Whether to stop all of the chains.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if name is None and stop_all is False:
        print("Error: Must specify a name or `--all`.")
        return
    config = get_config()
    if stop_all:
        chains = config.chains
    else:
        chains = [chain for chain in config.chains if chain["name"] == name]
    if verbose:
        chain_names = ",".join([chain["name"] for chain in chains])
        print(f"Shutting down: {chain_names}")

    fout = open(os.devnull, "w")
    for chain in chains:
        name = chain["name"]
        rippled = chain["rippled"]
        config = chain["config"]
        to_run = [rippled, "--conf", config, "stop"]
        subprocess.call(to_run, stdout=fout, stderr=subprocess.STDOUT)
        if verbose:
            print(f"Stopped {name}")

    remove_chain(name, stop_all)


@click.command(name="restart")
@click.option("--name", help="The name of the chain to restart.")
@click.option(
    "--all", "restart_all", is_flag=True, help="Whether to stop all of the chains."
)
@click.option(
    "--verbose", is_flag=True, help="Whether or not to print more verbose information."
)
@click.pass_context
def restart_chain(
    ctx: click.Context,
    name: Optional[str] = None,
    restart_all: bool = False,
    verbose: bool = False,
) -> None:
    """
    Restart a rippled node(s).
    \f

    Args:
        ctx: The click context.
        name: The name of the chain to restart.
        restart_all: Whether to restart all of the chains.
        verbose: Whether or not to print more verbose information.
    """  # noqa: D301
    if name is None and restart_all is False:
        print("Error: Must specify a name or `--all`.")
        return

    config = get_config()
    if restart_all:
        chains = config.chains
    else:
        chains = [chain for chain in config.chains if chain["name"] == name]

    ctx.invoke(stop_chain, name=name, stop_all=restart_all, verbose=verbose)
    for chain in chains:
        ctx.invoke(
            start_chain,
            name=chain["name"],
            rippled=chain["rippled"],
            config=chain["config"],
            verbose=verbose,
        )
