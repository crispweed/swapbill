Currency Supply
===================

A small, fixed, 'seed' amount of swapbill is currently created by the protocol,
and assigned to outputs determined by the SwapBill developers, and written into the client source code.
The purpose of this seed amount is to help fund development of SwapBill protocol and to help provide some
initial liquidity for exchanges and backer funds.

After this seed amount, the only way to *create* any additional swapbill is by 'proof of burn' (on the host blockchain).

You can find some discussion of the concept of proof of burn `here <https://en.bitcoin.it/wiki/Proof_of_burn>`__.

Essentially, if you *destroy* some of the host currency in a specified way,
the swapbill protocol will credit you with a corresponding amount in swapbill.

More specifically, exactly one unit of swapbill is created for each unit of host currency that is destroyed.

This proof of burn mechanism is quite important, then, in that it provides a kind of fixed cap for the price of swapbill,
in terms of the host coin.
Since it's always guaranteed to be possible to create 1 unit of swapbill for 1 unit of host currency,
it doesn't make any sense for anyone to ever exchange swapbill at a higher price than this
(and, in fact, the exchange mechanisms don't permit any higher rate of exchange).

In most cases you shouldn't need to *actually perform* any burn transactions,
since you can expect to get a better price by *exchanging* host coin for existing swapbill, instead,
