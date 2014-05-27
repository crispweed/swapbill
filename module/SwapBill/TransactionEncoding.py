from __future__ import print_function
import struct, binascii
from SwapBill import Address, HostTransaction, ControlAddressPrefix

class UnsupportedTransaction(Exception):
	pass
class NotValidSwapBillTransaction(Exception):
	pass

_mappingByTypeCode = (
    ('Burn', 0, ((0, 16), 'amount'), ('destination',), ()),
    ('Pay', 1, (('amount', 6, 'maxBlock', 4, None, 6), None), ('change','destination'), ()),
    ('LTCBuyOffer',
     1,
     (('swapBillOffered', 6, 'maxBlock', 4, 'exchangeRate', 4, None, 2), None),
     ('change', 'ltcBuy'),
     (('receivingAddress', None),)
	),
    ('LTCSellOffer',
     1,
     (('swapBillDesired', 6, 'maxBlock', 4, 'exchangeRate', 4, None, 2), None),
     ('change', 'ltcSell'),
     ()
	),
    ('LTCExchangeCompletion', 0, (('pendingExchangeIndex', 6, None, 10), None), (), (('destinationAddress', 'destinationAmount'),)),
    ('Collect', None, (('_numberOfSources', 2, None, 14), None), ('destination',), ()),
	)

_forwardCompatibilityMapping = ('ForwardToFutureNetworkVersion', 1, (('amount', 6, 'maxBlock', 4, None, 6), None), ('change',), ())

def _mappingFromTypeString(transactionType):
	for i in range(len(_mappingByTypeCode)):
		if transactionType == _mappingByTypeCode[i][0]:
			return i, _mappingByTypeCode[i]
	raise Exception('Unknown transaction type string', transactionType)
def _mappingFromTypeCode(typeCode):
	if typeCode < len(_mappingByTypeCode):
		return _mappingByTypeCode[typeCode]
	if typeCode < 128:
		return _forwardCompatibilityMapping
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
	result = b''
	for i in range(numberOfBytes):
		byteValue = value & 255
		value = value // 256
		result += struct.pack('<B', byteValue)
	assert value == 0
	return result

def ToStateTransaction(tx):
	controlAddressData = tx.outputPubKeyHash(0)
	assert controlAddressData.startswith(ControlAddressPrefix.prefix)
	assert len(ControlAddressPrefix.prefix) == 3
	typeCode = _decodeInt(controlAddressData[3:4])
	mapping = _mappingFromTypeCode(typeCode)
	transactionType = mapping[0]
	details = {}
	meta = {'_numberOfSources':mapping[1]}
	controlAddressMapping, amountMapping = mapping[2]
	pos = 4
	for i in range(len(controlAddressMapping) // 2):
		valueMapping = controlAddressMapping[i * 2]
		numberOfBytes = controlAddressMapping[i * 2 + 1]
		data = controlAddressData[pos:pos + numberOfBytes]
		if valueMapping == 0:
			if data != struct.pack('<B', 0) * numberOfBytes:
				raise NotValidSwapBillTransaction
		elif valueMapping is not None:
			value = _decodeInt(data)
			if valueMapping.startswith('_'):
				meta[valueMapping] = value
			else:
				details[valueMapping] = value
		pos += numberOfBytes
	assert pos == 20
	if amountMapping is not None:
		details[amountMapping] = tx.outputAmount(0)
	numberOfSources = meta['_numberOfSources']
	if numberOfSources > tx.numberOfInputs():
		raise NotValidSwapBillTransaction('not enough inputs, or bad meta data for number of inputs')
	if numberOfSources == 1:
		details['sourceAccount'] = (tx.inputTXID(0), tx.inputVOut(0))
	elif numberOfSources != 0:
		details['sourceAccounts'] = []
		for i in range(numberOfSources):
			details['sourceAccounts'].append((tx.inputTXID(i), tx.inputVOut(i)))
	outputs = mapping[3]
	destinations = mapping[4]
	for i in range(len(destinations)):
		addressMapping, amountMapping = destinations[i]
		assert addressMapping is not None
		if addressMapping is not None:
			details[addressMapping] = tx.outputPubKeyHash(1 + len(outputs) + i)
		if amountMapping is not None:
			details[amountMapping] = tx.outputAmount(1 + len(outputs) + i)
	return transactionType, outputs, details

def FromStateTransaction(transactionType, outputs, outputPubKeyHashes, originalDetails):
	assert len(outputs) == len(outputPubKeyHashes)
	typeCode, mapping = _mappingFromTypeString(transactionType)
	tx = HostTransaction.InMemoryTransaction()
	details = originalDetails.copy()
	if 'sourceAccount' in details:
		txID, vout = details['sourceAccount']
		tx.addInput(txID, vout)
	elif 'sourceAccounts' in details:
		for txID, vout in details['sourceAccounts']:
			tx.addInput(txID, vout)
	details['_numberOfSources'] = tx.numberOfInputs()
	if mapping[1] is not None:
		assert mapping[1] == details['_numberOfSources']
	details[None] = 0
	details[0] = 0
	controlAddressMapping, amountMapping = mapping[2]
	controlAddressData = ControlAddressPrefix.prefix + _encodeInt(typeCode, 1)
	for i in range(len(controlAddressMapping) // 2):
		valueMapping = controlAddressMapping[i * 2]
		numberOfBytes = controlAddressMapping[i * 2 + 1]
		controlAddressData += _encodeInt(details[valueMapping], numberOfBytes)
	assert len(controlAddressData) == 20
	tx.addOutput(controlAddressData, details[amountMapping])
	expectedOutputs = mapping[3]
	assert expectedOutputs == outputs
	for pubKeyHash in outputPubKeyHashes:
		tx.addOutput(pubKeyHash, 0)
	destinations = mapping[4]
	for addressMapping, amountMapping in destinations:
		assert addressMapping is not None
		tx.addOutput(details[addressMapping], details[amountMapping])
	transactionType_Check, outputs_Check, details_Check = ToStateTransaction(tx)
	assert transactionType_Check == transactionType
	assert outputs_Check == outputs
	assert details_Check == originalDetails
	return tx
