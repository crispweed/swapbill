# Introduction

SwapBill is an 'embedded' cryptocurrency protocol and cryptocurrency, currently at the preview stage,
and supporting embedding in bitcoin testnet and litecoin testnet.

This project is a (pure python) reference client for the SwapBill protocol.

# Features

In addition to standard cryptocurrency features,
SwapBill notably also provides trustless cross-chain exchange functionality (based on a built-in 'pay on reveal secret' transaction type).

# Requirements

To run the SwapBill reference client you'll need:

* Python version 2.7, 3.2, 3.3 or 3.4
* The third party Python 'ecdsa' and 'requests' modules
* The bitcoin reference client ('Bitcoin Core') set up and running as an RPC server, and/or
* The litecoin reference client ('LitecoinQT') set up and running as an RPC server

The code has been tested on Linux and Windows, but should work on any platform with support for the litecoin reference client and the
required Python dependencies.

# Resources

The SwapBill documentation can be found here: http://swapbill.readthedocs.org

The original bitcointalk announcement thread can be found [here](https://bitcointalk.org/index.php?topic=628547)

The SwapBill source code lives here: https://github.com/crispweed/swapbill

Twitter: @swapbill
Official Subreddit: http://www.reddit.com/r/swapbill/

# Quick start

Download the source code.

Install the required third party python dependencies, e.g.:

* by installing the python-requests and python-ecdsa packages (in Ubuntu or similar, use python3-requests and python3-ecdsa for python3), or
* through pip or easy_install, e.g. 'sudo pip install requests', 'sudo pip install ecdsa' (or without sudo, in a virtualenv)

Set up Bitcoin Core to run as an RPC server, on testnet.
(More details about this in the documentation [here](http://swapbill.readthedocs.org/en/latest/hostsetup.html).)

Run the client, from the top directory of the source code, with 'python Client.py get_balance'.
You should see something like:

```
~/git/swapbill $ python Client.py get_balance
Failed to load from cache, full index generation required (no cache file found)
State update starting from block 305846
Committed state updated to start of block 305886
In memory state updated to end of block 305906
Operation successful
balance : 0
```

For more details, troubleshooting, and to find out how to exchange between swapbill and host coin (or across blockchains),
refer to [the documentation](http://swapbill.readthedocs.org).

