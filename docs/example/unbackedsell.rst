Unbacked sell transactions
===========================

In addition to the backed litecoin sell offers, it's also possible to make *unbacked* sell offers.

The key differences between the two types of sell offer are that:

* some initial swapbill is required in order to make an unbacked sell offer
* in the case of an unbacked sell offer, it is up to the seller to make final completion payments for each trade offer match
* a deposit is payed in to unbacked sell offers, and will be lost if the final completion payment is not made (e.g. if your internet goes down, or something like this!)
* backed sells only require one transaction from the seller, and there is no risk to the seller after that transaction has gone through
* backed sells are based on a lump sum committed to the SwapBill protocol by the backer, however, and then only guarantee offers up to a maximum number of transactions, and there is a theoretical possibility for lots of transactions to come through an consume all of the backer amount
* some commission is payable to the backer for each backed sell offer
* unbacked sells have an expiry period, which can be set when you make the offer
* backed sells never expire

Roughly speaking, backed ltc sells are good for smaller transactions, and are the best way to obtain swapbill initially,
but for larger transactions, and if you can be confident about being able to submit completion transactions
(e.g. if you have a backup internet connection!) then unbacked sells can be preferrable.

To make an unbacked sell offer we start with a sell_offer action, as before, but in this case we *don't* specify a value for backerID
(and so don't need to check for backers and backer details).

Our seller starts with some swapbill::

    ~/git/swapbill $ python Client.py get_balance
    ...
    Operation successful
    balance : 3.00531212

Checking buy offers
--------------------

As before, we check the current set of buy offers::

    ~/git/swapbill $ python Client.py get_buy_offers
    ...
    Operation successful
    exchange rate : 0.92
        swapbill offered : 0.92211766
        host coin equivalent : 0.84834825
        mine : False
    exchange rate : 0.95
        swapbill offered : 2
        host coin equivalent : 1.9
        mine : False

Sell offer
-----------------

Let's try and match the top offer::

    ~/git/swapbill $ python Client.py sell_offer --hostCoinOffered 0.84834825 --exchangeRate 0.92
    ...
    attempting to send SellOffer, hostCoinSell output address=moyQMZZDDfS4jGARJojCFY62Lcc8CMuYYY, exchangeRate=920000000, hostCoinOffered=84834825, maxBlock=279595
    Operation successful
    transaction id : bd4906dc3f85bbc670290e804ed59b0275a9aec7f25aef6940cc56976400a226

This goes through successfully, and we can see that the buy offer has been matched::

    ~/git/swapbill $ python Client.py get_buy_offers
    ...
    in memory: SellOffer
     - 3.00531212 swapbill output consumed
     - 2.94767976 swapbill output added
    In memory state updated to end of block 279593
    Operation successful
    exchange rate : 0.95
        mine : False
        host coin equivalent : 1.9
        swapbill offered : 2

A deposit proportional to the amount of swapbill we are looking to exchange has been taken from our current balance, but also a
seed amount equivalent to the minimum balance protocol constraint (currently set to 0.001 for bitcoin swapbill)::

    ~/git/swapbill $ python Client.py get_balance
    ...
    Operation successful
    balance : 2.96535406

Now it is up to us to complete.
We can see the pending exchange with get_pending_exchanges::

    ~/git/swapbill $ python Client.py get_pending_exchanges
    ...
    Operation successful
    pending exchange index : 4
        deposit paid by seller : 0.05763236
        expires on block : 279608
        swap bill paid by buyer : 0.92211766
        outstanding host coin payment amount : 0.84834825
        I am seller (and need to complete) : True
        I am buyer (and waiting for payment) : False
        confirmations : 1
        blocks until expiry : 15

We should wait for a few more blocks to go through before completing the exchange, in case of blockchain reorganisation.

(We can ignore the issue of blockchain reorganisation to a large extent for a lot of other 'single transaction' actions,
but this is something we need to be more careful about specifically in the case completion transactions.
In the case of backed sells this is something that backers normally have to worry about for you!)

Once we're happy with the number of comfirmations for our pending exchange, the actual completion transaction is then very straightforward::

    ~/git/swapbill $ python Client.py complete_sell --pendingExchangeID 4
    ...
    attempting to send ExchangeCompletion, destinationAddress=n25vgZ5ahLxmM7YujMmRnFGVPUTZA6aooL, destinationAmount=84834825, pendingExchangeIndex=4
    Operation successful
    transaction id : ca7a712cb8746122aa55f2b49a298099a4b4f1927375cf67e85b62486b2b1421

Once this transaction has gone through we're refunded the deposit, and the seed amount,
and credited the swapbill amount corresponding to our exchange::

    ~/git/swapbill $ python Client.py get_balance
    in memory: ExchangeCompletion
     - trade offer updated
    Operation successful
    balance : 3.94510408

