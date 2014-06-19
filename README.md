# Introduction

SwapBill is an 'embedded' cryptocurrency protocol and cryptocurrency, currently at the preview stage and hosted on the litecoin blockchain.

A reference client for SwapBill is provided, written in Python and using the litecoin reference client (litecoinQT or litecoind) as
as a backend for peer to peer network connectivity and block validation.

# Requirements

To run the SwapBill reference client you'll need:

* Python version 2.7, 3.2, 3.3 or 3.4
* The third party Python 'ecdsa' and 'requests' modules
* The litecoin reference client (litecoinQT or litecoind) set up and running as an RPC server

The code has been tested on Linux and Windows, but should work on any platform with support for the litecoin reference client and the
required Python dependencies.

# Setting up litecoinQT or litecoind as an RPC server

The SwapBill client can connect to either litecoind or litecoinQT as an RPC server (so with or without the QT graphical interface),
as long as this is configured appropriately, but from here on I'll use the term 'litecoind' generically to refer to either litecoind
or litecoinQT set up as an RPC server, and 'the client' to refer to the SwapBill reference client.

You can download installers for litecoind from <https://litecoin.org/>, or this can also be built from source (from <https://github.com/litecoin-project/litecoin>).

For the current preview version of the client, you'll need to tell litecoind to connect to the litecoin testnet.

The default location for the litecoind configuration file is `~/.litecoin/litecoin.conf` on Linux,
and something like `C:\Users\YourUserName\AppData\Roaming\LiteCoin\litecoin.conf` on Windows.

Create a litecoin.conf file in this default location (if not already present), and add some lines like the following:

    server=1
    testnet=1
    rpcuser=litecoinrpc
    rpcpassword=somesecretpassword

(Note that starting from preview version 0.3 a full transaction index, and therefore the txindex option, is no longer required. Change the password!)

To start the server you can then either launch litecoinQT (the graphical client) normally, or run litecoind from the command line.
If running litecoind, the -printtoconsole option can be used to get console output about what the server is doing.

You can test the RPC server by making RPC queries from the command line, e.g.:

    ~/git/litecoin/src $ ./litecoind getbalance
    11914.15504872

(This RPC interface is very handy for interaction with the reference client generally, and for general troubleshooting.)

# Running the client

There's no installation process for the client and you can just run this directly
from the downloaded source tree.
(You'll need to ensure that third party dependencies are met before running the client, or you'll get an error message telling you to do this.)

At the time of writing, the project is hosted on <https://github.com/crispweed/swapbill>, and you can get the client source code with:

```
~/git $ git clone https://github.com/crispweed/swapbill
Cloning into 'swapbill'...
remote: Counting objects: 52, done.
remote: Compressing objects: 100% (41/41), done.
remote: Total 52 (delta 9), reused 46 (delta 3)
Unpacking objects: 100% (52/52), done.
```

and then run the client with (e.g.):

```
~/git $ cd swapbill/
~/git/swapbill $ python Client.py get_balance
```

Or, if you don't have git, you can download the archive from <https://github.com/crispweed/swapbill/archive/master.zip>, extract to a new directory, and run from there.

If you don't have litecoind or litecoinQT running, or if you don't have the RPC interface set up correctly, you'll see something like:

```
~/git/swapbill $ python Client.py get_balance
Couldn't connect for remote procedure call, will sleep for ten seconds and then try again.
Couldn't connect for remote procedure call, will sleep for ten seconds and then try again.
(...repeated indefinitely)
```

But if you start the RPC server, the client should connect and complete the command from there.

If the RPC interface is working correctly you should see something like this:

```
~/git/swapbill $ python Client.py get_balance
Failed to load from cache, full index generation required (no cache file found)
State update starting from block 305846
Committed state updated to start of block 305886
In memory state updated to end of block 305906
Operation successful
balance : 0
```

## Testnet

For the current release the client is configured to work only with the litecoin testnet,
and only spend 'testnet litecoin' outputs.
Any swapbill balances created with the client are then all 'testnet swapbill'.

