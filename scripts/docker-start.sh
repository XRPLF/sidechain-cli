rm ~/.config/xbridge-cli/config.json  # TODO: remove once cleanup is better
xbridge-cli server create-config all --docker
xbridge-cli server start-all --docker
xbridge-cli server list
xbridge-cli explorer
jq .LockingChain.DoorAccount.Address $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs xbridge-cli fund locking_chain
jq '.LockingChain.WitnessSubmitAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs xbridge-cli fund locking_chain
jq '.LockingChain.WitnessRewardAccounts[]' $XCHAIN_CONFIG_DIR/bridge_bootstrap.json | tr -d '"' | xargs xbridge-cli fund locking_chain
xbridge-cli bridge build --name=bridge -v
xbridge-cli fund locking_chain raFcdz1g8LWJDJWJE2ZKLRGdmUmsTyxaym
xbridge-cli bridge create-account --from-locking --bridge bridge --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to rJdTJRJZ6GXCCRaamHJgEqVzB7Zy4557Pi --amount 10 -v
xbridge-cli bridge transfer --bridge bridge --from-locking --amount 10 --from snqs2zzXuMA71w9isKHPTrvFn1HaJ --to snyEJjY2Xi5Dxdh81Jy9Mj3AiYRQM --verbose
