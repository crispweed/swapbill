from __future__ import print_function
import struct, binascii
from SwapBill import Address, HostTransaction, ControlAddressPrefix, Amounts
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

class UnsupportedTransaction(Exception):
	pass
class NotValidSwapBillTransaction(Exception):
	pass

# for exchange rate and commission parameters
assert Amounts.percentBytes == 4

_fundedMappingByTypeCode = (
    ('Burn', ((0, 17), 'amount'), ('destination',), ()),
    ('Pay', (('amount', 6, 'maxBlock', 4, None, 7), None), ('change','destination'), ()),
    ('LTCBuyOffer',
     (('swapBillOffered', 6, 'maxBlock', 4, 'exchangeRate', 4, None, 3), None),
     ('ltcBuy',),
     (('receivingAddress', None),)
	),
    ('LTCSellOffer',
     (('ltcOffered', 6, 'maxBlock', 4, 'exchangeRate', 4, None, 3), None),
     ('ltcSell',),
     ()
	),
    ('BackLTCSells',
     (('backingAmount', 6, 'transactionsBacked', 3, 'maxBlock', 4, 'commission', 4), None),
     ('ltcSellBacker',),
     (('ltcReceiveAddress', None),)
	),
    ('BackedLTCSellOffer',
     (('exchangeRate', 4, 'backerIndex', 6, None, 7), None),
     ('sellerReceive',),
     (('backerLTCReceiveAddress', 'ltcOfferedPlusCommission'),)
	),
	)

_forwardCompatibilityMapping = ('ForwardToFutureNetworkVersion', (('amount', 6, 'maxBlock', 4, None, 7), None), ('change',), ())

_unfundedMappingByTypeCode = (
    ('LTCExchangeCompletion',
     (('pendingExchangeIndex', 6, None, 11), None),
     (),
     (('destinationAddress', 'destinationAmount'),)
    ),
	)

def _mappingFromTypeString(transactionType):
	for i in range(len(_fundedMappingByTypeCode)):
		if transactionType == _fundedMappingByTypeCode[i][0]:
			return i, _fundedMappingByTypeCode[i]
	for i in range(len(_unfundedMappingByTypeCode)):
		if transactionType == _unfundedMappingByTypeCode[i][0]:
			return 128 + i, _unfundedMappingByTypeCode[i]
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

def _decodeInt(data):
	multiplier = 1
	result = 0
	for i in range(len(data)):
		byteValue = struct.unpack('<B', data[i:i + 1])[0]
		result += byteValue * multiplier
		multiplier = multiplier << 8
	return result

def _encodeInt(value, numberOfBytes):
	if value < 0:
		raise ExceptionReportedToUser('Negative values are not allowed for transaction parameters.')
	#print('value:', value)
	#print('numberOfBytes:', numberOfBytes)
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
	typeCode = _decodeInt(controlAddressData[pos:pos+1])
	mapping = _mappingFromTypeCode(typeCode)
	funded = (len(mapping[2]) > 0)
	transactionType = mapping[0]
	details = {}
	controlAddressMapping, amountMapping = mapping[1]
	pos += 1
	for i in range(len(controlAddressMapping) // 2):
		valueMapping = controlAddressMapping[i * 2]
		numberOfBytes = controlAddressMapping[i * 2 + 1]
		data = controlAddressData[pos:pos + numberOfBytes]
		if valueMapping == 0:
			if data != struct.pack('<B', 0) * numberOfBytes:
				raise NotValidSwapBillTransaction
		elif valueMapping is not None:
			value = _decodeInt(data)
			details[valueMapping] = value
		pos += numberOfBytes
	assert pos == 20
	if amountMapping is not None:
		details[amountMapping] = tx.outputAmount(0)
	sourceAccounts = None
	if funded:
		sourceAccounts = []
		for i in range(tx.numberOfInputs()):
			sourceAccounts.append((tx.inputTXID(i), tx.inputVOut(i)))
	outputs = mapping[2]
	destinations = mapping[3]
	for i in range(len(destinations)):
		addressMapping, amountMapping = destinations[i]
		assert addressMapping is not None
		if addressMapping is not None:
			details[addressMapping] = tx.outputPubKeyHash(1 + len(outputs) + i)
		if amountMapping is not None:
			details[amountMapping] = tx.outputAmount(1 + len(outputs) + i)
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
	originalDetails = details
	details = originalDetails.copy()
	funded = (len(mapping[2]) > 0)
	assert funded == (sourceAccounts is not None)
	if sourceAccounts is not None:
		for txID, vout in sourceAccounts:
			tx.addInput(txID, vout)
	details[None] = 0
	details[0] = 0
	controlAddressMapping, amountMapping = mapping[1]
	controlAddressData = ControlAddressPrefix.prefix + _encodeInt(typeCode, 1)
	for i in range(len(controlAddressMapping) // 2):
		valueMapping = controlAddressMapping[i * 2]
		numberOfBytes = controlAddressMapping[i * 2 + 1]
		controlAddressData += _encodeInt(details[valueMapping], numberOfBytes)
	assert len(controlAddressData) == 20
	_checkedAddOutputWithValue(tx, controlAddressData, details[amountMapping])
	expectedOutputs = mapping[2]
	assert expectedOutputs == outputs
	for pubKeyHash in outputPubKeyHashes:
		tx.addOutput(pubKeyHash, 0)
	destinations = mapping[3]
	for addressMapping, amountMapping in destinations:
		assert addressMapping is not None
		_checkedAddOutputWithValue(tx, details[addressMapping], details[amountMapping])
	return tx
