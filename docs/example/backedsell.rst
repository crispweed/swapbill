Backed sell transactions
=========================

A backed sell transaction enables you to sell host currency for swapbill (to obtain some initial swapbill, for example), with just one single sell offer transaction.

Backed sell transactions are actually the recommended way to obtain some initial swapbill, in preference to burn transactions.

As with burn transactions, no swapbill balance is required in order to make a backed sell offer,
but this does depend on some backing amount having already been committed by a third party, and some commission is payable to the backer for these transactions.

(Because commission is paid to backer, with the rate of commission subject to market forces, *if* there is swapbill available for exchange then there *should* be backers available,
otherwise this is an indication that swapbill supply is insufficient, and so creating more swapbill by burning is appropriate!)

Checking backers
-----------------

You can use the 'get_sell_backers' action to check if there are backers available,
and to find out information about the backers such as rate of commission being charged, as follows::


    ~/git/swapbill $ python Client.py get_sell_backers
    ...
    Operation successful
    host coin sell backer index : 0
        I am backer : False
        transactions covered : 1000
        backing amount : 190
        blocks until expiry : 29865
        maximum exchange swapbill : 0.17788235
        backing amount per transaction : 0.19
        expires on block : 309437
        commission : 0.005

The key values to look at are 'commission' and 'transactions covered'.

The commission value here indicates that 0.5% commission is payable to the backer on the amount of host coin offered for sale.

The 'transactions covered' value is calculated based on 'backing amount' and 'backing amount per transaction',
and this tells us how many transactions (at a minimum) can be guaranteed by the current backing amount,
and therefore how safe it is to use this backer for sell transactions.

The backed trade mechanism works by backers committing funds to guarantee trades for a certain number of transactions in advance.

If we submit a sell transaction using this backer, and then 1000 other valid trade transactions to the same backer
(all using the maximum allowed backing amount)
all come through on the blockchain
in between this backer query and our sell transaction,
then it's possible that our transaction does not get backed, and we lose the host coin amount paid in to our sell transaction.

As long as our sell transaction comes through to the blockchain with *less than* 1000 other transactions
to the same backer in between, however, SwapBill uses the funds committed by the backer to guarantee our exchange.

Lets go ahead and exchange some host coin for swapbill, through this backer.

Listing buy offers
-------------------

The next step is to check the buy offers currently posted to the blockchain, to get an idea of the current exchange rate::

    ~/git/swapbill $ python Client.py get_buy_offers
    ...
    Operation successful
    exchange rate : 0.92
        mine : True
        swapbill offered : 1.1
        host coin equivalent : 1.012
    exchange rate : 0.95
        mine : True
        swapbill offered : 2
        host coin equivalent : 1.9

The best offer comes first, with 1.1 swapbill offered at an exchange rate of 0.92 host coin per swapbill.

Let's assume we're ok with making an exchange at this rate.

Maximum exchange with rate
---------------------------

As we saw above, each backer has a maximum backing amount per individual transaction.

This is important in order to prevent a single transaction using all of the backing amount,
and to provide some solid guarantees about the number of transactions that can be backed.
But it also means that there is a maximum amount we can exchange through the backer in any one transaction.

The get_sell_backers query above gave us a 'maximum exchange swapbill' value, which specified the maximum amount
which can be exchanged, specified in swapbill, but we're going to need to specify an amount in host coin in our sell transaction.

We could get out a calculator, and work this out, but it's easier to let the get_sell_backers query do this for us::

    ~/git/swapbill $ python Client.py get_sell_backers --withExchangeRate 0.92
    ...
    Operation successful
    host coin sell backer index : 0
        backing amount : 190
        maximum exchange swapbill : 0.17788235
        transactions covered : 1000
        expires on block : 309437
        maximum exchange host coin : 0.16365176
        commission : 0.005
        backing amount per transaction : 0.19
        I am backer : False
        blocks until expiry : 29863

So the maximum amount if host coin we can exchange through this backer in a single transaction,
at an exchange rate of 0.92 host coin per swapbill, is 0.16365176.

