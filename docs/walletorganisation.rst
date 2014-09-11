Wallet organisation
===================

SwapBill and host wallets
----------------------------

When you run the client there are two different wallet locations to be aware of:

* the 'standard' bitcoind wallet built in to bitcoind, and
* a separate, independant wallet only by the SwapBill client.

Through the RPC interface SwapBill effectively has access to your bitcoind wallet, and uses this for this to pay for:

1. transaction fees
#. dust output amounts
#. 'burn' transactions
#. host currency payments as part of an exchange between swapbill and host currency

The first two items listed here are essentially 'backing' funds and should only ever consume very small amounts of host currency.

The last two items can potentially be significant amounts, but SwapBill will only make these kinds of payments as part
of quite specific actions.

SwapBill wallets
------------------

SwapBill then stores another set of private keys, separately from bitcoind, to control SwapBill specific outputs.
These are essentially outputs that control balances in the SwapBill protocol, and it's necessary for SwapBill to
track these keys independantly in order to prevent bitcoind from inadvertently consuming these outputs.

These private keys can be found in 'wallet.txt' files, located in the SwapBill data directory, under host specific subdirectories.

As well as private keys, SwapBill also stores 'secrets', located in 'secretsWallet.txt'.
These secrets are host independant, and 'secretsWallet.txt' is therefore located outside of host specific subdirectories.

Don't send your wallet files or reveal the contents to anyone,
unless you want them to be able to spend your swapbill, and make sure that these files are backed up securely!
