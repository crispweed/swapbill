from __future__ import print_function
from SwapBill import TradeOfferHeap, TradeOffer, Balances, Amounts, KeyPair
from SwapBill.Amounts import e

# these assertions are used to communicate whether or not a transaction is possible to the user
class BadlyFormedTransaction(Exception):
	pass
class TransactionFailsAgainstCurrentState(Exception):
	pass
class InsufficientFundsForTransaction(Exception):
	pass

# these should normally indicate some internal error
# e.g. transaction mappings don't correspond the state transaction methods
# or client main transaction setup code is incorrect
class InvalidTransactionParameters(Exception):
	pass
class InvalidTransactionType(Exception):
	pass

class LTCSellBacker(object):
	pass
class PendingPay(object):
	pass

class State(object):
	def __init__(self, protocolParams, seedAccount=None, seedAmount=0):
		## state is initialised at the start of the block with startBlockIndex
		self._protocolParams = protocolParams
		startBlockIndex = protocolParams['startBlock']
		self._currentBlockIndex = startBlockIndex
		self._balances = Balances.Balances()
		if seedAccount is not None:
			self._balances.add(seedAccount, seedAmount)
		self._totalCreated = 0
		self._totalForwarded = 0
		self._hostCoinBuys = TradeOfferHeap.Heap(startBlockIndex, False) # lower exchange rate is better offer
		self._hostCoinSells = TradeOfferHeap.Heap(startBlockIndex, True) # higher exchange rate is better offer
		self._nextExchangeIndex = 0
		self._pendingExchanges = {}
		self._nextBackerIndex = 0
		self._hostCoinSellBackers = {}
		self._nextPendingPayIndex = 0
		self._pendingPays = {}

	def parametersMatch(self, protocolParams):
		return protocolParams == self._protocolParams

	def advanceToNextBlock(self):
		expired = self._hostCoinBuys.advanceToNextBlock()
		for buy in expired:
			self._balances.addStateChange(buy.refundAccount)
			self._balances.addTo_Forwarded(buy.refundAccount, buy._swapBillOffered)
			self._balances.removeRef(buy.refundAccount)
		expired = self._hostCoinSells.advanceToNextBlock()
		for sell in expired:
			self._balances.addStateChange(sell.receivingAccount)
			self._balances.addTo_Forwarded(sell.receivingAccount, self._protocolParams['minimumSwapBillBalance'] + sell._swapBillDeposit)
			if sell.isBacked:
				self._balances.addTo_Forwarded(sell.receivingAccount, sell.backingSwapBill)
				self._balances.addStateChange(sell.backingReceiveAccount)
				self._balances.removeRef(sell.backingReceiveAccount)
			self._balances.removeRef(sell.receivingAccount)
		# ** currently iterates through all pending exchanges each block added
		# are there scaling issues with this?
		toDelete = []
		for key in self._pendingExchanges:
			exchange = self._pendingExchanges[key]
			if exchange.expiry == self._currentBlockIndex:
				# refund buyers funds locked up in the exchange, plus sellers deposit (as penalty for failing to make exchange)
				self._balances.addTo_Forwarded(exchange.buyerAccount, exchange.swapBillAmount + exchange.swapBillDeposit)
				self._balances.addStateChange(exchange.buyerAccount)
				self._balances.addStateChange(exchange.sellerAccount)
				self._balances.removeRef(exchange.buyerAccount)
				self._balances.removeRef(exchange.sellerAccount)
				toDelete.append(key)
		for key in toDelete:
			self._pendingExchanges.pop(key)
		# ** currently iterates through all entries each block added
		# are there scaling issues with this?
		toDelete = []
		for key in self._hostCoinSellBackers:
			backer = self._hostCoinSellBackers[key]
			if backer.expiry == self._currentBlockIndex:
				# refund remaining amount
				self._balances.addTo_Forwarded(backer.refundAccount, backer.backingAmount)
				self._balances.addStateChange(backer.refundAccount)
				self._balances.removeRef(backer.refundAccount)
				toDelete.append(key)
		for key in toDelete:
				self._hostCoinSellBackers.pop(key)
		toDelete = []
		for key in self._pendingPays:
			pendingPay = self._pendingPays[key]
			if pendingPay.expiry == self._currentBlockIndex:
				self._balances.addTo_Forwarded(pendingPay.refundAccount, pendingPay.amount)
				self._balances.removeRef(pendingPay.refundAccount)
				self._balances.removeRef(pendingPay.destinationAccount)
				toDelete.append(key)
		for key in toDelete:
				self._pendingPays.pop(key)
		self._currentBlockIndex += 1

	def _matchOffersAndAddExchange(self, buy, sell):
		assert buy.refundAccount in self._balances.changeCounts
		assert sell.receivingAccount in self._balances.changeCounts
		exchange = TradeOffer.MatchOffers(protocolParams=self._protocolParams, buy=buy, sell=sell)
		self._balances.addStateChange(sell.receivingAccount)
		self._balances.addStateChange(buy.refundAccount)
		exchange.expiry = self._currentBlockIndex + self._protocolParams['blocksForExchangeCompletion']
		exchange.buyerLTCReceive = buy.hostCoinReceiveAddress
		exchange.buyerAccount = buy.refundAccount
		exchange.sellerAccount = sell.receivingAccount
		exchange.backerIndex= -1
		if sell.isBacked:
			assert sell.backingSwapBill >= exchange.swapBillAmount
			sell.backingSwapBill -= exchange.swapBillAmount
			self._balances.addTo_Forwarded(sell.backingReceiveAccount, exchange.swapBillAmount)
			self._balances.addStateChange(sell.backingReceiveAccount)
			exchange.backerIndex = sell.backerIndex
		key = self._nextExchangeIndex
		self._nextExchangeIndex += 1
		# the existing account refs from buy and sell details transfer into the exchange object
		# and then we add new refs for offer remainders as necessary
		# backing receiving account ref remains with sell by default
		self._pendingExchanges[key] = exchange
		if buy.hasBeenConsumed():
			buy = None
		else:
			self._balances.addRef(buy.refundAccount)
		if sell.hasBeenConsumed():
			# seller (or backer) gets seed amount (which was locked up implicitly in the sell offer) refunded
			backer = self._hostCoinSellBackers.get(exchange.backerIndex, None)
			if backer is None:
				# unbacked exchange, or backer expired
				self._balances.addTo_Forwarded(sell.receivingAccount, self._protocolParams['minimumSwapBillBalance'])
			else:
				#refund back into the backer object
				backer.backingAmount += self._protocolParams['minimumSwapBillBalance']
			if sell.isBacked:
				self._balances.removeRef(sell.backingReceiveAccount)
			sell = None
		else:
			self._balances.addRef(sell.receivingAccount)
		return buy, sell

	def _newBuyOffer(self, buy):
		toReAdd = []
		while True:
			if self._hostCoinSells.empty() or not TradeOffer.OffersMeetOrOverlap(buy=buy, sell=self._hostCoinSells.peekCurrentBest()):
				# no more matchable sell offers
				self._hostCoinBuys.addOffer(buy)
				break
			sell = self._hostCoinSells.popCurrentBest()
			try:
				buyRemainder, sellRemainder = self._matchOffersAndAddExchange(buy=buy, sell=sell)
			except TradeOffer.OfferIsBelowMinimumExchange:
				toReAdd.append(sell)
				continue
			if sellRemainder is not None:
				toReAdd.append(sellRemainder)
			if buyRemainder is not None:
				buy = buyRemainder
				continue # (remainder can match against another offer)
			# new offer is fully matched
			break
		for entry in toReAdd:
			self._hostCoinSells.addOffer(entry)
	def _newSellOffer(self, sell):
		toReAdd = []
		while True:
			if self._hostCoinBuys.empty() or not TradeOffer.OffersMeetOrOverlap(buy=self._hostCoinBuys.peekCurrentBest(), sell=sell):
				# no more matchable buy offers
				self._hostCoinSells.addOffer(sell)
				break
			buy = self._hostCoinBuys.popCurrentBest()
			try:
				buyRemainder, sellRemainder = self._matchOffersAndAddExchange(buy=buy, sell=sell)
			except TradeOffer.OfferIsBelowMinimumExchange:
				toReAdd.append(buy)
				continue
			if buyRemainder is not None:
				toReAdd.append(buyRemainder)
			if sellRemainder is not None:
				sell = sellRemainder
				continue # (remainder can match against another offer)
			# new offer is fully matched
			break
		for entry in toReAdd:
			self._hostCoinBuys.addOffer(entry)

	def _checkChange(self, change):
		if change < 0:
			raise InsufficientFundsForTransaction()
		if change > 0 and change < self._protocolParams['minimumSwapBillBalance']:
			raise InsufficientFundsForTransaction()

	def _fundedTransaction_Burn(self, txID, swapBillInput, amount, outputs):
		assert outputs == ('destination',)
		if swapBillInput + amount < self._protocolParams['minimumSwapBillBalance']:
			raise BadlyFormedTransaction('burn output is below minimum balance')
		if txID is None:
			return
		self._totalCreated += amount
		return swapBillInput + amount

	def _fundedTransaction_Pay(self, txID, swapBillInput, amount, maxBlock, outputs):
		assert outputs == ('change', 'destination')
		if amount < self._protocolParams['minimumSwapBillBalance']:
			raise BadlyFormedTransaction('amount is below minimum balance')
		if maxBlock < self._currentBlockIndex:
			raise TransactionFailsAgainstCurrentState('max block for transaction has been exceeded')
		change = swapBillInput - amount
		self._checkChange(change)
		if txID is None:
			return
		self._balances.add((txID, 2), amount)
		return change

	def _fundedTransaction_BuyOffer(self, txID, swapBillInput, swapBillOffered, exchangeRate, receivingAddress, maxBlock, outputs):
		assert outputs == ('hostCoinBuy',)
		if exchangeRate == 0 or exchangeRate >= Amounts.percentDivisor:
			raise BadlyFormedTransaction('invalid exchange rate value')
		try:
			buy = TradeOffer.BuyOffer(protocolParams=self._protocolParams, swapBillOffered=swapBillOffered, rate=exchangeRate)
		except TradeOffer.OfferIsBelowMinimumExchange:
			raise BadlyFormedTransaction('does not satisfy minimum exchange amount')
		if maxBlock < self._currentBlockIndex:
			raise TransactionFailsAgainstCurrentState('max block for transaction has been exceeded')
		change = swapBillInput - swapBillOffered
		self._checkChange(change)
		if txID is None:
			return
		refundAccount = (txID, 1) # same as change account and already created
		#print("refundAccount:", refundAccount)
		self._balances.addFirstRef(refundAccount)
		buy.hostCoinReceiveAddress = receivingAddress
		buy.refundAccount = refundAccount
		buy.expiry = maxBlock
		self._newBuyOffer(buy)
		return change

	def _fundedTransaction_SellOffer(self, txID, swapBillInput, hostCoinOffered, exchangeRate, maxBlock, outputs):
		assert outputs == ('hostCoinSell',)
		if exchangeRate == 0 or exchangeRate >= Amounts.percentDivisor:
			raise BadlyFormedTransaction('invalid exchange rate value')
		swapBillDeposit = TradeOffer.DepositRequiredForLTCSell(protocolParams=self._protocolParams, rate=exchangeRate, hostCoinOffered=hostCoinOffered)
		try:
			sell = TradeOffer.SellOffer(protocolParams=self._protocolParams, swapBillDeposit=swapBillDeposit, hostCoinOffered=hostCoinOffered, rate=exchangeRate)
		except TradeOffer.OfferIsBelowMinimumExchange:
			raise BadlyFormedTransaction('does not satisfy minimum exchange amount')
		if maxBlock < self._currentBlockIndex:
			raise TransactionFailsAgainstCurrentState('max block for transaction has been exceeded')
		# note that a seed amount (minimum balance) is assigned to the sell offer, in addition to the deposit
		change = swapBillInput - swapBillDeposit - self._protocolParams['minimumSwapBillBalance']
		self._checkChange(change)
		if txID is None:
			return
		receivingAccount = (txID, 1) # same as change account and already created
		self._balances.addFirstRef(receivingAccount)
		sell.isBacked = False
		sell.receivingAccount = receivingAccount
		sell.expiry = maxBlock
		self._newSellOffer(sell)
		return change

	def _fundedTransaction_BackLTCSells(self, txID, swapBillInput, backingAmount, transactionsBacked, commission, hostCoinReceiveAddress, maxBlock, outputs):
		assert outputs == ('hostCoinSellBacker',)
		if commission == 0 or commission >= Amounts.percentDivisor:
			raise BadlyFormedTransaction('invalid commission value')
		if backingAmount < self._protocolParams['minimumSwapBillBalance']:
			raise BadlyFormedTransaction('backing amount is below minimum balance')
		transactionMax = backingAmount // transactionsBacked
		if transactionMax < self._protocolParams['minimumSwapBillBalance']:
			raise BadlyFormedTransaction('transaction max is below minimum balance')
		if maxBlock < self._currentBlockIndex:
			raise TransactionFailsAgainstCurrentState('max block for transaction has been exceeded')
		change = swapBillInput - backingAmount
		self._checkChange(change)
		if txID is None:
			return
		refundAccount = (txID, 1) # same as change account and already created
		self._balances.addFirstRef(refundAccount)
		backer = LTCSellBacker()
		backer.backingAmount = backingAmount
		backer.transactionMax = transactionMax
		backer.commission = commission
		backer.hostCoinReceiveAddress = hostCoinReceiveAddress
		backer.refundAccount = refundAccount
		backer.expiry = maxBlock
		key = self._nextBackerIndex
		self._nextBackerIndex += 1
		self._hostCoinSellBackers[key] = backer
		return change

	def _fundedTransaction_BackedSellOffer(self, txID, swapBillInput, exchangeRate, backerIndex, backerHostCoinReceiveAddress, hostCoinOfferedPlusCommission, outputs):
		assert outputs == ('sellerReceive',)
		if exchangeRate == 0 or exchangeRate >= Amounts.percentDivisor:
			raise BadlyFormedTransaction('invalid exchange rate value')
		if not backerIndex in self._hostCoinSellBackers:
			raise TransactionFailsAgainstCurrentState('no ltc sell backer with the specified index')
		backer = self._hostCoinSellBackers[backerIndex]
		# we make sure that commission is rounded down here, to make this correspond with commission added to exchange amounts specified by user
		commission = hostCoinOfferedPlusCommission * backer.commission // (Amounts.percentDivisor + backer.commission)
		hostCoinOffered = hostCoinOfferedPlusCommission - commission
		swapBillDeposit = TradeOffer.DepositRequiredForLTCSell(protocolParams=self._protocolParams, rate=exchangeRate, hostCoinOffered=hostCoinOffered)
		try:
			sell = TradeOffer.SellOffer(protocolParams=self._protocolParams, swapBillDeposit=swapBillDeposit, hostCoinOffered=hostCoinOffered, rate=exchangeRate)
		except TradeOffer.OfferIsBelowMinimumExchange:
			raise TransactionFailsAgainstCurrentState('does not satisfy minimum exchange amount')
		if backerHostCoinReceiveAddress != backer.hostCoinReceiveAddress:
			raise TransactionFailsAgainstCurrentState('destination address does not match backer receive address for ltc sell backer with the specified index')
		swapBillEquivalent = TradeOffer.ltcToSwapBill_RoundedUp(rate=exchangeRate, ltc=hostCoinOffered)
		# note that minimum balance amount is implicitly seeded into sell offers
		transactionBackingAmount = self._protocolParams['minimumSwapBillBalance'] + swapBillDeposit + swapBillEquivalent
		if transactionBackingAmount > backer.transactionMax:
			raise TransactionFailsAgainstCurrentState('backing amount required for this transaction is larger than the maximum allowed per transaction by the backer')
		backerChange = backer.backingAmount - transactionBackingAmount
		if backerChange < 0:
			raise TransactionFailsAgainstCurrentState('insufficient backing funds')
		if backerChange > 0 and backerChange < self._protocolParams['minimumSwapBillBalance']:
			raise TransactionFailsAgainstCurrentState('insufficient backing funds')
		if txID is None:
			return
		backer.backingAmount -= transactionBackingAmount
		receivingAccount = (txID, 1) # same as change account and already created
		self._balances.addFirstRef(receivingAccount)
		self._balances.addRef(backer.refundAccount)
		sell.receivingAccount = backer.refundAccount
		sell.isBacked = True
		sell.backingSwapBill = swapBillEquivalent
		sell.backingReceiveAccount = receivingAccount
		sell.backerIndex = backerIndex
		sell.expiry = 0xffffffff
		self._newSellOffer(sell)
		return swapBillInput

	def _fundedTransaction_PayOnRevealSecret(self, txID, swapBillInput, amount, maxBlock, secretAddress, outputs):
		assert outputs == ('change', 'destination')
		if amount < self._protocolParams['minimumSwapBillBalance']:
			raise BadlyFormedTransaction('amount is below minimum balance')
		if maxBlock < self._currentBlockIndex:
			raise TransactionFailsAgainstCurrentState('max block for transaction has been exceeded')
		change = swapBillInput - amount
		self._checkChange(change)
		if txID is None:
			return
		changeAccount = (txID, 1) # already created
		destinationAccount = (txID, 2)
		self._balances.add(destinationAccount, 0)
		self._balances.addFirstRef(changeAccount)
		self._balances.addFirstRef(destinationAccount)
		pendingPay = PendingPay()
		pendingPay.amount = amount
		pendingPay.destinationAccount = destinationAccount
		pendingPay.refundAccount = changeAccount
		pendingPay.expiry = maxBlock
		pendingPay.secretHash = secretAddress
		pendingPay.confirmedOnBlock = self._currentBlockIndex
		key = self._nextPendingPayIndex
		self._nextPendingPayIndex += 1
		self._pendingPays[key] = pendingPay
		return change

	def _fundedTransaction_ForwardToFutureNetworkVersion(self, txID, swapBillInput, amount, maxBlock, outputs):
		assert outputs == ('change',)
		if amount < self._protocolParams['minimumSwapBillBalance']:
			raise BadlyFormedTransaction('amount is below minimum balance')
		if maxBlock < self._currentBlockIndex:
			raise TransactionFailsAgainstCurrentState('max block for transaction has been exceeded')
		if swapBillInput < amount:
			raise InsufficientFundsForTransaction()
		change = swapBillInput - amount
		self._checkChange(change)
		if txID is None:
			return
		self._totalForwarded += amount
		return change

	def _unfundedTransaction_ExchangeCompletion(self, txID, pendingExchangeIndex, destinationAddress, destinationAmount, outputs):
		assert outputs == ()
		if not pendingExchangeIndex in self._pendingExchanges:
			raise TransactionFailsAgainstCurrentState('no pending exchange with the specified index')
		exchange = self._pendingExchanges[pendingExchangeIndex]
		if destinationAddress != exchange.buyerLTCReceive:
			raise TransactionFailsAgainstCurrentState('destination account does not match destination for pending exchange with the specified index')
		if destinationAmount < exchange.ltc:
			raise TransactionFailsAgainstCurrentState('amount is less than required payment amount')
		if txID is None:
			if destinationAmount > exchange.ltc:
				raise TransactionFailsAgainstCurrentState('amount is greater than required payment amount')
			return
		# the seller completed their side of the exchange, so credit them the buyers swapbill
		# and the seller is also refunded their deposit here
		backer = self._hostCoinSellBackers.get(exchange.backerIndex, None)
		if backer is None:
			# unbacked exchange, or backer expired
			self._balances.addTo_Forwarded(exchange.sellerAccount, exchange.swapBillAmount + exchange.swapBillDeposit)
		else:
			#refund back into the backer object
			backer.backingAmount += exchange.swapBillAmount + exchange.swapBillDeposit
		self._balances.addStateChange(exchange.buyerAccount)
		self._balances.addStateChange(exchange.sellerAccount)
		self._balances.removeRef(exchange.buyerAccount)
		#if not exchange.buyerAccount in self._balances.balances:
			#print('removed account:', exchange.buyerAccount)
		self._balances.removeRef(exchange.sellerAccount)
		self._pendingExchanges.pop(pendingExchangeIndex)

	def _unfundedTransaction_RevealPendingPaymentSecret(self, txID, pendingPayIndex, publicKeySecret, outputs):
		assert outputs == ()
		if not pendingPayIndex in self._pendingPays:
			raise TransactionFailsAgainstCurrentState('no pending payment with the specified index')
		pay = self._pendingPays[pendingPayIndex]
		if KeyPair.PublicKeyToPubKeyHash(publicKeySecret) != pay.secretHash:
			raise TransactionFailsAgainstCurrentState('the supplied public key does not match the public key hash associated with the pending payment')
		if txID is None:
			return		
		self._balances.addTo_Forwarded(pay.destinationAccount, pay.amount)
		self._balances.removeRef(pay.refundAccount)
		self._balances.removeRef(pay.destinationAccount)
		self._pendingPays.pop(pendingPayIndex)

	def checkFundedTransaction(self, transactionType, sourceAccounts, transactionDetails, outputs):
		try:
			method = getattr(self, '_fundedTransaction_' + transactionType)
		except AttributeError as e:
			raise InvalidTransactionType(e)
		swapBillInput = 0
		for sourceAccount in sourceAccounts:
			if not self._balances.accountHasBalance(sourceAccount):
				continue
			swapBillInput += self._balances.balanceFor(sourceAccount)
		method(txID=None, swapBillInput=swapBillInput, outputs=outputs, **transactionDetails)
	def applyFundedTransaction(self, transactionType, txID, sourceAccounts, transactionDetails, outputs):
		try:
			method = getattr(self, '_fundedTransaction_' + transactionType)
		except AttributeError as e:
			return 'bad transaction type'
		swapBillInput = 0
		for sourceAccount in sourceAccounts:
			swapBillInput += self._balances.consumeContents_IfAny(sourceAccount)
		errorReport = None
		changeAccount = (txID, 1)
		self._balances.add(changeAccount, 0)
		change = swapBillInput
		try:
			# note that source accounts can potentially be credited during this call
			change = method(txID=txID, swapBillInput=swapBillInput, outputs=outputs, **transactionDetails)
		except (BadlyFormedTransaction, TransactionFailsAgainstCurrentState) as e:
			errorReport = str(e)
		except InsufficientFundsForTransaction:
			errorReport = 'insufficient funds'
		assert change == 0 or change >= self._protocolParams['minimumSwapBillBalance']
		self._balances.addTo(changeAccount, change)
		self._balances.consumeAndForward(sourceAccounts, changeAccount)
		self._balances.removeIfZeroBalanceAndUnreferenced(changeAccount)
		return errorReport

	def checkUnfundedTransaction(self, transactionType, transactionDetails, outputs):
		try:
			method = getattr(self, '_unfundedTransaction_' + transactionType)
		except AttributeError as e:
			raise InvalidTransactionType(e)
		method(txID=None, outputs=outputs, **transactionDetails)
	def applyUnfundedTransaction(self, transactionType, txID, transactionDetails, outputs):
		try:
			method = getattr(self, '_unfundedTransaction_' + transactionType)
		except AttributeError as e:
			return 'bad transaction type'
		try:
			method(txID=txID, outputs=outputs, **transactionDetails)
		except (BadlyFormedTransaction, TransactionFailsAgainstCurrentState) as e:
			return str(e)
		except InsufficientFundsForTransaction:
			return 'insufficient funds'
		return None

	def checkTransaction(self, transactionType, sourceAccounts, transactionDetails, outputs):
		if sourceAccounts is None:
			self.checkUnfundedTransaction(transactionType, transactionDetails, outputs)
		else:
			self.checkFundedTransaction(transactionType, sourceAccounts, transactionDetails, outputs)
	def applyTransaction(self, transactionType, txID, sourceAccounts, transactionDetails, outputs):
		if sourceAccounts is None:
			return self.applyUnfundedTransaction(transactionType, txID, transactionDetails, outputs)
		return self.applyFundedTransaction(transactionType, txID, sourceAccounts, transactionDetails, outputs)

	def calculateBackerMaximumExchange(self, backer):
		maximumExchange = backer.transactionMax - self._protocolParams['minimumSwapBillBalance']
		depositDivisor = self._protocolParams['depositDivisor']
		maximumExchange *= depositDivisor
		maximumExchange //= (depositDivisor + 1)
		return maximumExchange

	def calculateBackerMaximumExchangeInHostCoin(self, backer, rate):
		maximumExchange = self.calculateBackerMaximumExchange(backer)
		return TradeOffer.swapBillToLTC_RoundedDown(rate, maximumExchange)
	
