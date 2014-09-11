Cross chain exchanges
===========================

So far we've looked exclusively at operations on one single blockchain, in the examples so far.
But SwapBill can be embedded in more than one blockchain, and includes support for trustless exchange of
coin *between different host blockchains*.

Working with more than one host
--------------------------------

The examples so far all use the default value for SwapBill's host parameter, which is 'bitcoin', but
all the transactions we've shown up to here can also be applied on other blockchains.

The hosts currently supported by the client are 'bitcoin' and 'litecoin'.

The following simple get_balance command will connect to a bitcoin RPC server,
and submit transactions on the bitcoin blockchain::

    ~/git/swapbill $ python Client.py get_balance

By specifying an explicit '--host' setting in the following get_balance command, however,
we can tell SwapBill to connect to a *litecoin* RPC server,
and submit transactions on the *litecoin* blockchain::

    ~/git/swapbill $ python Client.py --host litecoin get_balance

If we have both bitcoin and litecoin RPC servers running, we can work with both blockchains at the same time,
with the host set independantly for each individual client command.

SwapBill wallets are managed independantly for each host (in subdirectories in the SwapBill data directory).

Cross chain exchange support
--------------------------------

The support provided by SwapBill for cross chain exchange is less extensive, currently,
than support for exchanges between swapbill and host coin on the same blockchain.

When exchanging between swapbill and host coin on the same blockchain,
buy and sell offer books and offer management is included in the SwapBill protocol,
the backer mechanism enables us to provide single transaction exchanges in both directions,
and deposits are paid in case of failure to complete exchanges.

In the case of cross chain exchanges, the two parties wanting to exchange need to use
some external mechanism (outside of the SwapBill protocol) to find each other and agree on a suitable rate of exchange.

And then, these two parties each depend on the other party to actually go forward and complete the exchange.
The exchange mechanism is 'atomic' in that both parties are protected from losing their coin,
but it's possible for either of the parties to 'bail out' of the exchange without any loss of deposit,
and in this case the other party may suffer the inconvenience of their part of the exchange being locked up for a specified
period of time (depending on the parameters chosen for the exchange) before these funds are finally refunded.

Pay on reveal secret
-----------------------

The cross chain exchange mechanism is based on a fairly straightforward fundamental mechanism,
a special version of the 'pay' transaction which only actually pays the destination adress on condition
that a specified secret is revealed.

You can submit this special case of pay transaction as follows::

    ~/git/swapbill $ python Client.py pay --amount 0.1 --toAddress mibcs5rAjrw4Xmb6MSZKQgxURVVrja1Qjt --blocksUntilExpiry 100 --onRevealSecret
    ...
    attempting to send PayOnRevealSecret, change output address=mj3fuoJ25dETSUmjWv7i3fBj3rVK1URGRA, destination output address=mibcs5rAjrw4Xmb6MSZKQgxURVVrja1Qjt, amount=10000000, maxBlock=279703, secretAddress=mwjUEa9CJhKGhjLBFLzBwKcDDyGdzNQsc6
    Operation successful
    transaction id : 713e7047fb2c1fe080c244fa7ca4da74eb9fa06ad576d0bf2cb62dd6137f19bf

This won't pay the destination address straight away, but will instead create a pending payment.
The current set of pending payments can then be queried with the get_pending_payments command::

    ~/git/swapbill $ python Client.py get_pending_payments
    ...
    Operation successful
    pending payment index : 1
        paid by me : True
        I hold secret : True
        blocks until expiry : 100
        amount : 0.1
        paid to me : True
        confirmations : 1
        expires on block : 279703

In the 'pay' command SwapBill created a secret for you, and keeps track of this in a separate 'secrets wallet'.

If you have the secret for a pending payment, you can use the reveal_secret_for_pending_payment command to reveal this secret and force the payment to complete::

    ~/git/swapbill $ python Client.py reveal_secret_for_pending_payment --pendingPaymentID 1
    ...
    attempting to send RevealPendingPaymentSecret, pendingPayIndex=1, publicKeySecret=b'7Cg\xdc\x16\x16\xbc\xde\xdb%\xff\x0b\x89>F.\xf3p\xf8\xb1\xdf\xa0_\xdb\x13\x10\xc1r\xfc\xc3R\xea\x03\xf4+\xb7\x18\xd7\xafX\xf5\xc6\x9f\xdd/\xc5\xb8*.;\x83\x88\x17\x0c\xb9]\xabq(\xc8\x98\xdaJo'
    Operation successful
    transaction id : e9ff101d0046edf4a65b4bb0916d8d6b430e265856a68208c0aa5a69216807e5

