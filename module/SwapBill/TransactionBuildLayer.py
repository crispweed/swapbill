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

	def getActiveAccount(self, state):
		best = None
		bestAmount = 0
		for account in self._ownedAccounts.spendableAccounts:
			assert state.getSpendableAmount(account) > 0
			amount = state._balances[account]
			if amount > bestAmount:
				best = account
				bestAmount = amount
		if bestAmount == 0:
			raise ExceptionReportedToUser('No active swapbill balance currently available (you may need to wait for a transaction in progress to complete).')
		self._scriptPubKeyLookup[best] = self._ownedAccounts.spendableAccounts[best][2]
		self._privateKeys.append(self._ownedAccounts.spendableAccounts[best][1])
		return best

	def getAllOwnedAndSpendable(self, state):
		result = []
		for account in self._ownedAccounts.spendableAccounts:
			assert state.getSpendableAmount(account) > 0
			self._scriptPubKeyLookup[account] = self._ownedAccounts.spendableAccounts[account][2]
			self._privateKeys.append(self._ownedAccounts.spendableAccounts[account][1])
			result.append(account)
		return result

	def sendTransaction(self, tx):
		# higher level transaction send interface
		unsignedData = RawTransaction.Create(tx, self._scriptPubKeyLookup)
		unsignedHex = RawTransaction.ToHex(unsignedData)
		return self._host.signAndSend(unsignedHex, self._privateKeys)
