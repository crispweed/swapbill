from __future__ import print_function
import os
from os import path
from SwapBill import RawTransaction, Address, Amounts, RPC
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

class SigningFailed(ExceptionReportedToUser):
	pass
class MaximumSignedSizeExceeded(Exception):
	pass

class Host(object):
	def __init__(self, rpcHost, addressVersion, privateKeyAddressVersion, submittedTransactionsLogFileName):
		self._rpcHost = rpcHost
		self._addressVersion = addressVersion
		self._privateKeyAddressVersion = privateKeyAddressVersion
		self._cachedBlockHash = None
		self._cachedBlockDataHash = None
		#blockHashForBlockZero = self._rpcHost.call('getblockhash', 0)
		#self._hasExtendTransactionsInBlockQuery = True
		#try:
			#transactionsInBlockZero = self._rpcHost.call('getrawtransactionsinblock', blockHashForBlockZero)
		##except RPC.MethodNotFoundException:
		#except RPC.RPCFailureException: # ** we get a different RPC error for this on Windows
			#self._hasExtendTransactionsInBlockQuery = False
		self._submittedTransactionsFileName = submittedTransactionsLogFileName

# unspents, addresses, transaction encode and send

	def getUnspent(self):
		## lowest level getUnspent interface
		result = []
		allUnspent = self._rpcHost.call('listunspent')
		for output in allUnspent:
			if not 'address' in output: ## is this check required?
				continue
			filtered = {}
			for key in ('txid', 'vout', 'scriptPubKey'):
				filtered[key] = output[key]
			filtered['address'] = Address.ToPubKeyHash(self._addressVersion, output['address'])
			filtered['amount'] = Amounts.ToSatoshis(output['amount'])
			result.append(filtered)
		return result

	def getNewNonSwapBillAddress(self):
		return Address.ToPubKeyHash(self._addressVersion, self._rpcHost.call('getnewaddress'))

	def signAndSend(self, unsignedTransactionHex, privateKeys, maximumSignedSize):
		#print('\t\tunsignedTransactionHex =', unsignedTransactionHex.__repr__())
		#print('\t\tprivateKeys =', privateKeys.__repr__())
		#print('\t\tmaximumSignedSize =', maximumSignedSize.__repr__())
		#return None
		## lowest level transaction send interface
		signingResult = self._rpcHost.call('signrawtransaction', unsignedTransactionHex)
		if signingResult['complete'] != True:
			privateKeys_WIF = []
			for privateKey in privateKeys:
				privateKeys_WIF.append(Address.PrivateKeyToWIF(privateKey, self._privateKeyAddressVersion))
			signingResult = self._rpcHost.call('signrawtransaction', signingResult['hex'], None, privateKeys_WIF)
		if signingResult['complete'] != True:
			raise SigningFailed("RPC call to signrawtransaction did not set 'complete' to True")
		signedHex = signingResult['hex']
		byteSize = len(signedHex) / 2
		if byteSize > maximumSignedSize:
			raise MaximumSignedSizeExceeded()
		try:
			txID = self._rpcHost.call('sendrawtransaction', signedHex)
		except RPC.RPCFailureException as e:
			raise ExceptionReportedToUser('RPC error sending signed transaction: ' + str(e))
		with open(self._submittedTransactionsFileName, mode='a') as f:
			f.write(txID)
			f.write('\n')
			f.write(signedHex)
			f.write('\n')
		return txID

# block chain tracking, transaction stream and decoding

	def getBlockHashAtIndexOrNone(self, blockIndex):
		try:
			return self._rpcHost.call('getblockhash', blockIndex)
		except RPC.RPCFailureWithMessage as e:
			if str(e) == 'Block number out of range.':
				return None
		except RPC.RPCFailureException:
			pass
		raise ExceptionReportedToUser('Unexpected RPC error in call to getblockhash.')

	def _getBlock_Cached(self, blockHash):
		if self._cachedBlockHash != blockHash:
			self._cachedBlock = self._rpcHost.call('getblock', blockHash)
			self._cachedBlockHash = blockHash
		return self._cachedBlock
	def _getBlockData_Cached(self, blockHash):
		if self._cachedBlockDataHash != blockHash:
			self._cachedBlockData = RawTransaction.FromHex(self._rpcHost.call('getblock', blockHash, False))
			self._cachedBlockDataHash = blockHash
		return self._cachedBlockData

	def getNextBlockHash(self, blockHash):
		block = self._getBlock_Cached(blockHash)
		return block.get('nextblockhash', None)
	def getBlockTransactions(self, blockHash):
		result = []
		block = self._getBlock_Cached(blockHash)
		transactionIDs = block['tx']
		blockData = self._getBlockData_Cached(blockHash)
		rawTransactions = RawTransaction.GetTransactionsInBlock(blockData)
		assert len(rawTransactions) == len(transactionIDs)
		assert len(transactionIDs) >= 1
		for i in range(len(rawTransactions) - 1):
			result.append((transactionIDs[i + 1], rawTransactions[i + 1]))
		return result

	def getMemPoolTransactions(self):
		mempool = self._rpcHost.call('getrawmempool')
		result = []
		for txHash in mempool:
			txHex = self._rpcHost.call('getrawtransaction', txHash)
			result.append((txHash, RawTransaction.FromHex(txHex)))
		return result

# convenience

	def formatAddressForEndUser(self,  pubKeyHash):
		return Address.FromPubKeyHash(self._addressVersion, pubKeyHash)
	def addressFromEndUserFormat(self,  address):
		return Address.ToPubKeyHash(self._addressVersion, address)

	def formatAccountForEndUser(self, account):
		txID, vOut = account
		return txID + ':' + str(vOut)
