Requirements
====================================

To run the SwapBill reference client you'll need:

* Python version 2.7, 3.2, 3.3 or 3.4
* The third party Python 'ecdsa' and 'requests' modules
* For operations involving 'litecoin testnet swapbill': the litecoin reference client set up and running as an RPC server
* For operations involving 'bitcoin testnet swapbill': the bitcoin reference client set up and running as an RPC server

So you'll need *either* a litecoin *or* bitcoin RPC server set up, but can then work with the corresponding swapbill denomination
for whichever server you have set up.

If you have both RPC servers set up, you can also try out the functionality for cross chain exchanges between these two denominations.

The code has been tested on Linux and Windows, but should work on any platform with support for the litecoin reference client and the
required Python dependencies.

Header only clients
------------------------------------

While the current version of the SwapBill preview client requires a full litecoind or bitcoind node as a backend,
the protocol is designed *not* to require a full blockchain scan, and so a 'header only' client is also possible, and something that will likely be added in the future.
