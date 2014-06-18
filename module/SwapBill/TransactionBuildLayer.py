from SwapBill import RawTransaction
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

class TransactionBuildLayer(object):
	def __init__(self, host, ownedAccounts):
		self._host = host
		self._ownedAccounts = ownedAccounts

	def startTransactionConstruction(self):
		self._scriptPubKeyLookup = {}
		self._privateKeys = []

	def getUnspent(self):
		## higher level interface that caches scriptPubKey for later lookup
		## this to be called once before each transaction send
		## (but can also be called without subsequent transaction send)
		amounts = []
		asInputs = []
		allUnspent = self._host.getUnspent()
		for output in allUnspent:
			key = (output['txid'], output['vout'])
			assert not key in self._scriptPubKeyLookup
			self._scriptPubKeyLookup[key] = output['scriptPubKey']
			amounts.append(output['amount'])
			asInputs.append((output['txid'], output['vout']))
		return amounts, asInputs

	def getSwapBillUnspent(self, state):
		result = []
		for account in self._ownedAccounts.accounts:
			if state._balances.balanceFor(account) > 0:
				result.append(account)
		result.sort()
		return result

	def swapBillUnspentUsed(self, account):
		self._scriptPubKeyLookup[account] = self._ownedAccounts.accounts[account][2]
		self._privateKeys.append(self._ownedAccounts.accounts[account][1])

	def checkIfThereIsAtLeastOneOutstandingTradeRef(self, state):
		return bool(self._ownedAccounts.tradeOfferChangeCounts)

	def sendTransaction(self, tx, maximumSignedSize):
		# higher level transaction send interface
		unsignedData = RawTransaction.Create(tx, self._scriptPubKeyLookup)
		unsignedHex = RawTransaction.ToHex(unsignedData)
		return self._host.signAndSend(unsignedHex, self._privateKeys, maximumSignedSize)
