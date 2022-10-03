"""CLI command for setting up a bridge."""

import json
import os
from pprint import pformat
from typing import Any, Dict, List, Tuple, cast

import click
from xrpl.models import ServerState, SignerEntry, SignerListSet, XChainCreateBridge

from sidechain_cli.misc.fund import fund_account
from sidechain_cli.utils import (
    BridgeConfig,
    BridgeData,
    add_bridge,
    check_bridge_exists,
    check_chain_exists,
    check_witness_exists,
    get_config,
    submit_tx,
)


@click.command(name="build")
@click.option(
    "--name",
    required=True,
    prompt=True,
    help="The name of the bridge (used for differentiation purposes).",
)
@click.option(
    "--chains",
    required=True,
    nargs=2,
    type=str,
    help="The two chains that the bridge goes between.",
)
@click.option(
    "--witness",
    "witnesses",
    required=True,
    multiple=True,
    type=str,
    help="The witness servers that monitor the bridge.",
)
@click.option(
    "--bootstrap",
    envvar="XCHAIN_CONFIG_DIR",
    required=True,
    prompt=True,
    type=click.Path(exists=True),
    help="The filepath to the bootstrap config file.",
)
@click.option(
    "--signature_reward",
    default="100",
    help="The reward for witnesses providing a signature.",
)
@click.option(
    "-v",
    "--verbose",
    help="Whether or not to print more verbose information. Also supports `-vv`.",
    count=True,
)
@click.pass_context
def setup_bridge(
    ctx: click.Context,
    name: str,
    chains: Tuple[str, str],
    witnesses: List[str],
    bootstrap: str,
    signature_reward: str,
    verbose: int = 0,
) -> None:
    """
    Keep track of a bridge between a locking chain and issuing chain.
    \f

    Args:
        ctx: The click context.
        name: The name of the bridge (used for differentiation purposes).
        chains: The two chains that the bridge goes between.
        witnesses: The witness server(s) that monitor the bridge.
        bootstrap: The filepath to the bootstrap config file.
        signature_reward: The reward for witnesses providing a signature.
        verbose: Whether or not to print more verbose information. Add more v's for
            more verbosity.
    """  # noqa: D301
    # check name
    if check_bridge_exists(name):
        click.echo(f"Bridge named {name} already exists.")
        return
    # validate chains
    for chain in chains:
        if not check_chain_exists(chain):
            click.echo(f"Chain {chain} is not running.")
            return
    # validate witnesses
    for witness in witnesses:
        if not check_witness_exists(witness):
            click.echo(f"Witness {witness} is not running.")
            return

    config = get_config()
    witness_config = config.get_witness((witnesses[0])).get_config()
    doors = (
        witness_config["XChainBridge"]["LockingChainDoor"],
        witness_config["XChainBridge"]["IssuingChainDoor"],
    )
    tokens = (
        witness_config["XChainBridge"]["LockingChainIssue"],
        witness_config["XChainBridge"]["IssuingChainIssue"],
    )

    chain1 = config.get_chain(chains[0])
    client1 = chain1.get_client()
    chain2 = config.get_chain(chains[1])
    client2 = chain2.get_client()
    server_state1 = client1.request(ServerState())
    min_create1 = server_state1.result["state"]["validated_ledger"]["reserve_base"]
    server_state2 = client2.request(ServerState())
    min_create2 = server_state2.result["state"]["validated_ledger"]["reserve_base"]

    bridge_data: BridgeData = {
        "name": name,
        "chains": chains,
        "num_witnesses": len(witnesses),
        "door_accounts": doors,
        "xchain_currencies": tokens,
        "signature_reward": signature_reward,
        "create_account_amounts": (str(min_create2), str(min_create1)),
    }

    if verbose:
        click.echo(pformat(bridge_data))
    add_bridge(bridge_data)

    # get bootstrap if using env var
    if bootstrap == os.getenv("XCHAIN_CONFIG_DIR"):
        bootstrap = os.path.join(bootstrap, "bridge_bootstrap.json")

    with open(bootstrap) as f:
        bootstrap_config = json.load(f)

    bridge_config = BridgeConfig.from_dict(cast(Dict[str, Any], bridge_data))

    chain1 = get_config().get_chain(bridge_config.chains[0])
    client1 = chain1.get_client()
    chain2 = get_config().get_chain(bridge_config.chains[1])
    client2 = chain2.get_client()

    signer_entries = []
    for witness_entry in bootstrap_config["Witnesses"]["SignerList"]:
        signer_entries.append(
            SignerEntry(
                account=witness_entry["Account"], signer_weight=witness_entry["Weight"]
            )
        )

    bridge_obj = bridge_config.get_bridge()
    locking_door_account = bootstrap_config["LockingChain"]["DoorAccount"]["Address"]
    locking_door_seed = bootstrap_config["LockingChain"]["DoorAccount"]["Seed"]

    create_tx1 = XChainCreateBridge(
        account=locking_door_account,
        xchain_bridge=bridge_obj,
        signature_reward=bridge_config.signature_reward,
        min_account_create_amount=bridge_config.create_account_amounts[0],
    )
    submit_tx(create_tx1, client1, locking_door_seed, verbose)

    signer_tx1 = SignerListSet(
        account=locking_door_account,
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx(signer_tx1, client1, locking_door_seed, verbose)

    # TODO: disable master key

    issuing_door_account = bootstrap_config["IssuingChain"]["DoorAccount"]["Address"]
    issuing_door_seed = bootstrap_config["IssuingChain"]["DoorAccount"]["Seed"]

    create_tx2 = XChainCreateBridge(
        account=issuing_door_account,
        xchain_bridge=bridge_obj,
        signature_reward=bridge_config.signature_reward,
        min_account_create_amount=bridge_config.create_account_amounts[1],
    )
    issuing_door_seed = bootstrap_config["IssuingChain"]["DoorAccount"]["Seed"]
    submit_tx(create_tx2, client2, issuing_door_seed, verbose)

    signer_tx2 = SignerListSet(
        account=issuing_door_account,
        signer_quorum=max(1, len(signer_entries) - 1),
        signer_entries=signer_entries,
    )
    submit_tx(signer_tx2, client2, issuing_door_seed, verbose)

    # TODO: disable master key

    accounts_to_create = set(
        bootstrap_config["IssuingChain"]["WitnessRewardAccounts"]
        + bootstrap_config["IssuingChain"]["WitnessSubmitAccounts"]
    )
    for witness_acct in accounts_to_create:
        ctx.invoke(
            fund_account,
            chain=bridge_config.chains[0],
            account=witness_acct,
            verbose=verbose > 1,
        )
        ctx.invoke(
            fund_account,
            chain=bridge_config.chains[1],
            account=witness_acct,
            verbose=verbose > 1,
        )

    if verbose > 0:
        click.secho("Initialized witness reward accounts", fg="blue")