Payment on someone else's secret
----------------------------------

It's also possible to make a payment dependant on *someone else's* secret being revealed, with the counter_pay command::

    ~/git/swapbill $ python Client.py counter_pay --help
    usage: SwapBillClient counter_pay [-h] --amount AMOUNT --toAddress TOADDRESS
                                      [--blocksUntilExpiry BLOCKSUNTILEXPIRY]
                                      --pendingPaymentHost {bitcoin,litecoin}
                                      --pendingPaymentID PENDINGPAYMENTID

    optional arguments:
      -h, --help            show this help message and exit
      --amount AMOUNT       amount of swapbill to be paid, as a decimal fraction
                            (one satoshi is 0.00000001)
      --toAddress TOADDRESS
                            pay to this address
      --blocksUntilExpiry BLOCKSUNTILEXPIRY
                            if the transaction takes longer than this to go
                            through then the transaction expires (in which case no
                            payment is made and the full amount is returned as
                            change)
      --pendingPaymentHost {bitcoin,litecoin}
                            host blockchain for target payment, can currently be
                            either 'litecoin' or 'bitcoin'
      --pendingPaymentID PENDINGPAYMENTID
                            the id of the pending payment, on the specified
                            blockchain

This does essentially the same as the pay transaction shown above (with '--onRevealSecret'),
but with the difference being that, in this case, instead of generating a secret,
the counter_pay command makes the payment dependant on *the same secret* as another pending payment.

The '--pendingPaymentHost' and '--pendingPaymentID' are used to specify which pending payment the secret should be taken from.
Importantly, the host blockchain for the pending payment that is referenced in this way can be specified independantly
of the payment being submitted.

Secrets watch list
---------------------

When you make a submit a counter_pay action, SwapBill also adds the secret to a watch list.
If that secret is revealed, subsequently, during block chain synchronisation, SwapBill will then add this secret to your secrets wallet.

Putting it together
--------------------

Let's put all the above together, then, and see how this can be used for cross chain exchange.

We'll simulate two parties for the exchange by setting up separate SwapBill data directories for each party::

    ~/git/swapbill $ mkdir a
    ~/git/swapbill $ python Client.py --dataDir a get_balance
    Failed to load from cache, full index generation required (no cache file found)
    State update starting from block 278805
    Committed state updated to start of block 279587
    In memory state updated to end of block 279607
    Operation successful
    balance : 0
    ~/git/swapbill $ mkdir b
    ~/git/swapbill $ python Client.py --dataDir b get_balance
    Failed to load from cache, full index generation required (no cache file found)
    State update starting from block 278805
    Committed state updated to start of block 279587
    In memory state updated to end of block 279607
    Operation successful
    balance : 0

Initial balances
--------------------

The two parties for the exchange will need 'bitcoin swapbill' and 'litecoin swapbill' to exchange.
(To exchange 'native' bitcoin and litecoin, these should first be converted into 'bitcoin swapbill' and 'litecoin swapbill' with the on-chain
exchange mechanisms described in the previous examples.)

For this example we'll give **a** a balance of 3.5 bitcoin swapbill, and **b** a balance of 350 litecoin swapbill, which they then want to exchange.

For **a**::

    ~/git/swapbill $ python Client.py --dataDir a get_receive_address
    ...
    Operation successful
    receive_address : mhjZL4K111nP6UPxait6jFpQfEAdoKVwVi
    ~/git/swapbill $ python Client.py pay --toAddress mhjZL4K111nP6UPxait6jFpQfEAdoKVwVi --amount 3.5
    ...
    attempting to send Pay, change output address=n4UDtohgBFWwtEyJnSSQuyA5ZEcGdf5Tq5, destination output address=mhjZL4K111nP6UPxait6jFpQfEAdoKVwVi, amount=350000000, maxBlock=279616
    Operation successful
    transaction id : 90b85732f46a85c4c51bdf917903ed747dfa0ba7bb01250acbcb708217529385
    ~/git/swapbill $ python Client.py --dataDir a get_balance -i
    ...
    Operation successful
    balance : 3.5

