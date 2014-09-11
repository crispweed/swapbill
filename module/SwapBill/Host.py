from __future__ import print_function
import os, sys
if sys.version > '3':
	long = int
from os import path
from SwapBill import RawTransaction, Address, Amounts, RPC, Util
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
		self._submittedTransactionsFileName = submittedTransactionsLogFileName

	def getAddressVersion(self):
		return self._addressVersion

# unspents, addresses, transaction encode and send

	def getUnspent(self):
		# lowest level getUnspent interface
		result = []
		allUnspent = self._rpcHost.call('listunspent')
		def negativeConfirmations(entry):
			return -entry['confirmations']
		allUnspent.sort(key = negativeConfirmations)
		for output in allUnspent:
			if not 'address' in output: ## is this check required?
				continue
			filtered = {}
			for key in ('txid', 'vout', 'scriptPubKey'):
				filtered[key] = output[key]
			filtered['address'] = Address.ToPubKeyHash(self._addressVersion, output['address'])
			amount_FloatFromJSON = output['amount']
			amount_TenthsOfSatoshis = long(amount_FloatFromJSON * 1e9)
			# round to nearest, after conversion to integer
			amount_Satoshis = (amount_TenthsOfSatoshis + 5) // 10
			filtered['amount'] = amount_Satoshis
			result.append(filtered)
		return result

	def getManagedAddress(self):
		return Address.ToPubKeyHash(self._addressVersion, self._rpcHost.call('getnewaddress'))

	def signAndSend(self, unsignedTransactionHex, privateKeys, maximumSignedSize):
		# lowest level transaction send interface
		signingResult = self._rpcHost.call('signrawtransaction', unsignedTransactionHex)
		if signingResult['complete'] != True:
			privateKeys_WIF = []
			for privateKey in privateKeys:
				privateKeys_WIF.append(Address.PrivateKeyToWIF(privateKey, self._privateKeyAddressVersion))
			signingResult = self._rpcHost.call('signrawtransaction', signingResult['hex'], None, privateKeys_WIF)
		if signingResult['complete'] != True:
			#print(unsignedTransactionHex)
			#print(privateKeys)
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
			self._cachedBlockData = Util.fromHex(self._rpcHost.call('getblock', blockHash, False))
			self._cachedBlockDataHash = blockHash
		return self._cachedBlockData

	def getNextBlockHash(self, blockHash):
		block = self._getBlock_Cached(blockHash)
		return block.get('nextblockhash', None)
	def getBlockTransactions(self, blockHash):
		block = self._getBlock_Cached(blockHash)
		transactionIDs = block['tx']
		blockData = self._getBlockData_Cached(blockHash)
		rawTransactions = RawTransaction.GetTransactionsInBlock(blockData)
		assert len(rawTransactions) == len(transactionIDs)
		assert len(transactionIDs) >= 1
		return list(zip(transactionIDs, rawTransactions))[1:]

	def getMemPoolTransactions(self):
		mempool = self._rpcHost.call('getrawmempool')
		result = []
		for txHash in mempool:
			txHex = self._rpcHost.call('getrawtransaction', txHash)
			result.append((txHash, Util.fromHex(txHex)))
		return result

# convenience

	def formatAccountForEndUser(self, account):
		txID, vOut = account
		return txID + ':' + str(vOut)
