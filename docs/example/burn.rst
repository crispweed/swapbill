Burn transactions
===================

SwapBill allows you to create swapbill by burning host coin.
(See :doc:`/currencysupply`.)

This is not the recommended way to obtain swapbill,
but it's an important part of the SwapBill protocol definition,
so let's see how this works!

Assuming you have sufficient host coin, a burn transaction can be submitted as follows::

    ~/git/swapbill $ python Client.py burn --amount 0.5
    Loaded cached state data successfully
    State update starting from block 279288
    Committed state updated to start of block 279288
    In memory state updated to end of block 279308
    attempting to send Burn, destination output address=mhF3UNUueb4USnHJ5N9x5E67KTV9BgFDHk, amount=50000000
    Operation successful
    transaction id : ac51ac2bfbbb16912ed7423da275f9b6acae3f466eff852595f0fbb5aa6699cf

Host blockchain selection
---------------------------

Once this goes through you will have destroyed 0.5 bitcoin, but in exchange you're credited with a corresponding amount of swapbill.

The above command defaults to the bitcoin host blockchain (and requires bitcoind to be running as an RPC server),
and has the effect of burning testnet btc in exchange for bitcoin testnet swapbill,
but you can do exactly the same thing with litecoind as a backend by changing the client invocation to:::

    ~/git/swapbill $ python Client.py --host litecoin burn --amount 0.5

(In which case the client will burn 0.5 testnet ltc in exchange for 0.5 litecoin testnet swapbill!)

Throughout the examples we'll use the default host setting (bitcoin) for simplicity, but you can adapt the examples to
use litecoin as necessary.

Minimum balance constraint
---------------------------

It's worth noting at this point that the SwapBill protocol includes a constraint on the minimum amount of swapbill associated with any
given SwapBill 'account', or output. This is a financial motivation for users to minimise the number of active swapbill outputs
to be tracked, and a discouragement for 'spam' outputs.
For 'bitcoin swapbill', whe constraint is currently set to exactly 0.001 swapbill, or 100000 swapbill satoshis, and so that's the minimum amount we're allowed to burn.
If you try to burn less, the client should refuse to submit the transaction and display a suitable error message.
(For 'litecoin swapbill the minimum balance is higher, and is currently set to exactly 0.1 swapbill, or 10000000 swapbill satoshis.)

Transaction confirmation
--------------------------

By default, queries such as get_balance only report the amount actually confirmed (with at least one confirmation) by the host blockchain,
and so if we try querying this straight away, we won't see any swapbill credited yet for this burn::

    ~/git/swapbill $ python Client.py get_balance
    Loaded cached state data successfully
    State update starting from block 279288
    Committed state updated to start of block 279288
    In memory state updated to end of block 279308
    Operation successful
    balance : 0

But we can use the -i option to force the query to include pending transactions (from the bitcoind memory pool), and then we get::

    ~/git/swapbill $ python Client.py get_balance -i
    Loaded cached state data successfully
    State update starting from block 279288
    Committed state updated to start of block 279288
    In memory state updated to end of block 279308
    in memory pool: Burn
     - 0.5 swapbill output added
    Operation successful
    balance : 0.5

And then, if we wait a bit to allow the transaction to go through, we can see this as a confirmed transaction::

    ~/git/swapbill $ python Client.py get_balance
    Loaded cached state data successfully
    State update starting from block 279288
    Committed state updated to start of block 279289
    in memory: Burn
     - 0.5 swapbill output added
    In memory state updated to end of block 279309
    Operation successful
    balance : 0.5

Note that it can sometimes take a while for new blocks to be mined on the testnet blockchains (in particular with the litecoin testnet),
depending on whether anyone is actually mining this blockchain, and if no one is mining (!) it can then take a while for swapbill transactions to be confirmed.

Aside: committed and in memory transactions
--------------------------------------------

In the above output we can see different block counts for 'committed' and 'in memory' state, and it's worth taking a moment to explain this.

What's going on here is that the client commits state to disk to avoid spending time resynchronising on each invocation,
but with this committed state lagging a fixed number of blocks (currently 20) behind the actual current block chain end.

This mechanism enables the client to handle small blockchain reorganisations robustly, without overcomplicating the client code.
If there are blockchain reorganisations of more than 20 blocks this will trigger a full resynch,
but blockchain reorganisations of less than 20 blocks can be processed naturally starting from the committed state.

For transaction reporting during synchronisation:
* Transactions that are included in the persistent state cached to disk get prefixed by 'committed'.
* Transactions that are confirmed in the blockchain but not yet cached to disk get prefixed by 'in memory'. (When you run the client again, you'll normally see these transactions repeated, unless there was a blockchain reorganisation invalidating the transaction.)
* Transactions that are not yet confirmed in the blockchain, but present in the bitcoind memory pool get get prefixed with 'in memory pool'.


Better way to obtain swapbill
-------------------------------

As noted above, burning host coin is not the recommended way to get initial swapbill.
You can get a better price if you exchange host coin for swapbill, and we'll look at how to do this a bit later on..

