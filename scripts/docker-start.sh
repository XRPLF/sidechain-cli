rm ~/.config/sidechain-cli/config.json  # TODO: remove once cleanup is better
sidechain-cli server create-config all --docker
sidechain-cli server start-all --rippled-only --docker
sidechain-cli server list
sidechain-cli explorer
jq .LockingChain.DoorAccount.Address $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund --chain locking_chain --account
jq '.LockingChain.WitnessSubmitAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs -L1 sidechain-cli fund --chain locking_chain --account
jq '.LockingChain.WitnessRewardAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs -L1 sidechain-cli fund --chain locking_chain --account
sidechain-cli bridge build --name=bridge -v
sidechain-cli server start-all --witness-only --docker
sidechain-cli server list
sidechain-cli fund --chain locking_chain --account raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
sidechain-cli bridge create-account --from_locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi --amount 10 -v
sidechain-cli bridge transfer --bridge bridge --from_locking --amount 10000000 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --verbose