Backed sell transaction
------------------------

After checking that we have enough funds available in our host coin wallet::

    ~/git $ bitcoin/src/bitcoin-cli getbalance
    2.98189956

We can go ahead and submit our backed sell transaction as follows::

    ~/git/swapbill $ python Client.py sell_offer --hostCoinOffered 0.16365176 --exchangeRate 0.92 --backerID 0
    ...
    attempting to send BackedSellOffer, sellerReceive output address=n4WPsVHA3pdAjmDpfZy6dxZ6pigDgEBws7, backerHostCoinReceiveAddress=msdaZFHTJAEm841SxzUez4ip7SSVxEx9vF, backerIndex=0, exchangeRate=920000000, hostCoinOfferedPlusCommission=16447001
    Operation successful
    transaction id : 4704f8b40446c123bb2a715abaa3f100f99cd499886a529216904053361ba175

Note that this transaction doesn't need *any* initial swapbill balance. It is funded purely in host coin.

Assuming there are no other competing sell offers, this offer should go through directly (in the next block)
and be matched with the corresponding buy offer::

    ~/git/swapbill $ python Client.py get_balance
    Loaded cached state data successfully
    State update starting from block 279555
    Committed state updated to start of block 279556
    in memory: BackedSellOffer
     - 0.17788234 swapbill output added
    In memory state updated to end of block 279576
    Operation successful
    balance : 0.17788234

And we can see that the buy offer has been updated accordingly::

    ~/git/swapbill $ python Client.py get_buy_offers
    ...
    Operation successful
    exchange rate : 0.92
        host coin equivalent : 0.84834825
        mine : False
        swapbill offered : 0.92211766
    exchange rate : 0.95
        host coin equivalent : 1.9
        mine : False
        swapbill offered : 2

(The top buy offer there is a remainder left over after this offer was partially matched by our sell.)

Commission
-----------

Let's check the amount debited from our host coin wallet (after allowing change to clear)::

    ~/git $ bitcoin/src/bitcoin-cli getbalance
    2.81442955

So, this cost us 0.16747001 host coin.
This corresponds to:

* the amount of host coin we offered in our sell transaction (0.16365176)
* plus backer commission of 0.005 * 0.16365176 = 0.000818259
* plus 0.003 in transaction fees


By default, backers commission is added to the amount specified for hostCoinOffered in the sell_offer command.
If we want to specify an amount to be paid *including backer commission* then we can do this by setting the --includesCommission option.

Pending exchange
-----------------

If we check with the get_pending_exchanges command, just after our sell transaction goes through, we can see that a pending exchange has been created,
corresponding to this offer::

    ~/git/swapbill $ python Client.py get_pending_exchanges
    ...
    Operation successful
    pending exchange index : 0
        I am seller (and need to complete) : False
        I am buyer (and waiting for payment) : False
        backer id : 0
        blocks until expiry : 13
        confirmations : 3
        swap bill paid by buyer : 0.17788234
        expires on block : 279591
        deposit paid by seller : 0.01111765
        outstanding host coin payment amount : 0.16365176

This shows that the backer needs to complete the exchange with the person who made the buy offer.

Normally, the backer will go ahead and complete this exchange after a certain number of blocks have been confirmed.
But this is something that we don't have to worry about, at all, in this case,
as the backed exchange mechanism insulates us completely from exchange completion details.
(If the backer fails to complete the exchange with the buyer, *the backer* will lose their deposit.)

It's also possible to make an exchange *without a backer*.
In this case no backer commission is payable,
but you have to take care of making exchange completion transactions yourself.
(This is something we'll look at a bit later on.)

Waiting for a match
-------------------

In this case our sell offer was matched immediately, with an existing buy offer.

In other situations there may not be a matching buy offer (if we chose a lower exchange rate, for example),
competing sell offers may come through and match a buy offer before our offer.

And it's possible you offer to partially match with a partial remainder offer outstanding.

In these case's you'll need to wait for your offer to match, or for each part of your offer to match,
before being credited with the corresponding swapbill.
