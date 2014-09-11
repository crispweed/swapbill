Running the client
===================

Obtaining the source code
----------------------------

The project is hosted on https://github.com/crispweed/swapbill, and so you can get the client source code with git, as follows::

    ~/git $ git clone https://github.com/crispweed/swapbill
    Cloning into 'swapbill'...
    remote: Counting objects: 52, done.
    remote: Compressing objects: 100% (41/41), done.
    remote: Total 52 (delta 9), reused 46 (delta 3)
    Unpacking objects: 100% (52/52), done.

In case you don't have git, you can also download the source code directly as an archive from https://github.com/crispweed/swapbill/archive/master.zip, extract to a new directory.

No installer
----------------------------

There's no installation process for the client and you can just run it directly
from the downloaded source tree.

You'll need to ensure that the third party python library dependencies
are met before running the client, (see :doc:`requirements`) or you'll get an error message telling you to do this.

And then you run the client with (e.g.)::

    ~/git $ cd swapbill/
    ~/git/swapbill $ python Client.py get_balance

Selecting host blockchain
---------------------------

You can use the '--host' command line option to choose the desired host blockchain to run against.
This defaults to 'bitcoin', but if you want to run against litecoind (for example if you only have litecoind installed, and not bitcoind)
then you need to change client invocation as follows:

    ~/git/swapbill $ python Client.py --host litecoin get_balance

You can change this selection per client invocation, and work with multiple host blockchains without any problems.
(This is required for the cross chain exchange functionality!)

The client maintains independent subdirectories within its data directory for each host, with separate wallet files and state cache data.

RPC errors
-----------

If you don't have bitcoind running, or if you don't have the RPC interface set up correctly, you'll see something like::

    ~/git/swapbill $ python Client.py get_balance
    Couldn't connect for remote procedure call, will sleep for ten seconds and then try again.
    Couldn't connect for remote procedure call, will sleep for ten seconds and then try again.
    (...repeated indefinitely)

But if you start the RPC server, the client should connect and complete the command from there.

If the RPC interface is working correctly you should see something like this::

    ~/git/swapbill $ python Client.py get_balance
    Failed to load from cache, full index generation required (no cache file found)
    State update starting from block 305846
    Committed state updated to start of block 305886
    In memory state updated to end of block 305906
    Operation successful
    balance : 0

Command line help
------------------

You can get some help about the full set of command line arguments for the client with '-h' or '--help'::

    ~/git/swapbill $ python Client.py -h
    usage: SwapBillClient [-h] [--dataDir DATADIR] [--host {bitcoin,litecoin}]
                          {force_rescan,burn,pay,counter_pay,buy_offer,sell_offer,complete_sell,reveal_secret_for_pending_payment,back_sells,make_seed_output,get_receive_address,get_balance,get_buy_offers,get_sell_offers,get_pending_exchanges,get_sell_backers,get_pending_payments,get_state_info}
                          ...

    the reference implementation of the SwapBill protocol

    positional arguments:
      {force_rescan,burn,pay,counter_pay,buy_offer,sell_offer,complete_sell,reveal_secret_for_pending_payment,back_sells,make_seed_output,get_receive_address,get_balance,get_buy_offers,get_sell_offers,get_pending_exchanges,get_sell_backers,get_pending_payments,get_state_info}
                            the action to be taken
        force_rescan        delete cached state, forcing a full rescan on the next
                            query invocation
        burn                destroy host coin to create swapbill
        pay                 make a swapbill payment
        counter_pay         make a swapbill payment that depends on the same
                            secret as another payment
        buy_offer           make an offer to buy host coin with swapbill
        sell_offer          make an offer to sell host coin for swapbill
        complete_sell       complete a exchange with host coin by fulfilling a
                            pending exchange payment
        reveal_secret_for_pending_payment
                            provide the secret public key required for a pending
                            payment to go through
        back_sells          commit swapbill to back exchanges with host coin
        make_seed_output    make a transaction for use as a seed output
        get_receive_address
                            generate a new key pair for the swapbill wallet and
                            display the corresponding public payment address
        get_balance         get current SwapBill balance
        get_buy_offers      get list of currently active host coin buy offers
        get_sell_offers     get list of currently active host coin sell offers
        get_pending_exchanges
                            get current SwapBill pending exchange payments
        get_sell_backers    get information about funds currently commited to
                            backing host coin sell transactions
        get_pending_payments
                            get information payments currently pending proof of
                            receipt
        get_state_info      get some general state information

    optional arguments:
      -h, --help            show this help message and exit
      --dataDir DATADIR     the location of the data directory
      --host {bitcoin,litecoin}
                            host blockchain, can currently be either 'litecoin' or
                            'bitcoin'

And then, you can get help about individual commands by passing '-h' (or '--help') right after the command::

    ~/git/swapbill $ python Client.py burn -h
    usage: SwapBillClient burn [-h] --amount AMOUNT

    optional arguments:
      -h, --help       show this help message and exit
      --amount AMOUNT  amount of host coin to be destroyed, as a decimal fraction
                       (one satoshi is 0.00000001)

Worked examples
------------------

The best way to understand what the main commands do is to go through the various examples
provided later on in this documentation.
