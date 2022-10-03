rm ~/.config/sidechain-cli/config.json  # TODO: remove once cleanup is better
sidechain-cli server create-config all
sidechain-cli server start-all --verbose
sidechain-cli server list
read -p "Pausing... (hit enter to continue)"
jq .LockingChain.DoorAccount.Address $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs sidechain-cli fund --chain locking_chain --account
jq '.LockingChain.WitnessSubmitAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs -L1 sidechain-cli fund --chain locking_chain --account
jq '.LockingChain.WitnessRewardAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs -L1 sidechain-cli fund --chain locking_chain --account
sidechain-cli bridge build --bridge bridge --bootstrap $XCHAIN_CONFIG_DIR/bridge_bootstrap.json --verbose
sidechain-cli fund --chain locking_chain --account raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
sidechain-cli fund --chain issuing_chain --account rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi
sidechain-cli fund --chain issuing_chain --account rGzx83BVoqTYbGn7tiVAnFw7cbxjin13jL
sidechain-cli bridge transfer --bridge bridge --src_chain locking_chain --amount 10000000 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --tutorial
