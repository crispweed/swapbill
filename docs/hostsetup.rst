Setting up the host RPC server
=============================================

The (SwapBill) client currently requires a 'full node' to be set up on the host blockchain,
and running as an RPC server.
(See :doc:`requirements`.)
The client will then call through to this RPC server for blockchain updates, and for signing
and sending swapbill transaction.

Downloadable installers
--------------------------

For bitcoin, you can install 'Bitcoin Core', from `here <https://bitcoin.org/en/download>`__.
For litecoin, you can install 'Litecoin-QT', from `here <https://litecoin.org/>`__.

Building from source
--------------------------

Or you can build from source, from https://github.com/bitcoin/bitcoin or https://github.com/litecoin-project/litecoin.

When building from source, note that gui support is not actually required.
If you just build either bitcoind or litecoind, and not the QT versions, you can avoid bringing in QT dependencies.

Configuration
----------------

You'll need to configure bitcoind to start as a server, and to connect to testnet.

The default location for the bitcoind configuration file is ``~/.bitcoin/bitcoin.conf`` on Linux,
and something like ``C:\Users\YourUserName\AppData\Roaming\BitCoin\bitcoin.conf`` on Windows.

(For litecoind the locations are similar, but with 'litecoin' in place of 'bitcoin'.)

Create a file in this default location (if not already present), and add lines like the following::

    server=1
    testnet=1
    rpcuser=rpcuser
    rpcpassword=somesecretpassword

(Change the password!)

To start the server you can then either launch bitcoinQT (the graphical client) normally, or run bitcoind from the command line.

A good setup for Linux can be to tell bitcoind to run in the background (e.g. by adding daemon=1 to the conf file),
and use 'tail -f' to watch the end of the generated log file ('tail -f ~/.bitcoin/testnet3/debug.log').

You can test the RPC server by making RPC queries from the command line, e.g.::

    ~/git/bitcoin/src $ ./bitcoin-cli getbalance
    11914.15504872

or::

    ~/git $ litecoin/src/litecoind getblockcount
    381925

(This RPC interface is very handy for interaction with the reference client generally, and for general troubleshooting.)

Bootstrapping
---------------

When you first start a full node, it can be worthwhile downloading a 'bootstrap' file to speed up initial synchronisation,
but we'll just be connecting to the testnet, and bootstrapping is not really necessary for this.
Just go ahead and start your node and let it synch to the testnet blockchain!

.. When you first start a full node, it can potentially take a *long* time to download the blockchain history,
   and it can be worth speeding this up by downloading a 'bootstrap' file.

   There's some information and discussion about this on the following bitcointalk thread:
   https://bitcointalk.org/index.php?topic=145386.0

   The same thing is also possible for litecoin: https://litecoin.info/Bootstrap.dat

Obtaining host currency
-------------------------

You'll need some host currency to work with.

With testnet coin, it's possible to obtain some coin quite quickly, through testnet 'faucets',
such as `this one <http://tpfaucet.appspot.com/>`__ (for bitcoin testnet), or `here <http://testnet.litecointools.com/>`__
for litecoin testnet.

In the case of the litecoin testnet it's also fairly easy to get testnet coin directly by through the (CPU) mining functionality in litecoind.
Use the ```setgenerate true``` RPC command to turn this on.
(It seems a lot harder to do this with bitcoin testnet, though.)

SwapBill client configuration
--------------------------------

The SwapBill client looks for your bitcoin or litecoin config file in the default locations, and reads your rpc username and password from there,
so no additial configuration should be required before running the SwapBill client.

