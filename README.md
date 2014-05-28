# Requirements

The SwapBill client is written in Python and supports Python versions 2.7, 3.2, 3.3 and 3.4.

The third party Python 'ecdsa' and 'requests' modules are required and must be installed.

The client is currently set up to use the litecoin reference client (litecoinQT or litecoind) as a backend
(and the litecoin blockchain as host blockchain), and so the litecoin reference client must also be installed.

The client has been tested on Linux and Windows, but should work on any platform which supports the litecoin reference client and the
required Python dependencies.

# Setting up litecoinQT or litecoind as an RPC server

You can get the litecoin reference client from <https://litecoin.org/>.

The SwapBill client connects to the litecoin reference client with RPC calls, and so we need to ensure that this set up as an RPC server.

The reference client should then also connect to the litecoin testnet (as opposed to mainnet), and maintain a full transaction index.

To set this up, create a litecoin.conf file in the default location (if you don't already have one), and add some lines like the following:

    server=1
    testnet=1
    txindex=1
    rpcuser=litecoinrpc
    rpcpassword=somesecretpassword

(Change the password!)

The default location for this file on Linux is `~/.litecoin/litecoin.conf`,
while on Windows it looks like this is located at the path corresponding to `C:\Users\YourUserName\AppData\Roaming\LiteCoin\litecoin.conf`,
depending on your system setup.

To start the server you can then either launch litecoinQT (the graphical client) normally, or run litecoind from the command line.
If running litecoind, the -printtoconsole option can be used to get console output about what the server is doing.

If you already ran the reference client previously, against testnet, *without the txindex option* a reindexing operation will be required,
you should get a message about this.
If running litecoinQT you should be able to just click OK to go ahead, or you can call litecoind with the -reindex option to do this explicitly.

You can test the RPC server by making RPC queries from the command line, e.g.:

    ~/git/litecoin/src $ ./litecoind getbalance
    11914.15504872

(This RPC interface is very handy for interaction with the reference client generally, and for general troubleshooting.)

## A note about the txindex option

The txindex tells litecoind to include a full transaction index, which is required if you want to look up any arbitrary transaction in the blockchain history
by transaction ID.

Because of the way the SwapBill protocol works, with swapbill amounts associated directly with unspent outputs in the underlying blockchain,
the SwapBill client just need to scan the transactions in each new block as it arrives,
and *doesn't* need to look up arbitrary transactions from further back in the blockchain history.

Unfortunately, the RPC interface to the litecoin reference client doesn't provide a way to query the transactions by block, and
the txindex option is then required, essentially, as a workaround to implement this specific query functionality.

It's possible, and quite straightforward, to patch the reference client source code to add an RPC method for querying the set of transactions in a given block,
without the txindex option needing to be set. The SwapBill client actually tests for the existance of a custom 'getrawtransactionsinblock' RPC method,
and uses this if available. With this custom query no arbitrary transaction queries is required, and the txindex option can be left unset.

# Running the client

There's no installation process for the client, currently, and instead this just runs directly
from the downloaded source tree.
(You'll need to ensure that third party dependencies are met, before running the client, or you'll get an error message telling you to do this.)

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
State update starting from block 280696
Committed state updated to start of block 283286
In memory state updated to end of block 283306
Operation successful
active : 0
spendable : 0
total : 0
```

## Testnet

For the current release the client is configured to work only with the litecoin testnet,
and only spend 'testnet litecoin' outputs, and any swapbill balances created with the client are then all 'testnet swapbill'.

As with the bitcoin testnet, litecoin testnet coins are designed to be without value, and the same then goes for testnet swapbill,
so you can try things out at this stage without spending any real litecoin.

From here on, wherever we talk about 'swapbill' or 'litecoin', (for the current release) this means 'testnet litecoin' and 'testnet swapbill'.

## Protocol subject to change

The purpose of this release is to solicit community feedback about a protocol in development.
The protocol and client interface implemented for the current release, and as described in this document, are not final,
and are subject to change.

# Basic operation

## Wallet organisation

From here on, also, we'll refer to the litecoin reference client simply as litecoind, and the SwapBill client as just 'the client'.
(The client doesn't care whether RPC requests are served by litecoind or litecoinQT, and you can use these interchangeably.)

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

To create some swapbill in this way, you'll first need some litecoin to burn.

For the current testnet only release, you can get some litecoin from a faucet,
such as [here](http://testnet.litecointools.com/) or [here](http://kuttler.eu/bitcoin/ltc/faucet/),
but it also seems fairly easy at the moment to get testnet litecoin directly by mining.
For this you can simply use the ```setgenerate true``` RPC command to turn on mining in litecoind.

Once you have spendable litecoin you can go ahead and use this to create some swapbill with the client's 'burn' action.

```
~/git/swapbill $ python Client.py burn --amount 10000000
Loaded cached state data successfully
State update starting from block 283276
Committed state updated to start of block 283346
In memory state updated to end of block 283366
attempting to send Burn, destination output address=myLej8rPxBF2ZE5ST2YVDpnA7Dwjh8fbRA, amount=10000000
Operation successful
transaction id : 01e436f2d26827dd9bd35b01e08a7aa4676b118284113b23ce3f0e5eac645cb6
```

The amount here is in satoshis, so this just destroyed 0.1 litecoin.
But in exchange we're credited with a corresponding amount of swapbill.

It's worth noting at this point that the SwapBill protocol includes a constraint on the minimum amount of swapbill associated with any
given SwapBill 'account', or output. This is a financial motivation for users to minimise the number of unspent and active swapbill outputs
to be tracked, and a discouragement for 'spam' outputs.
The constraint is currently set to exactly 10000000 satoshis, and so that's the minimum amount we're allowed to burn.
(If you try to burn less, the client should refuse to submit the transaction and display a suitable error message.)

By default, queries such as get_balance only report the amount actually confirmed (with at least one confirmation) by the host blockchain,
and so if we try querying this straight away, we won't see any swapbill credited for this burn:

```
~/git/swapbill $ python Client.py get_balance
Loaded cached state data successfully
State update starting from block 283346
Committed state updated to start of block 283346
In memory state updated to end of block 283366
Operation successful
active : 0
spendable : 0
total : 0
```

But we can use the -i option to force the query to include pending transactions (from the litecoind memory pool), and then we get:

```
~/git/swapbill $ python Client.py get_balance -i
Loaded cached state data successfully
State update starting from block 283346
Committed state updated to start of block 283346
In memory state updated to end of block 283366
in memory pool: Burn
 - 10000000 swapbill output added
Operation successful
active : 10000000
spendable : 10000000
total : 10000000
```

And then, if we wait a bit to allow the transaction to go through, we can see this as a confirmed transaction:

```
~/git/swapbill $ python Client.py get_balance
Loaded cached state data successfully
State update starting from block 283346
Committed state updated to start of block 283349
in memory: Burn
 - 10000000 swapbill output added
In memory state updated to end of block 283369
Operation successful
active : 10000000
spendable : 10000000
total : 10000000
```

Note that it can sometimes take a while for new blocks to be mined on the litecoin testnet,
depending on whether anyone is actually mining this blockchain (!), and it can then take a while for swapbill transactions to be confirmed.

Burn transactions are necessary to create swapbill initially,
but you'll get a better exchange rate for your host currency if you *exchange*
host currency for swapbill (see below), and so exchanges for the host currency should be preferred over burns wherever possible.

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
receive_address : mox1jfYfZF5JdZrh5AiGmYB37xKza1526B
```

This is actually just a standard address for the host blockchain, but the client stores the corresponding private key in wallet.txt,
and will detect any swapbill outputs paying to this address and add the relevant amounts to your balance.

```
~/git/swapbill $ python Client.py pay --amount 10000000 --toAddress mox1jfYfZF5JdZrh5AiGmYB37xKza1526B
Loaded cached state data successfully
State update starting from block 283356
Committed state updated to start of block 283358
in memory: Burn
 - 10000000 swapbill output added
In memory state updated to end of block 283378
attempting to send Pay, change output address=mvCU9EbGn9MAPgcfvZ81zkhpacopLzVpWK, destination output address=mox1jfYfZF5JdZrh5AiGmYB37xKza1526B, amount=10000000, maxBlock=283387, sourceAccount=(u'01e436f2d26827dd9bd35b01e08a7aa4676b118284113b23ce3f0e5eac645cb6', 1)
Operation successful
transaction id : 1ffb0e1fb9bea35b9a1e84ce3a82937c340070637582f2e3083e817b761ea162
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
~/git/swapbill $ python Client.py -pay --amount 10000000 --toAddress mmdAwus4b6chWzvRtNVcL2YfxvWTeWUcq3
```

And then in this case, the default wallet owner is debited the swapbill payment amount, and this is credited to 'alice'.

(Note that you need to create the new data directory before invoking the client. The client won't create this directory for you.)

## Multiple outputs and 'collect'

The SwapBill protocol associates swapbill amounts with special unspent outputs (where these outputs corresponding directly to unspent outputs in the underlying blockchain).
Your swapbill balance total at any one time is then calculated as the sum of swapbill outputs owned by your wallet.

Most of the transactions in the SwapBill protocol operate on just 'one swapbill unspent', as transaction input,
and the maximum amount that can be paid in to the transaction is then equal to the highest value swapbill output currently available.
This is what is reported by the 'active' value returned by the get_balance query.

If we submit a number of separate burn transactions, or if we receive multiple swapbill payments, this active balance will be less than our
balance total, and will limit the maximum amount we can spend in new transactions.

```
~/git/swapbill $ mkdir bob
~/git/swapbill $ python Client.py --dataDir bob burn --amount 12345678
...
~/git/swapbill $ python Client.py --dataDir bob burn --amount 11111111
...
(transaction is confirmed on host blockchain)
~/git/swapbill $ python Client.py --dataDir bob get_balance
Loaded cached state data successfully
State update starting from block 283393
Committed state updated to start of block 283393
in memory: Burn
 - 11111111 swapbill output added
in memory: Burn
 - 12345678 swapbill output added
In memory state updated to end of block 283413
Operation successful
active : 12345678
spendable : 23456789
total : 23456789
~/git/swapbill $ python Client.py --dataDir bob pay --amount 13000000 --toAddress mmdAwus4b6chWzvRtNVcL2YfxvWTeWUcq3
...
In memory state updated to end of block 283413
Operation failed: ('Transaction would not complete successfully against current state:', 'insufficient balance in source account (transaction ignored)')
```

So the active balance is effectively the maximum amount that can be spent at any one time.

The 'collect' transaction combines multiple outputs into a single new output, and
from the point of view of the balances shown in the client, what this does is to move all of the swapbill included in the spendable balance
into that active balance.

```
~/git/swapbill $ python Client.py --dataDir bob collect
Loaded cached state data successfully
State update starting from block 283393
Committed state updated to start of block 283397
in memory: Burn
 - 11111111 swapbill output added
in memory: Burn
 - 12345678 swapbill output added
In memory state updated to end of block 283417
attempting to send Collect, destination output address=myoaYua9oYmfYnN6CwYRAStYndLRuwNaEK, sourceAccounts=[(u'4d5c80ed99d8baa3fd625ad5405782717ee8a23c6f8c25bb712e30c501ec5574', 1), (u'073d19b7fb4ec45b91d29fd7772d8ec943c9a8933037a8894c86a4376778e18c', 1)]
Operation successful
transaction id : db46bc5a4b0a44f2a01e377f8d0b9414f62b45c7f6ed86ad92edb65a161df88e

~/git/swapbill $ python Client.py --dataDir bob get_balance
Loaded cached state data successfully
...
in memory pool: Collect
 - 11111111 swapbill output consumed
 - 12345678 swapbill output consumed
Operation successful
active : 0
spendable : 0
total : 0

(wait a bit for the collect transaction to get confirmed)

~/git/swapbill $ python Client.py --dataDir bob get_balance
Loaded cached state data successfully
...
in memory: Collect
 - 11111111 swapbill output consumed
 - 12345678 swapbill output consumed
 - 23456789 swapbill output added
In memory state updated to end of block 283418
Operation successful
active : 23456789
spendable : 23456789
total : 23456789

(and now we can make the payment)

~/git/swapbill $ python Client.py --dataDir bob pay --amount 13000000 --toAddress mmdAwus4b6chWzvRtNVcL2YfxvWTeWUcq3
...
In memory state updated to end of block 283418
attempting to send Pay, change output address=mrcGoLRfThXeNzG6xVkpZNi8vXZd3TDHf5, destination output address=mmdAwus4b6chWzvRtNVcL2YfxvWTeWUcq3, amount=13000000, maxBlock=283427, sourceAccount=(u'db46bc5a4b0a44f2a01e377f8d0b9414f62b45c7f6ed86ad92edb65a161df88e', 1)
Operation successful
transaction id : d0ef280e3fff3d7b16588180a88703068f67ca348b6a76f24a36dd8292171845
```

## Splitting accounts

When you spend less than the amount in your active balance, in a pay transaction for example,
this has the effect of 'splitting' that balance into two separate outputs, and it's important to be aware of how the minimum balance constraint then comes into play.

The key point to be aware of is that the SwapBill protocol does not permit amounts less than the minimum balance constraint in
*either* the payment destination output, *or* the payment change output (if there is one).

So, based on the current minimum balance constraint of 10000000 satoshis, if the active account contains exactly 20000000 satoshis
then you can make a payment of:
* exactly 10000000 satoshis (which leaves both payment target and change exactly at the minimum balance), or
* exactly 20000000 satoshis (with no change output created)
but you can't make a payment of:
* less than 10000000 satoshis (result in payment destination holding less than minimum balance), or
* in between 10000000 and 20000000 satoshis (which would require a change output with less than the minimum balance)

## Trading swapbill for host currency

The swapbill protocol includes support for decentralised exchange between swapbill and the host currency, based on buy and sell
offer information posted on the block chain and protocol rules for matching these buy and sell offers.

Three additional client actions (and associated transaction types) are provided for this exchange mechanism:
* post_ltc_buy
* post_ltc_sell
* complete_ltc_sell

Buying litecoin with swapbill is the most straightforward use case because this requires just one action.
In this case you just post a trade offer (with amount to trade and exchange rate) and the SwapBill protocol takes over with handling the trade from there.

Selling litecoin for swapbill is a bit more complicated in that an offer completion transaction needs to be submitted to complete the transaction
after trade offers have been matched.

When buying litecoin the swapbill amount being offered is moved into the trade, and will then either be paid to the litecoin seller on completion,
or refunded on trade offer expiry or if the seller fails to complete the trade.

When selling litecoin a deposit in swapbill needs to be paid.
This is currently set to 1/16 of the trade amount.
If the seller completes the trade correctly then this deposit is refunded, but if the seller fails to make a completion payment after offers have been matched
then the deposit is paid to the matched buyer.

Exchange rates are always fractional values between 0.0 and 1.0 (greater than 0.0 and less than 1.0), and specify the number of litecoins per swapbill
(so an exchange rate of 0.5 indicates that one litecoin exchanges for 2 swapbill).

A couple of other details to note with regards to trading:
* the post sell offer transactions each effectively split off a new output (for receiving payment or refunds), and are subject to the minimum balance requirements described with regards to account splitting, above
* there is also a minimum litecoin equivalent constraint applied to trade offers - currently the litecoin equivalent for each trade offer type (calculate based on swapbill amount and exchange rate) must be at least 1000000 litecoin satoshis
* trade offers may be partially matched, and litecoin sell offers can then potentially require more than completion transaction

The trading mechanism provided by SwapBill is necessarily fairly complex, and a specification of the *exact* operation of this mechanism is beyond the scope of this document,
but we'll show a concrete example of trading worked through in the client to show *how to use* the mechanism.

## Trading example

The client uses the term 'buy' to refer to buying litecoin with swapbill,
and 'sell' to refer to selling litecoin for swapbill, and we'll use the same convention here.

So a 'buyer' has some swapbill, and wants to exchange for litecoin:

```
~/git/swapbill $ python Client.py --dataDir buyer get_balance
...
Operation successful
active : 100000000
spendable : 100000000
total : 100000000
```

To check the list of sell offers currently active on the block chain:

```
~/git/swapbill $ python Client.py --dataDir buyer get_sell_offers
Loaded cached state data successfully
...
Operation successful
exchange rate : 0.919999999925
    swapbill desired : 13400000
    deposit paid : 837500
    mine : False
    ltc equivalent : 12327999
exchange rate : 0.899999999907
    swapbill desired : 10000000
    deposit paid : 625000
    mine : False
    ltc equivalent : 8999999
exchange rate : 0.889999999898
    swapbill desired : 1800000
    deposit paid : 112500
    mine : False
    ltc equivalent : 1601999
```

Higher exchange rates are better for our buyer.

Our buyer is ok with each swapbill being valued at 0.919 litecoin, and goes ahead and posts a buy offer.

```
 ~/git/swapbill $ python Client.py --dataDir buyer post_ltc_buy --swapBillOffered 10000000 --exchangeRate 0.919
...
In memory state updated to end of block 283672
attempting to send LTCBuyOffer, change output address=mtTgHycMu7H4k7CTsk1mPLCRSYzLdPsRLi, ltcBuy output address=mtbXpS62QTuiZMicZ5H34eCW2BWfxVRdjN, exchangeRate=3947074945, maxBlock=283681, receivingAddress=mzA3C8icRRpWH8bpiFvzMiPGYKRyq2uRM1, sourceAccount=(u'e35e9a1dd74a825b4cec7ceb267cc746f22f8a2dee316f032d01f08eb7d92486', 1), swapBillOffered=10000000
Operation successful
transaction id : b0e88c6d9e7969f3ebbd7738dfd5cc42f245e03a5ab75dbfc5f20db6764ad74e
```

We check sell offers again immediately, and these are unchanged, with our buy offer still in the memory pool:

```
~/git/swapbill $ python Client.py --dataDir buyer get_sell_offers
Loaded cached state data successfully
...
In memory state updated to end of block 283672
in memory pool: LTCBuyOffer
 - 100000000 swapbill output consumed
Operation successful
exchange rate : 0.919999999925
    swapbill desired : 13400000
    deposit paid : 837500
    mine : False
    ltc equivalent : 12327999
exchange rate : 0.899999999907
    swapbill desired : 10000000
    deposit paid : 625000
    mine : False
    ltc equivalent : 8999999
exchange rate : 0.889999999898
    swapbill desired : 1800000
    deposit paid : 112500
    mine : False
    ltc equivalent : 1601999
```

But in the next block, the transaction goes through:

```
thomas@Z77A-MINT15 ~/git/swapbill $ python Client.py --dataDir buyer get_sell_offers
Loaded cached state data successfully
State update starting from block 283653
Committed state updated to start of block 283654
in memory: Burn
 - 100000000 swapbill output added
in memory: LTCBuyOffer
 - 100000000 swapbill output consumed
 - 80000000 swapbill output added
 - created buy offer, refund output seeded with 10000000 swapbill and locked until trade completed
In memory state updated to end of block 283674
Operation successful
exchange rate : 0.919999999925
    swapbill desired : 3400000
    deposit paid : 212500
    mine : False
    ltc equivalent : 3127999
exchange rate : 0.899999999907
    swapbill desired : 10000000
    deposit paid : 625000
    mine : False
    ltc equivalent : 8999999
exchange rate : 0.889999999898
    swapbill desired : 1800000
    deposit paid : 112500
    mine : False
    ltc equivalent : 1601999
```

So we can see that no other buy offers were madein this time, and (as long as there are no subsequent blockchain reorganisations) our offer has been matched against
the top sell offer, and the amount of the top sell offer reduced accordingly.

Note the line in our transaction reports about a refund output being seeded and locked until trade complete.
And we can see this, also, when we check our balance:

```
~/git/swapbill $ python Client.py --dataDir buyer get_balance
...
In memory state updated to end of block 283675
Operation successful
active : 80000000
spendable : 80000000
total : 90000000
```

This shows that 10000000 satoshis of our total balance is not 'spendable'.
What's happened here is that an output has been created for the trade.
This output will be credited with a refund of our swapbill in trading, plus the seller's deposit, if the trade is not completed by the seller.
And the output is locked (in the SwapBill protocol) because the trade is still active, and can potentially pay more swapbill in to the output.

If we check the current list of buy offers, our offer is not listed, because this has already been matched (it was matched immediately against an existing sell offer):

```
~/git/swapbill $ python Client.py --dataDir buyer get_buy_offers
...
In memory state updated to end of block 283677
Operation successful
No entries
```

There is now a 'pending exchange' generated by our trade offer, however, and we can see this with the get_pending_exchanges query:

```
~/git/swapbill $ python Client.py --dataDir buyer get_pending_exchanges
...
In memory state updated to end of block 283677
Operation successful
pending exchange index : 2
    I am seller (and need to complete) : False
    outstanding ltc payment amount : 9194999
    swap bill paid by buyer : 10000000
    expires on block : 283724
    I am buyer (and waiting for payment) : True
    deposit paid by seller : 625000
```

We just need to wait for the seller to complete the exchange, with the exchange completion including a payment of the outstanding litecoin amount listed.
If the seller doesn't complete the exchange before block 283724 then the SwapBill protocol will refund us the amount of swapbill paid, plus the deposit of 625000.

## Selling litecoin for swapbill

The process for selling litecoin is similar, but with a second transaction required for exchange completion.

So, a 'seller' has some litecoin, and wants to exchange for swapbill.

The seller needs some swapbill to seed a receive output for the trade, and to pay a deposit.

```
~/git/swapbill $ python Client.py --dataDir seller get_balance
...
Operation successful
active : 20000000
spendable : 20000000
total : 20000000
```

A receive output will be required for the trade, and a minimum balance of 10000000 will be required to seed that output,
leaving 10000000 available for a trade deposit.

The deposit is calculated as a fixed fraction of the swapbill amount being traded, with this fraction set by the SwapBill protocol, and currently fixed at 1/16.
So this balance will enable us to exchange litecoin for a further 160000000 swapbill.

To check the list of buy offers currently active on the block chain:

```
~/git/swapbill $ python Client.py --dataDir seller get_buy_offers
...
Operation successful
exchange rate : 0.931999999797
    ltc equivalent : 112771999
    mine : False
    swapbill offered : 121000000
exchange rate : 0.949999999953
    ltc equivalent : 80337699
    mine : False
    swapbill offered : 84566000
```

Lower exchange rates are better for the seller.

The seller wants to value each swapbill at 0.925 litecoin (so below the lowest existing buy offers), and goes ahead and posts an offer.

```
~/git/swapbill $ python Client.py --dataDir seller post_ltc_sell --swapBillDesired 160000000 --exchangeRate 0.925 --blocksUntilExpiry 4
...
In memory state updated to end of block 283686
attempting to send LTCSellOffer, change output address=mtaJf1mTHsjXW97aoNQmT5ALhW6EwBZHsT, ltcSell output address=mx4hbMPDUALfF4D7YdeAAw4rUFADdbjsSQ, exchangeRate=3972844748, maxBlock=283691, sourceAccount=(u'4473ef0aca2d3750ae19c525a7ca4db66dbd96f71af0caf6a460d94eb186899b', 1), swapBillDesired=160000000
Operation successful
transaction id : ff0cf83f1523074883f5e433f05326a60548a48a2f41919eb4989411e57f145c
```

Note that we've set an additional blocksUntilExpiry option here.
This option defaults to a fairly low value, but it can be quite important to control this value when making litecoin sell transactions,
since we'll need to make sure we watch for matches and submit the corresponding completion transactions.
By making the offer expire within a small number of blocks we can limit the time during which we need to check for matches,
although this also gives buyers less time to make matching offers.

Our sell offer goes through in the next mined block, but is not matched, because it is lower than the existing buy offers, and now appears on the list of sell offers.

```
~/git/swapbill $ python Client.py --dataDir seller get_sell_offers
...
In memory state updated to end of block 283687
Operation successful
exchange rate : 0.924999999814
    swapbill desired : 160000000
    deposit paid : 10000000
    mine : True
    ltc equivalent : 147999999
exchange rate : 0.919999999925
    swapbill desired : 3400000
    deposit paid : 212500
    mine : False
    ltc equivalent : 3127999
...
```

The exchange rate value shown is slightly different to the exchange rate we specified in the offer because
exchange rates are represented internally by the client (and in the SwapBill protocol) as integer values, and there was some rounding in the post_offer_action.

In the next block, some one makes a buy offer that matches our offer, but with a smaller amount, and our offer is therefore *partially matched*.

```
~/git/swapbill $ python Client.py --dataDir seller get_sell_offers
...
In memory state updated to end of block 283689
Operation successful
exchange rate : 0.924999999814
    swapbill desired : 147700000
    deposit paid : 9231250
    mine : True
    ltc equivalent : 136622499
exchange rate : 0.919999999925
    swapbill desired : 3400000
    deposit paid : 212500
    mine : False
    ltc equivalent : 3127999
...
```

And we can see that a new pending exchange is now listed for our offer.

```
~/git/swapbill $ python Client.py --dataDir seller get_pending_exchanges
...
In memory state updated to end of block 283689
Operation successful
pending exchange index : 3
    I am seller (and need to complete) : True
    outstanding ltc payment amount : 11377499
    swap bill paid by buyer : 12300000
    expires on block : 283739
    I am buyer (and waiting for payment) : False
    deposit paid by seller : 768750
```

We now have a fixed number of blocks in which to complete the trade before this pending exchange expires.
(The SwapBill protocol currently fixes this at 50 blocks from the block in which trade offers are matched.)

To complete the exchange we use the complete_ltc_sell action.

```
~/git/swapbill $ python Client.py --dataDir seller complete_ltc_sell --pendingExchangeID 3
...
In memory state updated to end of block 283689
attempting to send LTCExchangeCompletion, destinationAddress=mg7a3nRjWnAw9EP2f11g38uMk3JAENroXR, destinationAmount=11377499, pendingExchangeIndex=3
Operation successful
transaction id : abe86fd9a17b1b27f8f302b398995d20c2f6366590484f7feee2670db580a831
```

Once the completion transaction has gone through, we can see that we have been credited with swapbill for the partial exchange:

```
~/git/swapbill $ python Client.py --dataDir seller get_balance
...
In memory state updated to end of block 283690
Operation successful
active : 0
spendable : 0
total : 23068750
```

We need to watch for further matches, and complete as necessary, until the sell offer has expires.
This happens a few blocks later, and we can then see the unmatched swapbill refunded to our balance.

```
 ~/git/swapbill $ python Client.py --dataDir seller get_balance
Loaded cached state data successfully
State update starting from block 283671
Committed state updated to start of block 283671
...
in memory: LTCSellOffer
 - 20000000 swapbill output consumed
 - created sell offer, receiving output seeded with 10000000 swapbill and locked until trade completed
in memory: LTCBuyOffer
 - sell offer updated (receiving output contains 10000000 swapbill)
in memory: LTCExchangeCompletion
 - sell offer updated (receiving output contains 23068750 swapbill)
trade offer or pending exchange expired
In memory state updated to end of block 283691
Operation successful
active : 32300000
spendable : 32300000
total : 32300000
```
