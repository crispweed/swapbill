Buy transactions
===================

Ok, so we've looked at how to get hold of some swapbill, either through a backed exchange, or by burning host coin.

SwapBill is intended to serve a fairly specific purpose, however, (for facilitating decentralised cross currency exchange, specifically),
and when you've finished using your swapbill you will most likely want to exchange this back for host currency.

You can do this with the buy offer transaction (buying host coin with swapbill).
The process for this is similar to backed sell offers, but even more straightforward, because there's no need to select a backer in this case.

Checking sell offers
----------------------

Starting with a buyer, who has 1.5 swapbill they want to exchange for host coin::

    ~/git/swapbill $ python Client.py get_balance
    ...
    Operation successful
    balance : 1.5

Let's check the current list of sell offers::

    ~/git/swapbill $ python Client.py get_sell_offers
    ...
    Operation successful
    exchange rate : 0.91
        host coin offered : 0.9
        deposit : 0.06181319
        swapbill equivalent : 0.98901099
        mine : False
    exchange rate : 0.88
        host coin offered : 1
        deposit : 0.07102273
        swapbill equivalent : 1.13636364
        mine : False

Matching the top offer
------------------------

The best rate here is 0.91 host coin per swapbill.
Let's assume we're ok with exchanging at anything down to 0.9 host coin per swapbill.
So, we'll try and match that top offer first::

    ~/git/swapbill $ python Client.py buy_offer --swapBillOffered 0.98901099 --blocksUntilExpiry 1 --exchangeRate 0.91
    ...
    attempting to send BuyOffer, hostCoinBuy output address=mijmaJQvuLdpbXNqx5MRz6qnTUTZALK2Qy, exchangeRate=910000000, maxBlock=279588, receivingAddress=myxz78GA8zBmAbwtqN6qEhEwgE2f1tBjEY, swapBillOffered=98901099
    Operation successful
    transaction id : 34be36f0bdb7f165838bb1210f0eaf0aa8a91416a6f4c38e0b3431088ebbdf5f

This is similar to the sell offer we posted in the previous example, but there a couple of other points to note here.

First of all, note that we've specified a value for blocksUntilExpiry.
This is because we just want to match the top existing offer, but there is a possibility that someone else matches that offer first.
So we've set our transaction to expire in the next block, if it doesn't match, so that we can then go on and use the swapbill in another offer without having to wait too long.

A second point to note is that the decimal fractions displayed by queries such as get_sell_offers, and passed in for transaction parameters are
actually *exact* values, and not subject to approximation errors during parsing or display.
So we can copy the exact text printed for the top sell offer and expect our offer to match this exactly.
(This is a subtle point, but nevertheless quite an important implementation detail!)

No other offers come in before our buy offer, then, and this matches the top offer.

The amount offered is debited from our balance::

    ~/git/swapbill $ python Client.py get_balance
    ...
    Operation successful
    balance : 0.51098901

And we can see that the top sell offer has been removed::

    ~/git/swapbill $ python Client.py get_sell_offers
    ...
    in memory: BuyOffer
     - 1.5 swapbill output consumed
     - 0.51098901 swapbill output added
    In memory state updated to end of block 279587
    Operation successful
    exchange rate : 0.88
        deposit : 0.07102273
        swapbill equivalent : 1.13636364
        host coin offered : 1
        mine : False

Posting a speculative offer
----------------------------

We decide to post the remaining funds again, in another buy offer::

    ~/git/swapbill $ python Client.py --buy_offer --swapBillOffered 0.51098901 --exchangeRate 0.9
    ...
    attempting to send BuyOffer, hostCoinBuy output address=mo8ACE96HGVUfrthq4u1g4nZCZTB94jEuS, exchangeRate=900000000, maxBlock=279596, receivingAddress=mzaY6QqQxYtcCC1vJc19nxBet9f6frzsRs, swapBillOffered=51098901
    Operation successful
    transaction id : 98998855e17ffec7a63e9342981d4fad8f5acc97f4ae51dd27915479ac20863e

Again, note that we can post the exact current balance value, and the client will then include the whole balance in the offer.
Remember that the SwapBill protocol includes a minimum balance constraint, so we're not permitted to submit transactions that would leave a very small amount of change.
(If so, the client will report an error, and refuse to submit the transaction. Try spending very slightly less than your current balance,
to see this in practice.)

