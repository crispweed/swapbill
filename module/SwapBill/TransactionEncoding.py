from __future__ import print_function
import struct, binascii
from SwapBill import Address, HostTransaction, ControlAddressPrefix, Amounts, Util
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

class UnsupportedTransaction(Exception):
	pass
class NotValidSwapBillTransaction(Exception):
	pass

# for exchange rate and commission parameters
assert Amounts.percentBytes == 4

_fundedMappingByTypeCode = (
    ('Burn',
     'amount',
     ('destination',), ()
    ),
    ('Pay',
     ('amount', 6, 'maxBlock', 4),
     ('change','destination'), ()
    ),
    ('BuyOffer',
     ('swapBillOffered', 6, 'maxBlock', 4, 'exchangeRate', 4),
     ('hostCoinBuy',),
     (('receivingAddress', None),)
	),
    ('SellOffer',
     ('hostCoinOffered', 6, 'maxBlock', 4, 'exchangeRate', 4),
     ('hostCoinSell',),
     ()
	),
    ('BackLTCSells',
     ('backingAmount', 6, 'transactionsBacked', 3, 'maxBlock', 4, 'commission', 4),
     ('hostCoinSellBacker',),
     (('hostCoinReceiveAddress', None),)
	),
    ('BackedSellOffer',
     ('exchangeRate', 4, 'backerIndex', 6),
     ('sellerReceive',),
     (('backerHostCoinReceiveAddress', 'hostCoinOfferedPlusCommission'),)
	),
    ('PayOnRevealSecret',
     ('amount', 6, 'maxBlock', 4),
     ('change','destination'),
     (('secretAddress', None),)
    ),
	)

_forwardCompatibilityMapping = ('ForwardToFutureNetworkVersion', ('amount', 6, 'maxBlock', 4), ('change',), ())

_unfundedMappingByTypeCode = (
    ('ExchangeCompletion',
     ('pendingExchangeIndex', 6),
     (),
     (('destinationAddress', 'destinationAmount'),)
    ),
    ('RevealPendingPaymentSecret',
     ('pendingPayIndex', 6, 'publicKeySecret:Bytes', 64),
     (),
     ()
    ),
	)

_bytesSuffix = ':Bytes'

def _mappingFromTypeString(transactionType):
	for i, entry in enumerate(_fundedMappingByTypeCode):
		if transactionType == entry[0]:
			return i, entry
	for i, entry in enumerate(_unfundedMappingByTypeCode):
		if transactionType == entry[0]:
			return 128 + i, entry
	raise Exception('Unknown transaction type string', transactionType)
def _mappingFromTypeCode(typeCode):
	if typeCode < len(_fundedMappingByTypeCode):
		return _fundedMappingByTypeCode[typeCode]
	if typeCode < 128:
		return _forwardCompatibilityMapping
	typeCode -= 128
	if typeCode < len(_unfundedMappingByTypeCode):
		return _unfundedMappingByTypeCode[typeCode]
	raise UnsupportedTransaction()

def _encodeInt(value, numberOfBytes):
	if value < 0:
		raise ExceptionReportedToUser('Negative values are not allowed for transaction parameters.')
	result = b''
	for i in range(numberOfBytes):
		byteValue = value & 255
		value = value // 256
		result += struct.pack('<B', byteValue)
	if value > 0:
		raise ExceptionReportedToUser('Transaction parameter value exceeds supported range.')
	return result