As with the bitcoin testnet (see <https://en.bitcoin.it/wiki/Testnet>), litecoin testnet coins are designed to be without value, and the same goes for testnet swapbill,
so you can try things out at this stage without spending any real litecoin.

From here on (and for the current release), wherever we talk about 'swapbill' or 'litecoin', this means 'testnet litecoin' and 'testnet swapbill'.

## Protocol subject to change

The purpose of this release is to solicit community feedback about a protocol in development.
The protocol and client interface implemented for the current release, and as described in this document, are not final,
and are subject to change.

# Basic operation

## Wallet organisation

When you run the client there are two different wallets to be aware of:
* the 'standard' litecoind wallet built in to litecoind, and
* a separate, independant wallet available and controlled only by the client.

The litecoind wallet is used mostly for 'backing' funds for dust outputs and transaction fees in the underlying blockchain,
but can also be used for special 'burn' transactions, and for litecoin payments that complete litecoin to swapbill exchanges.

The client then stores the keys for special SwapBill control outputs separately.
These are essentially outputs that control balances in the SwapBill protocol, and the client then also tracks the relevant outputs independantly of litecoind.

The client wallet can be found in the client data directory (by default a 'swapBillData' directory, created in the working directory when you start the client),
in 'wallet.txt'.
This file contains the private keys that control your swapbill balances, so don't send this file or reveal the contents to anyone,
unless you want them to be able to spend your swapbill, and make sure that the file is backed up securely!

## Creating swapbill by proof of burn

The only way to *create* swapbill is by 'proof of burn' (on the host blockchain).
Essentially, if you *destroy* some of the host currency (litecoin) in a specified way,
the swapbill protocol will credit you with a corresponding amount in swapbill.

There's some discussion of proof of burn [here](https://en.bitcoin.it/wiki/Proof_of_burn).

Although burning litecoin is not the recommended way of obtaining some initial swapbill, the proof of burn mechanism is quite important.
The key point here is that you're *always* able to create swapbill
by burning host currency, at a fixed price,
and this then provides a price cap for swapbill in terms of the host currency.

Let's take a look at how this works, then, first of all.

### Obtaining testnet litecoin

To create swapbill by proof of burn, you'll first of all need some litecoin to destroy.

For the current testnet only release you only need to get hold of testnet litecoin, of course,
and there are sites set up as 'faucets' for this purpose,
such as [here](http://testnet.litecointools.com/) or [here](http://kuttler.eu/bitcoin/ltc/faucet/).

It's also not so hard to get testnet litecoin directly by through the (CPU) mining functionality in litecoind.
(Use the ```setgenerate true``` RPC command to turn this on.)

### Burning

Once you have spendable litecoin, go ahead and use this to create some swapbill, with the client's 'burn' action.

```
~/git/swapbill $ python Client.py burn --amount 0.5
Loaded cached state data successfully
State update starting from block 305886
Committed state updated to start of block 305890
In memory state updated to end of block 305910
attempting to send Burn, destination output address=n1J6nWhxwJinMt1VtwrC38V4yzZ3qPvCbv, amount=50000000
Operation successful
transaction id : d70e2a95237c35235eb77f9d1491be64bb357a8a50f8ce88260053fabc095e02
```

Once this goes through you will have destroyed 0.5 litecoin, but in exchange you're credited with a corresponding amount of swapbill.

It's worth noting at this point that the SwapBill protocol includes a constraint on the minimum amount of swapbill associated with any
given SwapBill 'account', or output. This is a financial motivation for users to minimise the number of active swapbill outputs
to be tracked, and a discouragement for 'spam' outputs.
The constraint is currently set to exactly 10000000 satoshis, or 0.1 litecoin, and so that's the minimum amount we're allowed to burn.
(If you try to burn less, the client should refuse to submit the transaction and display a suitable error message.)

By default, queries such as get_balance only report the amount actually confirmed (with at least one confirmation) by the host blockchain,
and so if we try querying this straight away, we won't see any swapbill credited for this burn:

```
~/git/swapbill $ python Client.py get_balance
Loaded cached state data successfully
State update starting from block 305890
Committed state updated to start of block 305890
In memory state updated to end of block 305910
Operation successful
balance : 0
```

But we can use the -i option to force the query to include pending transactions (from the litecoind memory pool), and then we get:

```
~/git/swapbill $ python Client.py get_balance -i
Loaded cached state data successfully
State update starting from block 305890
Committed state updated to start of block 305890
In memory state updated to end of block 305910
in memory pool: Burn
 - 0.5 swapbill output added
Operation successful
balance : 0.5
```

And then, if we wait a bit to allow the transaction to go through, we can see this as a confirmed transaction:

```
~/git/swapbill $ python Client.py get_balance
Loaded cached state data successfully
State update starting from block 305890
Committed state updated to start of block 305891
in memory: Burn
 - 0.5 swapbill output added
In memory state updated to end of block 305911
Operation successful
balance : 0.5
```

Note that it can sometimes take a while for new blocks to be mined on the litecoin testnet,
depending on whether anyone is actually mining this blockchain, and if no one is mining (!) it can then take a while for swapbill transactions to be confirmed..

Burn transactions are necessary to create swapbill initially, but once some swapbill has been burnt and is in circulation
it's much better to exchange host currency for this swapbill,
and you'll get a better exchange rate this way. (We'll come back to look at the exchange functionality a bit later.)

## Aside: committed and in memory transactions

In the above output we can see different block counts for 'committed' and 'in memory' state, and it's worth taking a moment to explain this.

What's going on here is that the client commits state to disk to avoid spending time resynchronising on each invocation,
but with this committed state lagging a fixed number of blocks (currently 20) behind the actual current block chain end.

This mechanism enables the client to handle small blockchain reorganisations robustly, without overcomplicating the client code.
If there are blockchain reorganisations of more than 20 blocks this will trigger a full resynch,
but blockchain reorganisations of less than 20 blocks can be processed naturally starting from the committed state.

For transaction reporting during synchronisation:
* Transactions that are included in the persistent state cached to disk get prefixed by 'committed'.
* Transactions that are confirmed in the blockchain but not yet cached to disk get prefixed by 'in memory'. (When you run the client again, you'll normally see these transactions repeated, unless there was a blockchain reorganisation invalidating the transaction.)
* Transactions that are not yet confirmed in the blockchain, but present in the litecoind memory pool get get prefixed with 'in memory pool'.

## Making payments

To make a payment in swapbill, we use the 'pay' action.
As with bitcoin and litecoin,
the payment recipient first needs to generate a target address for the payment,
and we can do this with the 'get_receive_address' action:

```
~/git/swapbill $ python Client.py get_receive_address
...
Operation successful
receive_address : mtLEgRXJA2WhaSZiXpocacTbRb9HAn9Xs1
```

This is actually just a standard address for the host blockchain, but the client stores the corresponding private key in wallet.txt,
and will detect any swapbill outputs paying to this address and add the relevant amounts to your balance.

```
~/git/swapbill $ python Client.py pay --amount 0.1 --toAddress mtLEgRXJA2WhaSZiXpocacTbRb9HAn9Xs1
Loaded cached state data successfully
State update starting from block 305894
Committed state updated to start of block 305894
in memory: Burn
 - 0.5 swapbill output added
In memory state updated to end of block 305914
attempting to send Pay, change output address=mnR7MJH3aXJ6HBhkcVitersptTLioykkK4, destination output address=mtLEgRXJA2WhaSZiXpocacTbRb9HAn9Xs1, amount=10000000, maxBlock=305923
Operation successful
transaction id : 29755ec9c77b1141f7473e5e958e7ef96df7e92eccd939dbe8c702f18899ef43
```

In this case we're actually just paying ourselves.
It's also possible to manage multiple swapbill wallets independantly, by changing the client data directory,
and to use this to try out transactions between different wallet 'owners':

```
~/git/swapbill $ mkdir alice
~/git/swapbill $ python Client.py --dataDir alice get_receive_address
...
Operation successful
receive_address : mmdAwus4b6chWzvRtNVcL2YfxvWTeWUcq3
~/git/swapbill $ python Client.py -pay --amount 0.1 --toAddress mmdAwus4b6chWzvRtNVcL2YfxvWTeWUcq3
```

And then, in this case, the default wallet owner is debited the swapbill payment amount, and this is credited to 'alice'.

(Note that you need to create the new data directory before invoking the client. The client won't create this directory for you.)

## Trading swapbill for host currency

The swapbill protocol includes support for decentralised exchange between swapbill and the host currency, based on buy and sell
offer information posted on the block chain and with protocol rules for matching these buy and sell offers.

Three additional client actions (and associated transaction types) are provided for this exchange mechanism:
* post_ltc_buy
* post_ltc_sell
* complete_ltc_sell

Buying litecoin with swapbill is the most straightforward use case because this requires just one transaction to post a trade offer,
with the SwapBill protocol then taking over handling of the trade completely from there.

There are then two different kinds of litecoin sell offer.

'Backed' sell offers are the recommended method, when there are are 'backers' available.
In this case the backer has already committed a swapbill amount to cover the trade, so you just need to make one sell offer transaction,
and the backer then takes care of exchange completion payments.

When no backers are available, you can also make unbacked sell offers, but are then responsible for subsequent exchange completion payments yourself.

When trade offers go through, swapbill amounts are associated with the offers and paid out again when offers are matched, according to the SwapBill protocol rules.

In the case of buy offers this is the swapbill amount being offered in exchange for litecoin.

In the case of sell offers this is a deposit amount, in swapbill, currently set to 1/16 of the trade amount, which is held by the protocol and paid back on condition of successful completion.
If the seller completes the trade correctly then this deposit is refunded, but if the seller fails to make a completion payment after offers have been matched
then the deposit is credited to the matched buyer (in compensation for their funds being locked up during the trade).

Exchange rates are always fractional values between 0.0 and 1.0 (greater than 0.0 and less than 1.0), and specify the number of litecoins per swapbill
(so an exchange rate of 0.5 indicates that one litecoin exchanges for 2 swapbill).

A couple of other details to note with regards to trading:
* the sell offer transactions also require an amount equal to the protocol minimum balance constraint to be 'seeded' into the sell offer (but, unlike the deposit, this seed amount will be returned to the seller whether or not trades are successfully completed)
* trade offers are subject to minimum exchange amounts for both the swapbill and litecoin equivalent parts of the exchange
* trade offers may be partially matched, and litecoin sell offers can then potentially require more than completion transaction
* matches between small trade offers are only permitted where the offers can be matched without violating the minimum exchange amounts and minimum offer amounts for any remainder

The trading mechanism provided by SwapBill is necessarily fairly complex, and a specification of the *exact* operation of this mechanism is beyond the scope of this document,
but we'll show a concrete example of trading worked through in the client to show *how to use* the mechanism.

Note that the client uses the term 'buy' to refer to buying litecoin with swapbill,
and 'sell' to refer to selling litecoin for swapbill, and we'll use the same convention here.

## Backed litecoin sell offer

Backed litecoin sell offers are actually the recommended way to obtain some initial swapbill, in preference to burn transactions.

As with burn transactions, no swapbill balance is required in order to make a backed litecoin sell offer,
but this does depend on some backing amount having already been committed by a third party, and some commission is payable to the backer for these transactions.

(Because commission is paid to backer, with the rate of commission subject to market forces, *if* there is swapbill available for exchange then there *should* be backers available,
otherwise this is an indication that swapbill supply is insufficient, and so creating more swapbill by burning is appropriate!)

You can use the 'get_ltc_sell_backers' action to check if there are backers available,
and to find out information about the backers such as rate of commission being charged, as follows:

```
~/git/swapbill $ python Client.py get_ltc_sell_backers
...
Operation successful
ltc sell backer index : 0
    blocks until expiry : 9952
    I am backer : False
    backing amount : 1000
    expires on block : 315881
    commission : 0.01
    maximum per transaction : 10
```

The commission value here indicates that 1% commission is payable to the backer on the amount of ltc offered for sale.

Apart from that, the important values to look at are backing amount value and maximum per transaction.

The backed trade mechanism provided by SwapBill works by backers committing funds to guarantee trades for a certain number of transactions in advance.

From the numbers here, we can see that the backer has enough funds currently committed to guarantee at least 100 trade transaction.
But, if 100 other valid trade transactions to the same backer all come through on the blockchain in between this backer query and our backed sell transaction actually, it's theoretically possible for us to lose our ltc payment amount.

With a larger backing amount, or a smaller maximum amount per transaction, more transactions would be guaranteed, making the trade more secure.
But lets go ahead and exchange some litecoin for swapbill through this backer, nevertheless.

The next step is to check the buy offers currently posted to the blockchain, to get an idea of the current excange rate:

```
~/git/swapbill $ python Client.py get_buy_offers
...
Operation successful
exchange rate : 0.92
    ltc equivalent : 1.104
    mine : False
    swapbill offered : 1.2
exchange rate : 0.95
    ltc equivalent : 0.38
    mine : False
    swapbill offered : 0.4
```

The best offer comes first, with 1.2 swapbill offered at an exchange rate of 0.92 litecoin per swapbill.
So let's assume we're ok with making an exchange at this rate, but we actually want to exchange a bit more than 1.104 litecoin.

```
~/git/swapbill $ python Client.py post_ltc_sell --ltcOffered 4 --exchangeRate 0.92 --backerID 0
Loaded cached state data successfully
State update starting from block 306244
Committed state updated to start of block 306247
In memory state updated to end of block 306267
attempting to send BackedLTCSellOffer, sellerReceive output address=msUkYfCkH8vdQGp1TmsnEm8Pm5vgEARBHb, backerIndex=0, backerLTCReceiveAddress=mo4DLT1a7ZhBRZTrXYXs9BRu6efyzrXmM1, exchangeRate=920000000, ltcOfferedPlusCommission=404000000
Operation successful
transaction id : 81e8bd072c386fa3b0744779083e98626de6f57719a025b8ae1115230c902fed
```

Note that, by default, backers commission will be added to the amount specified here for ltcOffered.
So, in this case, we'll actually pay 4.04 litecoin in to this transaction.
If we want to specify an amount to be paid *including backer commission* then we can do this by setting the --includesCommission flag.

After a short delay, this transaction goes through:

```
~/git/swapbill $ python Client.py get_balance
Loaded cached state data successfully
State update starting from block 306248
Committed state updated to start of block 306249
in memory: BackedLTCSellOffer
 - 1.2 swapbill output added
In memory state updated to end of block 306269
Operation successful
balance : 1.2
```

So we can see that our offer has been matched directly against the highest buy offer, and we've been credited the corresponding swapbill amount immediately.
(This was credited to us by the SwapBill protocol directly from the backer funds.)

We can see that the top buy offer has been removed:

```
~/git/swapbill $ python Client.py get_buy_offers
...
In memory state updated to end of block 306269
Operation successful
exchange rate : 0.95
    ltc equivalent : 0.38
    mine : False
    swapbill offered : 0.4
```

The top buy offer didn't fully match our offer, however, and so some of our sell offer remains outstanding:

```
~/git/swapbill $ python Client.py get_sell_offers
...
Operation successful
exchange rate : 0.92
    mine : False
    ltc offered : 2.896
    deposit : 0.19673914
    backer id : 0
    swapbill equivalent : 3.14782609
```

Note that this is not reported as being 'our' offer, because the offer is actually now the responsibility of the backer.
The deposit amount quoted here was actually paid by the backer, because the backer is responsible for completing the exchange
with each matched buyer.
And we don't need to worry about whether or not exchanges are completed successfully by the backer, because we're credited directly from backer funds
(by the SwapBill protocol) as soon as offers are matched.

We do need to wait until a buy offer comes along to match the remaining part of our sell offer, however.
This offer will never expire and there is no way for us to cancel the offer,
short of posting a matching buy offer ourself, so it's generally a good idea to only make offers that are likely to be matched directly when using the backed exchange mechanism,
if you're in a hurry to receive the swapbill!

Fortunately someone comes along and makes a matching buy offer:

```
~/git/swapbill $ python Client.py get_balance
Loaded cached state data successfully
State update starting from block 306252
Committed state updated to start of block 306253
in memory: BackedLTCSellOffer
 - 1.2 swapbill output added
in memory: LTCBuyOffer
 - trade offer completed
In memory state updated to end of block 306273
Operation successful
balance : 4.34782609
```

## Buying litecoin with swapbill

Ok, so we've looked at how to get hold of some swapbill, either through a backed exchange, or by burning litecoin.
SwapBill is intended to serve a fairly specific purpose, however, (for facilitating decentralised cross currency exchange, specifically),
and when you've finished using your swapbill you will most likely want to exchange this back for host currency.

You can do this with the buy offer transaction (buying litecoin with swapbill).
The process for this is similar to backed sell offers, but even more straightforward, because there's no need to select a backer in this case.

Starting with a buyer, who has 5 swapbill they want to exchange for litecoin:

```
~/git/swapbill $ python Client.py get_balance
...
Operation successful
balance : 5
```

Let's check the current list of sell offers:

```
~/git/swapbill $ python Client.py get_sell_offers -i
...
Operation successful
exchange rate : 0.91
    mine : False
    ltc offered : 3.5
    deposit : 0.24038462
    backer id : 0
    swapbill equivalent : 3.84615385
exchange rate : 0.88
    mine : False
    ltc offered : 2.4
    deposit : 0.17045455
    backer id : 0
    swapbill equivalent : 2.72727273
```

The best rate here is 0.91 litecoin per swapbill.
Let's assuming we're ok with exchanging at anything down to 0.9 litecoin per swapbill.
So, we'll try and match that top offer first:

```
~/git/swapbill $ python Client.py post_ltc_buy --swapBillOffered 3.84615385 --blocksUntilExpiry 1 --exchangeRate 0.91
...
attempting to send LTCBuyOffer, ltcBuy output address=mo4ceReHzLCh4i9Bb4tCPEvShvGfiakvus, exchangeRate=910000000, maxBlock=306282, receivingAddress=mr8EojsG7Rh2jvxt6gEaKd3zufFHXCXESa, swapBillOffered=384615385
Operation successful
transaction id : dcf2b207a33d26f58c429f47ac0cae654a0581bc61f0c0baf08c7b98c836250e
```

This is similar to the sell offer we posted in the previous example, but there a couple of other points to note here.

First of all, note that we've specified a value for blocksUntilExpiry.
This is because we just want to match the top existing offer, but there is a possibility that someone else matches that offer first.
So we've set our transaction to expire in the next block, if it doesn't match, so that we can then go on and use the swapbill in another offer.

A second point to note is that the decimal fractions displayed by queries such as get_sell_offers, and passed in for transaction parameters are
actually *exact* values, and not subject to approximation errors during parsing or display.
So we can copy the exact text printed for the top sell offer and expect our offer to match this exactly.
(This is a subtle point, but nevertheless quite an important implementation detail!)

No other offers come in before our buy offer, then, and this matches the top offer:

```
~/git/swapbill $ python Client.py get_balance
...
in memory: LTCBuyOffer
 - 5 swapbill output consumed
 - 1.15384615 swapbill output added
In memory state updated to end of block 306281
Operation successful
balance : 1.15384615
```

We decide to post the remaining funds again, in another buy offer:

```
~/git/swapbill $ python Client.py post_ltc_buy --swapBillOffered 1.15384615 --exchangeRate 0.9
...
attempting to send LTCBuyOffer, ltcBuy output address=mo4ceReHzLCh4i9Bb4tCPEvShvGfiakvus, exchangeRate=910000000, maxBlock=306282, receivingAddress=mr8EojsG7Rh2jvxt6gEaKd3zufFHXCXESa, swapBillOffered=384615385
Operation successful
transaction id : dcf2b207a33d26f58c429f47ac0cae654a0581bc61f0c0baf08c7b98c836250e
```

Again, note that we can post the exact current balance value, and the client will then include the whole balance in the offer.
Remember that the SwapBill protocol includes a minimum balance constraint, so this can be important,
as we're not permitted to submit transaction that would leave a very small amount of change.
(If so, the client will report an error, and refuse to submit the transaction. Try spending very slightly less than your current balance,
to see this in practice.)

In this case we didn't specify blocksUntilExpiry.
For buy transactions this currently defaults to 8, for backed sell transactions there is no expiry and for
unbacked sells the default is just 2 blocks (because unbacked sells need to be followed up with exchange completion for each matching buyer).

This offer doesn't match any existing sell offer, and is initially left as an outstanding offer:

```
~/git/swapbill $ python Client.py get_buy_offers
...
in memory: LTCBuyOffer
 - 1.15384615 swapbill output consumed
 - 0 swapbill output added
In memory state updated to end of block 306286
Operation successful
exchange rate : 0.9
    ltc equivalent : 1.03846154
    mine : True
    swapbill offered : 1.15384615
exchange rate : 0.95
    ltc equivalent : 0.38
    mine : False
    swapbill offered : 0.4
```

If no-one posts a matching offer before the end of the expiry period, the swapbill amount offered will be returned to our active balance.
But, as it is, a couple of sell offers come along in the next few blocks, and match the outstanding offer remainder:

```
~/git/swapbill $ python Client.py get_buy_offers
...
in memory: LTCBuyOffer
 - 1.15384615 swapbill output consumed
 - 0 swapbill output added
in memory: BackedLTCSellOffer
 - trade offer updated
in memory: BackedLTCSellOffer
 - trade offer updated
In memory state updated to end of block 306289
Operation successful
exchange rate : 0.95
    ltc equivalent : 0.38
    mine : False
    swapbill offered : 0.4
```

It turns out that our second offer was actually matched by two smaller sell offers.
And so at this point, we have three trade offer matches outstanding waiting for final litecoin payments to complete.
We can see this with the get_pending_exchanges query:

```
~/git/swapbill $ python Client.py get_pending_exchanges
...
In memory state updated to end of block 306289
Operation successful
pending exchange index : 3
    blocks until expiry : 42
    I am seller (and need to complete) : False
    outstanding ltc payment amount : 3.5
    swap bill paid by buyer : 3.84615385
    backer id : 0
    expires on block : 306331
    I am buyer (and waiting for payment) : True
    deposit paid by seller : 0.24038462
pending exchange index : 4
    blocks until expiry : 50
    I am seller (and need to complete) : False
    outstanding ltc payment amount : 0.09
    swap bill paid by buyer : 0.1
    backer id : 0
    expires on block : 306339
    I am buyer (and waiting for payment) : True
    deposit paid by seller : 0.00625
pending exchange index : 5
    blocks until expiry : 50
    I am seller (and need to complete) : False
    outstanding ltc payment amount : 0.94846153
    swap bill paid by buyer : 1.05384615
    backer id : 0
    expires on block : 306339
    I am buyer (and waiting for payment) : True
    deposit paid by seller : 0.06586538
```

As a litecoin buyer, we don't have to take any action here.
Either the seller pays the required litecoin amount and completes the exchange,
or we are refunded our swapbill plus some deposit paid by the seller as part of their sell offer.

In this case all three sell offers are actually backed sell offers, using the same backer, so it is up to this backer to complete the exchange.

A bit later we can see that one of the exchanges has been completed:

```
~/git/swapbill $ python Client.py get_pending_exchanges
...
in memory: LTCBuyOffer
 - 5 swapbill output consumed
 - 1.15384615 swapbill output added
in memory: LTCBuyOffer
 - 1.15384615 swapbill output consumed
 - 0 swapbill output added
in memory: BackedLTCSellOffer
 - trade offer updated
in memory: BackedLTCSellOffer
 - trade offer updated
in memory: LTCExchangeCompletion
 - trade offer completed
In memory state updated to end of block 306293
Operation successful
pending exchange index : 4
    blocks until expiry : 46
    I am seller (and need to complete) : False
    outstanding ltc payment amount : 0.09
    swap bill paid by buyer : 0.1
    backer id : 0
    expires on block : 306339
    I am buyer (and waiting for payment) : True
    deposit paid by seller : 0.00625
pending exchange index : 5
    blocks until expiry : 46
    I am seller (and need to complete) : False
    outstanding ltc payment amount : 0.94846153
    swap bill paid by buyer : 1.05384615
    backer id : 0
    expires on block : 306339
    I am buyer (and waiting for payment) : True
    deposit paid by seller : 0.06586538
```

Our litecoin balance is managed by litecoind, separately from the SwapBill client.
There's a check for the completion payment going through as part of the SwapBill protocol (and therefore as part of the client's synchronisation)
but the SwapBill client does'nt keep a running count of our litecoin balance, and you'll need to check this directly with litecoind
(e.g. with the getbalance RPC query) if you want to verify this yourself.

Some time later, all of the exchanges have been completed, and we should have received the full litecoin amount in our litecoind wallet:

```
~/git/swapbill $ python Client.py get_pending_exchanges
...
in memory: LTCBuyOffer
 - 1.15384615 swapbill output consumed
 - 0 swapbill output added
in memory: BackedLTCSellOffer
 - trade offer updated
in memory: BackedLTCSellOffer
 - trade offer updated
in memory: LTCExchangeCompletion
 - trade offer completed
in memory: LTCExchangeCompletion
 - trade offer updated
in memory: LTCExchangeCompletion
 - trade offer completed
In memory state updated to end of block 306304
Operation successful
No entries
```

## Unbacked sell litecoin for swapbill

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
but for larger transactions, and if you can be confident about being able to put completion transactions
(e.g. if you have a backup internet connection) then unbacked sells can be preferrable.

To make an unbacked sell offer we start with a post_ltc_sell action, as before, but in this case we *don't* specify a value for backerID
(and so don't need to check for backers and backer details).

Our seller starts with some swapbill:

```
~/git/swapbill $ python Client.py get_balance
...
Operation successful
balance : 9.45893721
```

Check buy offers:

```
 ~/git/swapbill $ python Client.py get_buy_offers
...
Operation successful
exchange rate : 0.95
    ltc equivalent : 0.38
    mine : False
    swapbill offered : 0.4
exchange rate : 0.96
    ltc equivalent : 0.61542028
    mine : False
    swapbill offered : 0.64106279
```

Let's try and match the top offer:

```
~/git/swapbill $ python Client.py post_ltc_sell --ltcOffered 0.38 --exchangeRate 0.95
...
attempting to send LTCSellOffer, ltcSell output address=mrshs7hscqVPHCiFshM3cetm4JHomiEsKQ, exchangeRate=950000000, ltcOffered=38000000, maxBlock=306302
Operation successful
transaction id : 650a80a27c9170f9f0d0a59c7646db91e874bb84edfda24d69aaecfe76eae64b
```

This goes through successfully, and we can see that the buy offer has been matched:

```
~/git/swapbill $ python Client.py get_buy_offers
...
in memory: LTCSellOffer
 - 0.1 swapbill output consumed
 - 4.34782609 swapbill output consumed
 - 4.42282609 swapbill output added
In memory state updated to end of block 306300
Operation successful
exchange rate : 0.96
    ltc equivalent : 0.61542028
    mine : False
    swapbill offered : 0.64106279
```

The amount of swapbill offered, plus a deposit, have been taken from our current balance, but also a
seed amount equivalent to the minimum balance protocol constraint (currently set to 0.1 swapbill):

```
~/git/swapbill $ python Client.py get_balance
...
in memory: LTCSellOffer
 - 0.1 swapbill output consumed
 - 4.34782609 swapbill output consumed
 - 4.42282609 swapbill output added
In memory state updated to end of block 306303
Operation successful
balance : 9.43393721
```

Now it is up to us to complete.
We can see the pending exchange with get_pending_exchanges:

```
 ~/git/swapbill $ python Client.py get_pending_exchanges
...
in memory: LTCSellOffer
 - 0.1 swapbill output consumed
 - 4.34782609 swapbill output consumed
 - 4.42282609 swapbill output added
In memory state updated to end of block 306300
Operation successful
pending exchange index : 6
    blocks until expiry : 50
    I am seller (and need to complete) : True
    outstanding ltc payment amount : 0.38
    swap bill paid by buyer : 0.4
    expires on block : 306350
    I am buyer (and waiting for payment) : False
    deposit paid by seller : 0.025
```

It's probably a good idea to wait for a few more blocks to go through before completing the exchange, in case of blockchain reorganisation.
(This is more of an issue for completion transactions than other transactions, and something that backers will normally worry about for you, in the case of backed sells!)

Note that 'blocks until expiry' starts at 50 blocks in the current protocol definition, and we can infer the number of confirmations from this.
A bit later on we can see the pending exchange with 47 blocks left to expiry, and decide to go ahead with the exchange.

```
 ~/git/swapbill $ python Client.py get_pending_exchanges
...
in memory: LTCSellOffer
 - 0.1 swapbill output consumed
 - 4.34782609 swapbill output consumed
 - 4.42282609 swapbill output added
In memory state updated to end of block 306303
Operation successful
pending exchange index : 6
    blocks until expiry : 47
    I am seller (and need to complete) : True
    outstanding ltc payment amount : 0.38
    swap bill paid by buyer : 0.4
    expires on block : 306350
    I am buyer (and waiting for payment) : False
    deposit paid by seller : 0.025
```

The actual completion transaction is then straightforward:

```
~/git/swapbill $ python Client.py complete_ltc_sell --pendingExchangeID 6
...
In memory state updated to end of block 306303
attempting to send LTCExchangeCompletion, destinationAddress=mmn38D6EaMSoF5wFpg4Nns3GZMgzbXMUu9, destinationAmount=38000000, pendingExchangeIndex=6
Operation successful
transaction id : 0481db0e3d529f5d17b1709ddc8007c7ceb7fceb57b4433e98d677b13cc5e35b
```

Once this transaction has gone through we're refunded the deposit, and the seed amount,
and credited the swapbill amount corresponding to our exchange:

```
~/git/swapbill $ python Client.py get_balance
...
in memory: LTCExchangeCompletion
 - trade offer completed
In memory state updated to end of block 306304
Operation successful
balance : 9.85893721
```
