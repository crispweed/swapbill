Pay transactions
===================

To make a payment in swapbill, we use the 'pay' action.

As with native bitcoin and litecoin payments,
the payment recipient must first generate a target address for the payment,
and we can do this with the 'get_receive_address' action::

    ~/git/swapbill $ python Client.py get_receive_address
    ...
    Operation successful
    receive_address : mzBfgH8vLf9EAo4yvJz1UieXqb9jX8YzUs

This is actually just a standard address in the same format as you would use for the host blockchain,
but the client manages this address independantly of bitcoind
(see :doc:`/walletorganisation`), and uses this address to sign SwapBill outputs.

Just as with other altcoin wallets, the client and will detect any SwapBill outputs paying to this address and add the corresponding swapbill amounts to your balance.

To pay some swapbill in to this address::

    ~/git/swapbill $ python Client.py pay --amount 0.1 --toAddress mzBfgH8vLf9EAo4yvJz1UieXqb9jX8YzUs
    Loaded cached state data successfully
    State update starting from block 279379
    Committed state updated to start of block 279379
    In memory state updated to end of block 279399
    attempting to send Pay, change output address=n319WGe5egQi3WRAxJ3RKAHFSafEvMSGxd, destination output address=mzBfgH8vLf9EAo4yvJz1UieXqb9jX8YzUs, amount=10000000, maxBlock=279408
    Operation successful
    transaction id : b3fb87e0750e572ad3b7407f4d1ddfa829afd7ef3da7872dd744499ae2b03307

Working with multiple wallets
-----------------------------

In this case we're actually just paying ourselves.
It's also possible to manage multiple swapbill wallets independantly, by changing the client data directory,
and to use this to try out transactions between different wallet 'owners'.

First, let's create a new SwapBill wallet 'owner' (corresponding to an alternative SwapBill data directory)::

    ~/git/swapbill $ mkdir alice
    ~/git/swapbill $ python Client.py --dataDir alice get_receive_address
    Failed to load from cache, full index generation required (no cache file found)
    ...
    Operation successful
    receive_address : n4M62XjmWCS9qhKCzaPDoKYmicAVVXoyGS

Note that you need to create the new data directory before invoking the client. The client won't create this directory for you.

And now we can pay 'alice' from the default wallet:

    ~/git/swapbill $ python Client.py -pay --amount 0.1 --toAddress mmdAwus4b6chWzvRtNVcL2YfxvWTeWUcq3

In this case, the default wallet owner is debited the swapbill payment amount, and this is credited to 'alice'.

Waiting for change to clear
----------------------------

If you try the examples posted here directly after the previous 'burn' transaction examples there should be enough funds available for both of these pay transactions.

If you get an error ``Operation failed: Insufficient swapbill for transaction.`` this may mean that you need to wait for a previous
transaction to be confirmed, in order for the change from that transaction to become available for spending once again.
(This works in exactly the same way as native bitcoin transactions, and exactly the same issue occurs there.)

You can check the amount actually available to spend at any one instant with ``python Client.py get_balance``.

If you add the -i option to this query, so ``python Client.py get_balance -i``, this tells you how much *will have available*
after all pending transactions (in the bitcoind memory pool) have cleared.

(The -i option just means 'include memory pool'.)

If ``get_balance`` doesn't show enough funds for a transaction, but ``get_balance -i`` does, then you just need to wait
for your memory pool transactions to go through.