def ToStateTransaction(tx):
	controlAddressData = tx.outputPubKeyHash(0)
	assert controlAddressData.startswith(ControlAddressPrefix.prefix)
	pos = len(ControlAddressPrefix.prefix)
	typeCode = Util.intFromBytes(controlAddressData[pos:pos+1])
	pos += 1
	mapping = _mappingFromTypeCode(typeCode)
	funded = (len(mapping[2]) > 0)
	transactionType = mapping[0]
	details = {}
	nextOutput = 1
	if type(mapping[1]) is tuple:
		controlAddressMapping = mapping[1]
		for i in range(len(controlAddressMapping) // 2):
			valueMapping = controlAddressMapping[i * 2]
			numberOfBytes = controlAddressMapping[i * 2 + 1]
			while pos + numberOfBytes > len(controlAddressData):
				controlAddressData += tx.outputPubKeyHash(nextOutput)
				nextOutput += 1
			data = controlAddressData[pos:pos + numberOfBytes]
			if valueMapping.endswith(_bytesSuffix):
				valueMapping = valueMapping[:-len(_bytesSuffix)]
				value = data
			else:
				value = Util.intFromBytes(data)
			details[valueMapping] = value
			pos += numberOfBytes
		assert pos <= len(controlAddressData)
	else:
		data = controlAddressData[pos:20]
		if data != struct.pack('<B', 0) * len(data):
			raise NotValidSwapBillTransaction
		amountMapping = mapping[1]
		details[amountMapping] = tx.outputAmount(0)
	sourceAccounts = None
	if funded:
		sourceAccounts = []
		for i in range(tx.numberOfInputs()):
			sourceAccounts.append((tx.inputTXID(i), tx.inputVOut(i)))
	outputs = mapping[2]
	destinations = mapping[3]
	nextOutput += len(outputs)
	for addressMapping, amountMapping in destinations:
		assert addressMapping is not None
		details[addressMapping] = tx.outputPubKeyHash(nextOutput)
		if amountMapping is not None:
			details[amountMapping] = tx.outputAmount(nextOutput)
		nextOutput += 1
	return transactionType, sourceAccounts, outputs, details

def _checkedAddOutputWithValue(tx, pubKeyHash, amount):
	if amount < 0:
		raise ExceptionReportedToUser('Negative output amounts are not permitted.')
	if amount >= 0x10000000000000000:
		raise ExceptionReportedToUser('Control address output amount exceeds supported range.')
	tx.addOutput(pubKeyHash, amount)

def FromStateTransaction(transactionType, sourceAccounts, outputs, outputPubKeyHashes, details):
	assert len(outputs) == len(outputPubKeyHashes)
	typeCode, mapping = _mappingFromTypeString(transactionType)
	tx = HostTransaction.InMemoryTransaction()
	#originalDetails = details
	#details = originalDetails.copy()
	funded = (len(mapping[2]) > 0)
	assert funded == (sourceAccounts is not None)
	if sourceAccounts is not None:
		for txID, vout in sourceAccounts:
			tx.addInput(txID, vout)
	controlData = ControlAddressPrefix.prefix + _encodeInt(typeCode, 1)
	controlAmount = 0
	if type(mapping[1]) is tuple:
		controlAddressMapping = mapping[1]
		for valueMapping, numberOfBytes in zip(controlAddressMapping[::2], controlAddressMapping[1::2]):
			if valueMapping.endswith(_bytesSuffix):
				valueMapping = valueMapping[:-len(_bytesSuffix)]
				data = details[valueMapping]
				assert len(data) == numberOfBytes
				controlData += details[valueMapping]
			else:
				data = details[valueMapping]
				controlData += _encodeInt(data, numberOfBytes)
			while len(controlData) > 20:
				_checkedAddOutputWithValue(tx, controlData[:20], 0)
				controlData = controlData[20:]
		assert len(controlData) <= 20
		controlAmount = 0
	else:
		controlAmount = details[mapping[1]]
	controlData += (20 - len(controlData)) * struct.pack('<B', 0)
	_checkedAddOutputWithValue(tx, controlData, controlAmount)
	expectedOutputs = mapping[2]
	assert expectedOutputs == outputs
	for pubKeyHash in outputPubKeyHashes:
		tx.addOutput(pubKeyHash, 0)
	destinations = mapping[3]
	for addressMapping, amountMapping in destinations:
		assert addressMapping is not None
		amount = 0 if amountMapping is None else details[amountMapping]
		_checkedAddOutputWithValue(tx, details[addressMapping], amount)
	return tx
