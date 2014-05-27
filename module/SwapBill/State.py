from __future__ import print_function
import binascii
from SwapBill import TradeOfferHeap, LTCTrading
from SwapBill.Amounts import e

class InvalidTransactionParameters(Exception):
	pass
class InvalidTransactionType(Exception):
	pass
class OutputsSpecDoesntMatch(Exception):
	pass

class BuyDetails(object):
	pass
class SellDetails(object):
	pass

class State(object):
	def __init__(self, startBlockIndex, startBlockHash, minimumBalance=1*e(7)):
		## state is initialised at the start of the block with startBlockIndex
		assert minimumBalance > 0
		self._startBlockHash = startBlockHash
		self._currentBlockIndex = startBlockIndex
		self._minimumBalance = minimumBalance
		self._balances = {}
		self._balanceRefCounts = {}
		self._tradeOfferChangeCounts = {}
		self._totalCreated = 0
		self._totalForwarded = 0
		self._LTCBuys = TradeOfferHeap.Heap(startBlockIndex, False) # lower exchange rate is better offer
		self._LTCSells = TradeOfferHeap.Heap(startBlockIndex, True) # higher exchange rate is better offer
		self._nextExchangeIndex = 0
		self._pendingExchanges = {}

	def getSpendableAmount(self, account):
		if account in self._balanceRefCounts:
			return 0
		return self._balances.get(account, 0)

	def startBlockMatches(self, startBlockHash):
		return self._startBlockHash == startBlockHash

	def advanceToNextBlock(self):
		expired = self._LTCBuys.advanceToNextBlock()
		for buyDetails in expired:
			self._tradeOfferChangeCounts[buyDetails.refundAccount] += 1
			self._addToAccount(buyDetails.refundAccount, buyDetails.swapBillAmount)
			self._removeAccountRef(buyDetails.refundAccount)
		expired = self._LTCSells.advanceToNextBlock()
		for sellDetails in expired:
			self._tradeOfferChangeCounts[sellDetails.receivingAccount] += 1
			self._addToAccount(sellDetails.receivingAccount, sellDetails.swapBillDeposit)
			self._removeAccountRef(sellDetails.receivingAccount)
		## ** currently iterates through all pending exchanges each block added
		## are there scaling issues with this?
		toDelete = []
		for key in self._pendingExchanges:
			exchange = self._pendingExchanges[key]
			if exchange.expiry == self._currentBlockIndex:
				#print("pending exchange expired")
				#print("buyerAddress:", exchange.buyerAddress)
				#print("refundAmount:", exchange.swapBillAmount + exchange.swapBillDeposit)
				## refund buyers funds locked up in the exchange, plus sellers deposit (as penalty for failing to make exchange)
				self._addToAccount(exchange.buyerAddress, exchange.swapBillAmount + exchange.swapBillDeposit)
				self._tradeOfferChangeCounts[exchange.buyerAddress] += 1
				self._tradeOfferChangeCounts[exchange.sellerReceivingAccount] += 1
				self._removeAccountRef(exchange.buyerAddress)
				self._removeAccountRef(exchange.sellerReceivingAccount)
				toDelete.append(key)
		for key in toDelete:
			self._pendingExchanges.pop(key)
		self._currentBlockIndex += 1

	def _addAccount(self, account, amount):
		assert type(amount) is int
		assert amount >= 0
		assert not account in self._balances
		self._balances[account] = amount
	def _addToAccount(self, account, amount):
		assert type(amount) is int
		assert amount >= 0
		self._balances[account] += amount
	def _consumeAccount(self, account):
		amount = self._balances[account]
		self._balances.pop(account)
		return amount

	def _removeAccountRef(self, account):
		assert self._balanceRefCounts[account] > 0
		assert self._balances[account] > 0
		if self._balanceRefCounts[account] == 1:
			self._tradeOfferChangeCounts.pop(account)
			self._balanceRefCounts.pop(account)
		else:
			self._balanceRefCounts[account] -= 1

	def _matchLTC(self):
		while True:
			if self._LTCBuys.empty() or self._LTCSells.empty():
				return
			if self._LTCBuys.currentBestExchangeRate() > self._LTCSells.currentBestExchangeRate():
				return
			buyRate = self._LTCBuys.currentBestExchangeRate()
			buyExpiry = self._LTCBuys.currentBestExpiry()
			buyDetails = self._LTCBuys.popCurrentBest()
			sellRate = self._LTCSells.currentBestExchangeRate()
			sellExpiry = self._LTCSells.currentBestExpiry()
			sellDetails = self._LTCSells.popCurrentBest()
			assert self._balanceRefCounts[sellDetails.receivingAccount] > 0
			assert self._balanceRefCounts[buyDetails.refundAccount] > 0
			self._tradeOfferChangeCounts[sellDetails.receivingAccount] += 1
			self._tradeOfferChangeCounts[buyDetails.refundAccount] += 1
			exchange, buyDetails, sellDetails = LTCTrading.Match(buyRate, buyExpiry, buyDetails, sellRate, sellExpiry, sellDetails)
			exchange.expiry = self._currentBlockIndex + 50
			key = self._nextExchangeIndex
			self._nextExchangeIndex += 1
			# the account refs from buy and sell details effectively transfer into this exchange object
			self._pendingExchanges[key] = exchange
			if not buyDetails is None:
				if LTCTrading.SatisfiesMinimumExchange(buyRate, buyDetails.swapBillAmount):
					self._LTCBuys.addOffer(buyRate, buyExpiry, buyDetails)
					self._balanceRefCounts[buyDetails.refundAccount] += 1
					continue # may need to match against a second offer
				else:
					## small remaining buy offer is discarded
					## refund swapbill amount left in this buy offer
					self._addToAccount(buyDetails.refundAccount, buyDetails.swapBillAmount)
			if not sellDetails is None:
				if LTCTrading.SatisfiesMinimumExchange(sellRate, sellDetails.swapBillAmount):
					self._LTCSells.addOffer(sellRate, sellExpiry, sellDetails)
					self._balanceRefCounts[sellDetails.receivingAccount] += 1
					continue
				else:
					## small remaining sell offer is discarded
					## refund swapbill amount left in this buy offer
					self._addToAccount(sellDetails.receivingAccount, sellDetails.swapBillDeposit)
			return # break out of while loop

	def _check_Burn(self, outputs, amount):
		if outputs != ('destination',):
			raise OutputsSpecDoesntMatch()
		assert type(amount) is int
		assert amount >= 0
		if amount < self._minimumBalance:
			return False, 'burn amount is below minimum balance'
		return True, ''
	def _apply_Burn(self, txID, amount):
		self._totalCreated += amount
		self._addAccount((txID, 1), amount)

	def _check_Pay(self, outputs, sourceAccount, amount, maxBlock):
		if outputs != ('change', 'destination'):
			raise OutputsSpecDoesntMatch()
		assert type(amount) is int
		assert amount >= 0
		if amount < self._minimumBalance:
			return False, 'amount is below minimum balance'
		if not sourceAccount in self._balances:
			return False, 'source account does not exist'
		if self._balances[sourceAccount] < amount:
			return False, 'insufficient balance in source account (transaction ignored)'
		if self._balances[sourceAccount] > amount and self._balances[sourceAccount] < amount + self._minimumBalance:
			return False, 'transaction includes change output, with change amount below minimum balance'
		if sourceAccount in self._balanceRefCounts:
			return False, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires"
		if maxBlock < self._currentBlockIndex:
			return True, 'max block for transaction has been exceeded'
		return True, ''
	def _apply_Pay(self, txID, sourceAccount, amount, maxBlock):
		available = self._consumeAccount(sourceAccount)
		if maxBlock < self._currentBlockIndex:
			amount = 0
		else:
			self._addAccount((txID, 2), amount)
		if available > amount:
			self._addAccount((txID, 1), available - amount)

	def _check_Collect(self, outputs, sourceAccounts):
		if outputs != ('destination',):
			raise OutputsSpecDoesntMatch()
		for sourceAccount in sourceAccounts:
			if not sourceAccount in self._balances:
				return False, 'at least one source account does not exist'
			if sourceAccount in self._balanceRefCounts:
				return False, "at least one source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires"
		return True, ''
	def _apply_Collect(self, txID, sourceAccounts):
		amount = 0
		for sourceAccount in sourceAccounts:
			amount += self._consumeAccount(sourceAccount)
		if amount > 0:
			self._addAccount((txID, 1), amount)

	def _check_LTCBuyOffer(self, outputs, sourceAccount, swapBillOffered, exchangeRate, receivingAddress, maxBlock):
		if outputs != ('change', 'ltcBuy'):
			raise OutputsSpecDoesntMatch()
		assert type(swapBillOffered) is int
		assert swapBillOffered >= 0
		assert type(exchangeRate) is int
		assert exchangeRate > 0
		assert exchangeRate < 0x100000000
		assert type(maxBlock) is int
		assert maxBlock >= 0
		if swapBillOffered == 0:
			return False, 'zero amount not permitted'
		if not sourceAccount in self._balances:
			return False, 'source account does not exist'
		if self._balances[sourceAccount] < swapBillOffered + self._minimumBalance:
			return False, 'insufficient balance in source account (offer not posted)'
		if sourceAccount in self._balanceRefCounts:
			return False, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires"
		if not LTCTrading.SatisfiesMinimumExchange(exchangeRate, swapBillOffered):
			return False, 'does not satisfy minimum exchange amount (offer not posted)'
		if maxBlock < self._currentBlockIndex:
			return True, 'max block for transaction has been exceeded'
		return True, ''
	def _apply_LTCBuyOffer(self, txID, sourceAccount, swapBillOffered, exchangeRate, receivingAddress, maxBlock):
		available = self._consumeAccount(sourceAccount)
		if maxBlock < self._currentBlockIndex:
			self._addAccount((txID, 1), available)
			return
		changeAccount = (txID, 1)
		refundAccount = (txID, 2)
		assert available >= swapBillOffered + self._minimumBalance
		available -= swapBillOffered
		self._addAccount(refundAccount, self._minimumBalance)
		available -= self._minimumBalance
		if available >= self._minimumBalance:
			self._addAccount(changeAccount, available)
		else:
			self._addToAccount(refundAccount, available)
		buyDetails = BuyDetails()
		buyDetails.swapBillAmount = swapBillOffered
		buyDetails.receivingAccount = receivingAddress
		buyDetails.refundAccount = refundAccount
		assert not refundAccount in self._balanceRefCounts
		self._balanceRefCounts[refundAccount] = 1
		self._tradeOfferChangeCounts[refundAccount] = 0
		self._LTCBuys.addOffer(exchangeRate, maxBlock, buyDetails)
		self._matchLTC()

	def _check_LTCSellOffer(self, outputs, sourceAccount, swapBillDesired, exchangeRate, maxBlock):
		if outputs != ('change', 'ltcSell'):
			raise OutputsSpecDoesntMatch()
		assert type(swapBillDesired) is int
		assert swapBillDesired >= 0
		assert type(exchangeRate) is int
		assert exchangeRate > 0
		assert exchangeRate < 0x100000000
		assert type(maxBlock) is int
		assert maxBlock >= 0
		if swapBillDesired == 0:
			return False, 'zero amount not permitted'
		if not sourceAccount in self._balances:
			return False, 'source account does not exist'
		swapBillDeposit = swapBillDesired // LTCTrading.depositDivisor
		if self._balances[sourceAccount] < swapBillDeposit + self._minimumBalance:
			return False, 'insufficient balance in source account (offer not posted)'
		if sourceAccount in self._balanceRefCounts:
			return False, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires"
		if not LTCTrading.SatisfiesMinimumExchange(exchangeRate, swapBillDesired):
			return False, 'does not satisfy minimum exchange amount (offer not posted)'
		if maxBlock < self._currentBlockIndex:
			return True, 'max block for transaction has been exceeded'
		return True, ''
	def _apply_LTCSellOffer(self, txID, sourceAccount, swapBillDesired, exchangeRate, maxBlock):
		swapBillDeposit = swapBillDesired // LTCTrading.depositDivisor
		available = self._consumeAccount(sourceAccount)
		if maxBlock < self._currentBlockIndex:
			self._addAccount((txID, 1), available)
			return
		changeAccount = (txID, 1)
		receivingAccount = (txID, 2)
		assert available >= swapBillDeposit + self._minimumBalance
		available -= swapBillDeposit
		self._addAccount(receivingAccount, self._minimumBalance)
		available -= self._minimumBalance
		if available >= self._minimumBalance:
			self._addAccount(changeAccount, available)
		else:
			self._addToAccount(receivingAccount, available)
		sellDetails = SellDetails()
		sellDetails.swapBillAmount = swapBillDesired
		sellDetails.swapBillDeposit = swapBillDeposit
		sellDetails.receivingAccount = receivingAccount
		assert not receivingAccount in self._balanceRefCounts
		self._balanceRefCounts[receivingAccount] = 1
		self._tradeOfferChangeCounts[receivingAccount] = 0
		self._LTCSells.addOffer(exchangeRate, maxBlock, sellDetails)
		self._matchLTC()

	def _check_LTCExchangeCompletion(self, outputs, pendingExchangeIndex, destinationAddress, destinationAmount):
		if outputs != ():
			raise OutputsSpecDoesntMatch()
		assert type(destinationAmount) is int
		if not pendingExchangeIndex in self._pendingExchanges:
			return False, 'no pending exchange with the specified index (transaction ignored)'
		exchangeDetails = self._pendingExchanges[pendingExchangeIndex]
		if destinationAddress != exchangeDetails.ltcReceiveAddress:
			return False, 'destination account does not match destination for pending exchange with the specified index (transaction ignored)'
		if destinationAmount < exchangeDetails.ltc:
			return False, 'amount is less than required payment amount (transaction ignored)'
		if destinationAmount > exchangeDetails.ltc:
			return True, 'amount is greater than required payment amount (exchange completes, but with ltc overpay)'
		return True, ''
	def _apply_LTCExchangeCompletion(self, txID, pendingExchangeIndex, destinationAddress, destinationAmount):
		exchangeDetails = self._pendingExchanges[pendingExchangeIndex]
		## the seller completed their side of the exchange, so credit them the buyers swapbill
		## and the seller is also refunded their deposit here
		self._addToAccount(exchangeDetails.sellerReceivingAccount, exchangeDetails.swapBillAmount + exchangeDetails.swapBillDeposit)
		self._tradeOfferChangeCounts[exchangeDetails.buyerAddress] += 1
		self._tradeOfferChangeCounts[exchangeDetails.sellerReceivingAccount] += 1
		self._removeAccountRef(exchangeDetails.buyerAddress)
		self._removeAccountRef(exchangeDetails.sellerReceivingAccount)
		self._pendingExchanges.pop(pendingExchangeIndex)

	def _check_ForwardToFutureNetworkVersion(self, outputs, sourceAccount, amount, maxBlock):
		if outputs != ('change',):
			raise OutputsSpecDoesntMatch()
		assert type(amount) is int
		assert amount >= 0
		if amount < self._minimumBalance:
			return False, 'amount is below minimum balance'
		if maxBlock < self._currentBlockIndex:
			return False, 'max block for transaction has been exceeded'
		if not sourceAccount in self._balances:
			return False, 'source account does not exist'
		if self._balances[sourceAccount] < amount:
			return False, 'insufficient balance in source account (transaction ignored)'
		if self._balances[sourceAccount] > amount and self._balances[sourceAccount] < amount + self._minimumBalance:
			return False, 'transaction includes change output, with change amount below minimum balance'
		if sourceAccount in self._balanceRefCounts:
			return False, "source account is linked to an outstanding trade offer or pending exchange and can't be spent until the trade is completed or expires"
		return True, ''
	def _apply_ForwardToFutureNetworkVersion(self, txID, sourceAccount, amount, maxBlock):
		available = self._consumeAccount(sourceAccount)
		self._totalForwarded += amount
		if available > amount:
			self._addAccount((txID, 1), available - amount)

	def checkTransaction(self, transactionType, outputs, transactionDetails):
		methodName = '_check_' + transactionType
		try:
			method = getattr(self, methodName)
		except AttributeError as e:
			raise InvalidTransactionType(e)
		try:
			return method(outputs, **transactionDetails)
		except TypeError as e:
			raise InvalidTransactionParameters(e)
	def applyTransaction(self, transactionType, txID, outputs, transactionDetails):
		assert self.checkTransaction(transactionType, outputs, transactionDetails)[0] == True
		methodName = '_apply_' + transactionType
		method = getattr(self, methodName)
		method(txID, **transactionDetails)