And for **b**::

    ~/git/swapbill $ python Client.py --dataDir b --host litecoin get_receive_address
    ...
    Operation successful
    receive_address : mnuKWDoH4wME5YdRQy6xM2y42QsHkCK4Fi
    ~/git/swapbill $ python Client.py --host litecoin pay --toAddress mnuKWDoH4wME5YdRQy6xM2y42QsHkCK4Fi --amount 350
    ...
    attempting to send Pay, change output address=n2qKD4wDo1Cp7f2pd1NXMhv9rhwyaxVREq, destination output address=mnuKWDoH4wME5YdRQy6xM2y42QsHkCK4Fi, amount=35000000000, maxBlock=383175
    Operation successful
    transaction id : c0578cfcf768043b6711d7c2730a1c86f35021870c4e76d60c04f1043448e704
    ~/git/swapbill $ python Client.py --dataDir b --host litecoin get_balance -i
    ...
    Operation successful
    balance : 350

For this to work, note that we need *both* litecoind *and* bitcoind running and set up as RPC servers.
(See :doc:`/hostsetup`.)

We used payments from the default swapbill wallet, in each case, but you could also use burn transactions or exchanges to
create these initial balances.

Procedure for exchange
------------------------

The basic procedure for the exchange will be as follows:

* **a** creates a litecoin swapbill receive address and sends this to **b**
* **b** creates a bitcoin swapbill receive address and sends this to **a**
* **a** submits a pay on reveal secret transaction (to **b**'s receive address), with quite a long time until expiry
* **b** checks the details for this payment, and makes sure this is confirmed, and then, if everything is ok, submits a counter_pay transaction (to **a**'s receive address), with a much shorter time until expiry
* both payments are now dependant on the same secret, which is currently known only to **a**
* **a** can now submit a reveal secret transaction, enabling the counter_pay to go through
* **b** then obtains the secret (during a subsequent syncronisation), and can submit a reveal secret transaction to enable the first payment to go through

Let's see how this works out, though, in concrete SwapBill client invocations..

Generate receive addresses
----------------------------

The parties generate receive addresses (and send these to each other)::

    ~/git/swapbill $ python Client.py --dataDir a --host litecoin get_receive_address
    ...
    Operation successful
    receive_address : n3QncHC6iAGPo5G4bFNZ9BeAfcb5KWAaEq
    ~/git/swapbill $ python Client.py --dataDir b get_receive_address
    ...
    Operation successful
    receive_address : mu9uDM3r571d198iaqznBfZFEtHfxCEpDA


First payment, **a** to **b**
-------------------------------

**a** submits a first pay on reveal secret transaction::

    ~/git/swapbill $ python Client.py --dataDir a pay --amount 3.5 --toAddress mu9uDM3r571d198iaqznBfZFEtHfxCEpDA --onRevealSecret --blocksUntilExpiry 18
    Loaded cached state data successfully
    State update starting from block 279597
    Committed state updated to start of block 279597
    in memory: Pay
     - 3.5 swapbill output added
    In memory state updated to end of block 279617
    attempting to send PayOnRevealSecret, change output address=n1YrUfwjZkKPjgpVViuBzaTtTahjWBwtwE, destination output address=mu9uDM3r571d198iaqznBfZFEtHfxCEpDA, amount=350000000, maxBlock=279636, secretAddress=mnMx4UJMUkdKw1drYXqG3N9SfoynSymbsV
    Operation successful
    transaction id : db7913fda875b3dbf94f1a09e272f0d2279175be27b3133a3f97f4b45ce63828

Note that we specified 18 for '--blocksUntilExpiry' here, which, based on approximately 10 minutes per block for bitcoin,
works out at approximately 3 hours.

A different number could be used here, but:

* This needs to allow plenty of time for **b** to set up a counter payment, with shorter expiry period, and checks for a certain number of confirmations.
* If **b** doesn't play ball, and doesn't move forward with their part of the exchange, **a**'s swapbill will be locked up until the end of this expiry period.

**b** checks this payment::

    ~/git/swapbill $ python Client.py --dataDir b get_pending_payments
    ...
    Operation successful
    pending payment index : 2
        paid to me : True
        confirmations : 1
        paid by me : False
        expires on block : 279636
        blocks until expiry : 17
        amount : 3.5

but then waits until the payment has a reasonable number of confirmations before making a counter payment.

Counter payment, **b** to **a**
-------------------------------

Once **b** is satisfied that there are enough confirmations for the first payment
(and confident that this first payment won't be backed out by a blockchain reorganisation), **b** proceeds with the counterpayment, as follows::

    ~/git/swapbill $ python Client.py --dataDir b --host litecoin counter_pay --amount 350 --toAddress n3QncHC6iAGPo5G4bFNZ9BeAfcb5KWAaEq --blocksUntilExpiry 36 --pendingPaymentHost bitcoin --pendingPaymentID 2
    ...
    attempting to send PayOnRevealSecret, change output address=mzy6QnsqiQjFAritKoqKUGvRyeJuy7bo1J, destination output address=n3QncHC6iAGPo5G4bFNZ9BeAfcb5KWAaEq, amount=35000000000, maxBlock=383216, secretAddress=mnMx4UJMUkdKw1drYXqG3N9SfoynSymbsV
    Operation successful
    transaction id : cbcbfdbf6d1d60750bfe4f2eed07cdf7abfcfadf9d87e765e9a5de9f151a1df3

The value of 36 for '--blocksUntilExpiry' here, based on approximately 2.5 minutes per block for litecoin,
works out at approximately 1.5 hours.

This expiry delay needs to be:
* long enough to give **a** enough time to accept the counter payment (including waiting for enough confirmations), but
* short enough that, even if **a** waits until this is nearly expired before accepting, **b** still has plenty of time to accept the first payment.

**a** checks this counter payment::

    ~/git/swapbill $ python Client.py --dataDir a --host litecoin get_pending_payments
    ...
    Operation successful
    pending payment index : 3
        blocks until expiry : 36
        paid to me : True
        confirmations : 1
        amount : 350
        paid by me : False
        I hold secret : True
        expires on block : 383216

Note that both 'paid to me' and 'I hold secret' show True, which shows that **a** can now go ahead and accept this counter payment.

Counter payment accepted by **a**
----------------------------------

Once **a** is satisfied that there are enough confirmations for the counterpayment, **a** goes ahead and reveals the secret, to accept this::

    ~/git/swapbill $ python Client.py --dataDir a --host litecoin reveal_secret_for_pending_payment --pendingPaymentID 3
    ...
    attempting to send RevealPendingPaymentSecret, pendingPayIndex=3, publicKeySecret=b'\xa5D\xa5q\xa5\x7f\x12\x92^\x02\x91\x01\xcc\x023@\xae\xc5\x04\xe9o!\xd09\xe2\x8d~<B.\xeebr\x9fZ\x95\xf3\xb9c\x05\xd8Ia>\xfd2\xd1z\xba=\x1eu\xf7\xa1\x88ox\xe9\xb4\x1bv\x81\xe0\x0f'
    Operation successful
    transaction id : 38fa2ab46a26466d2b31e0921e4e76858655e4736565d4c98dc9925099cce955

The counterpayment goes through, and **a** receives the litecoin part of the exchange::

    ~/git/swapbill $ python Client.py --dataDir a --host litecoin get_balance
    ...
    Operation successful
    balance : 350

But, for this, **a** was forced to reveal their secret.

First payment completed by **b**
----------------------------------

When **b** next synchronises, this secret is detected and added to their secrets wallet::

    ~/git/swapbill $ python Client.py --dataDir b --host litecoin get_balance
    Loaded cached state data successfully
    State update starting from block 383159
    Committed state updated to start of block 383160
    ...
    in memory: storing revealed secret with hash 4b14f0fc03d9aca2509688e3da04678bc418aad1
    In memory state updated to end of block 383181
    Operation successful
    balance : 0

And, if we now check the status for the first payment, on the bitcoin blockchain::

    ~/git/swapbill $ python Client.py --dataDir b get_pending_payments
    ...
    Operation successful
    pending payment index : 2
        paid by me : False
        paid to me : True
        I hold secret : True
        blocks until expiry : 15
        confirmations : 3
        amount : 3.5
        expires on block : 279636

We can see that **b** is now able to complete this payment, as follows::

    ~/git/swapbill $ python Client.py --dataDir b reveal_secret_for_pending_payment --pendingPaymentID 2
    ...
    attempting to send RevealPendingPaymentSecret, pendingPayIndex=2, publicKeySecret=b'\xa5D\xa5q\xa5\x7f\x12\x92^\x02\x91\x01\xcc\x023@\xae\xc5\x04\xe9o!\xd09\xe2\x8d~<B.\xeebr\x9fZ\x95\xf3\xb9c\x05\xd8Ia>\xfd2\xd1z\xba=\x1eu\xf7\xa1\x88ox\xe9\xb4\x1bv\x81\xe0\x0f'
    Operation successful
    transaction id : d2c9d58948e23a21d655d89c1de7d2688a97e6360409a0e839f91ba97054d55c

And **b** receives the bitcoin part of the exchange::

    ~/git/swapbill $ python Client.py --dataDir b get_balance
    ...
    in memory: RevealPendingPaymentSecret
    In memory state updated to end of block 279622
    Operation successful
    balance : 3.5
