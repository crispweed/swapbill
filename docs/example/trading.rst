Trading transactions
=====================

The swapbill protocol includes extensive support for decentralised exchange between swapbill and the host currency, based on buy and sell
offer information posted on the block chain and with protocol rules for matching these buy and sell offers.

Three additional client actions (and associated transaction types) are provided for this exchange mechanism:
* buy_offer
* sell_offer
* complete_sell

Terminology
------------

The client uses 'buy' to refer to buying host coin (with swapbill), and 'sell' to refer to selling host coin (for swapbill),
and we'll use the same convention in this documentation.

Buy transactions
-----------------

Buying host coin with swapbill is the most straightforward use case because this requires just one transaction to post a trade offer,
with the SwapBill protocol then taking over handling of the trade completely from there.

Sell transactions
-----------------

There are then two different kinds of host coin sell offer.

'Backed' sell offers are the recommended method, when there are are backers available.
In this case the backer has already committed a swapbill amount to cover the trade, so you just need to make one sell offer transaction,
and the backer then takes care of exchange completion payments.

When no backers are available, you can also make unbacked sell offers, but are then responsible for subsequent exchange completion payments yourself.

When trade offers go through, swapbill amounts are associated with the offers and paid out again when offers are matched, according to the SwapBill protocol rules.

In the case of buy offers this is the swapbill amount being offered in exchange for host coin.

In the case of sell offers this is a deposit amount, in swapbill, currently set to 1/16 of the trade amount, which is held by the protocol and paid back on condition of successful completion.
If the seller completes the trade correctly then this deposit is refunded, but if the seller fails to make a completion payment after offers have been matched
then the deposit is credited to the matched buyer (in compensation for their funds being locked up during the trade).

Exchange rates are always fractional values between 0.0 and 1.0 (greater than 0.0 and less than 1.0), and specify the number of host coins per swapbill
(so an exchange rate of 0.5 indicates that one host coin exchanges for 2 swapbill).

A couple of other details to note with regards to trading:
* the sell offer transactions also require an amount equal to the protocol minimum balance constraint to be 'seeded' into the sell offer (but, unlike the deposit, this seed amount will be returned to the seller whether or not trades are successfully completed)
* trade offers are subject to minimum exchange amounts for both the swapbill and host coin equivalent parts of the exchange
* trade offers may be partially matched, and host coin sell offers can then potentially require more than completion transaction
* matches between small trade offers are only permitted where the offers can be matched without violating the minimum exchange amounts and minimum offer amounts for any remainder

The trading mechanism provided by SwapBill is necessarily fairly complex, and a specification of the *exact* operation of this mechanism is beyond the scope of this document,
but we'll show a concrete example of trading worked through in the client to show *how to use* the mechanism.