In this case we didn't specify blocksUntilExpiry.
For buy transactions this currently defaults to 8.
For backed sell transactions there is no expiry and for
unbacked sells the default is just 2 blocks (because unbacked sells need to be followed up with exchange completion for each matching buyer).

This offer doesn't match any existing sell offer, and is therefore added to the existing order book as an outstanding offer::

    ~/git/swapbill $ python Client.py get_buy_offers
    ...
    Operation successful
    exchange rate : 0.9
        swapbill offered : 0.51098901
        host coin equivalent : 0.45989011
        mine : True
    exchange rate : 0.92
        swapbill offered : 0.92211766
        host coin equivalent : 0.84834825
        mine : False
    exchange rate : 0.95
        swapbill offered : 2
        host coin equivalent : 1.9
        mine : False

If no-one posts a matching offer before the end of the expiry period, the swapbill amount offered will be returned to our active balance.
But, as it is, a couple of sell offers come along in the next few blocks, and match the outstanding offer remainder.

We can see the SellOffer transactions come up in the sync output, and we can also see that the buy offer has been matched
and is no longer present::

    ~/git/swapbill $ python Client.py get_buy_offers
    Loaded cached state data successfully
    State update starting from block 279570
    ...
    in memory: SellOffer
     - trade offer updated
    in memory: SellOffer
     - trade offer updated
    In memory state updated to end of block 279591
    Operation successful
    exchange rate : 0.92
        swapbill offered : 0.92211766
        host coin equivalent : 0.84834825
        mine : False
    exchange rate : 0.95
        swapbill offered : 2
        host coin equivalent : 1.9
        mine : False

It turns out that our second offer was actually matched by two smaller sell offers.
And so at this point, we now have three trade offer matches outstanding, waiting for final host coin payments
from the seller to complete.

We can see this with the get_pending_exchanges query::

    ~/git/swapbill $ python Client.py get_pending_exchanges
    ...
    Operation successful
    pending exchange index : 1
        swap bill paid by buyer : 0.98901099
        I am buyer (and waiting for payment) : True
        deposit paid by seller : 0.06181319
        I am seller (and need to complete) : False
        expires on block : 279602
        blocks until expiry : 12
        confirmations : 4
        outstanding host coin payment amount : 0.9
    pending exchange index : 2
        swap bill paid by buyer : 0.33333333
        I am buyer (and waiting for payment) : True
        deposit paid by seller : 0.02083334
        I am seller (and need to complete) : False
        expires on block : 279605
        blocks until expiry : 15
        confirmations : 1
        outstanding host coin payment amount : 0.3
    pending exchange index : 3
        swap bill paid by buyer : 0.17765568
        I am buyer (and waiting for payment) : True
        deposit paid by seller : 0.01110348
        I am seller (and need to complete) : False
        expires on block : 279606
        blocks until expiry : 15
        confirmations : 1
        outstanding host coin payment amount : 0.15989011

As a host coin buyer, we don't have to take any action here.
Either the seller pays the required host coin amount and completes the exchange,
or we are refunded our swapbill plus some deposit paid by the seller as part of their sell offer.

A bit later we can see that one of the exchanges has been completed::

    ~/git/swapbill $ python Client.py get_pending_exchanges
    ...
    Operation successful
    pending exchange index : 1
        blocks until expiry : 11
        confirmations : 5
        I am seller (and need to complete) : True
        I am buyer (and waiting for payment) : False
        expires on block : 279602
        deposit paid by seller : 0.06181319
        swap bill paid by buyer : 0.98901099
        outstanding host coin payment amount : 0.9
    pending exchange index : 2
        blocks until expiry : 14
        confirmations : 2
        I am seller (and need to complete) : True
        I am buyer (and waiting for payment) : False
        expires on block : 279605
        deposit paid by seller : 0.02083334
        swap bill paid by buyer : 0.33333333
        outstanding host coin payment amount : 0.3

You can check your host coin balance separately, with ``bitcoin/src/bitcoin-cli getbalance``,
to confirm that you've received the host coin amount for this exchange.
(The SwapBill client verifies that the payment transaction is received, but does not track your host coin balance.)

