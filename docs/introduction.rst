Introduction
=============

Embedded protocol
-------------------

SwapBill is an 'embedded' cryptocurrency protocol,
which means that SwapBill transactions are hosted on an existing blockchain.

The SwapBill protocol defines a subset of host transactions
which are also considered valid SwapBill transactions, with additional control information encoded into these
special transactions, and with protocol rules for how these transactions then act on
a global SwapBill state.

Security
---------

The main advantage of this setup is that we benefit from the security guarantees of an existing,
established blockchain, including proof of work, whilst also having the
flexibility to add new transaction types and features that would be difficult to add directly to an existing blockchain.

Notably, this setup eliminates the need to obtain any kind of 'critical mass' of miners during a product launch phase,
and makes it possible for SwapBill to be launched and operate robustly without any minimum required uptake.

Purpose
---------

The primary purpose for SwapBill is to introduce trustless exchange features such as 'atomic' exchange between
coins hosted on different blockchains.

Status
---------

A reference client for the SwapBill protocol is provided, written in Python and using the bitcoin and/or litecoin reference clients as
as backends for peer to peer network connectivity and block validation.

The SwapBill client is currently at the preview stage, and for this reason only operates on testnet versions of host blockchains.

In the current release (|version|), the supported host blockchains are bitcoin testnet and litecoin testnet.

As described `here <https://en.bitcoin.it/wiki/Testnet>`__, testnet coins are designed to be without value, and the same goes for swapbill generated with the current preview client,
so you can try things out at this stage without risking any real value.

Multiple denominations
-------------------------

A different swapbill denomination is created for each host blockchain on which swapbill is embedded.
With the current reference client it is possible to create either 'bitcoin testnet swapbill' or 'litecoin testnet swapbill'.

Protocol subject to change
--------------------------

This preview client release is provided for community feedback about a protocol in development.
The protocol and client interface implemented for the current release, and as described in this document, are not final,
and are subject to change.

