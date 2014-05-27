# Requirements

The SwapBill client is written in Python and supports Python versions 2.7, 3.2, 3.3 and 3.4.

The third party Python 'ecdsa' and 'requests' modules are required and must be installed.

The client uses the litecoin reference client (litecoinQT or litecoind) as a backend, and so this reference client must also be installed.

The client has been tested on Linux and Windows, but should work on any platform which supports the litecoin reference client and the
required Python dependencies.

# Setting up litecoinQT or litecoind as an RPC server

You can get the reference client from <https://litecoin.org/>.

The SwapBill client connects to the reference client with RPC calls, and so we need to ensure that this set up as an RPC server.

The reference client should then also connect to the litecoin testnet (as opposed to mainnet), and maintain a full transaction index.

To set this up, create a litecoin.conf file in the default location (if you don't already have one), and add some lines like the following:

    server=1
    testnet=1
    txindex=1
    rpcuser=litecoinrpc
    rpcpassword=somesecretpassword

(Change the password!)

The default location for this file on Linux is `~/.litecoin/litecoin.conf`,
while on Windows it looks like this is located at the path corresponding to `C:\Users\YourUserName\AppData\Roaming\LiteCoin\litecoin.conf`,
depending on your system setup.

To start the server you can then either launch litecoinQT (the graphical client) normally, or run litecoind from the command line.
If running litecoind, the -printtoconsole option can be used to get console output about what the server is doing.

If you already ran the reference client previously, against testnet, *without the txindex option* a reindexing operation will be required,
you should get a message about this.
If running litecoinQT you should be able to just click OK to go ahead, or you can call litecoind with the -reindex option to do this explicitly.

You can test the RPC server by making RPC queries from the command line, e.g.:

    ~/git/litecoin/src $ ./litecoind getbalance
    11914.15504872

(This RPC interface is very handy for interaction with the reference client generally, and for general troubleshooting.)

# Running the client

There's no installation process for the client, currently, and instead this just runs directly
from the downloaded source tree.
(You'll need to ensure that third party dependencies are met, before running the client, or you'll get an error message telling you to do this.)

The project is currently hosted on <https://github.com/crispweed/swapbill>, so you can get the client source code with:

```
~/git $ git clone https://github.com/crispweed/swapbill
Cloning into 'swapbill'...
remote: Counting objects: 52, done.
remote: Compressing objects: 100% (41/41), done.
remote: Total 52 (delta 9), reused 46 (delta 3)
Unpacking objects: 100% (52/52), done.
```

and then run the client with (e.g.):

```
~/git $ cd swapbill/
~/git/swapbill $ python Client.py get_balance
```

Or, if you don't have git, you can download the archive from <https://github.com/crispweed/swapbill/archive/master.zip>, extract to a new directory, and run from there.

If you don't have litecoind or litecoinQT running, or if you don't have the RPC interface set up correctly, you'll see something like:

```
~/git/swapbill $ python Client.py get_balance
Couldn't connect for remote procedure call, will sleep for ten seconds and then try again.
Couldn't connect for remote procedure call, will sleep for ten seconds and then try again.
(...repeated indefinitely)
```

If the RPC interface is working correctly, however, you should see something like this:

```
~/git/swapbill $ python Client.py get_balance
Failed to load from cache, full index generation required (no cache file found)
State update starting from block 280696
Committed state updated to start of block 283286
In memory state updated to end of block 283306
Operation successful
active : 0
spendable : 0
total : 0
```

