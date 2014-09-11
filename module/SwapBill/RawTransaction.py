import struct
from SwapBill import HostTransaction, Util

class NotSwapBillTransaction(Exception):
	pass
class NotEnoughOutputs(Exception):
	pass

class _RanOutOfData(Exception):
	pass

# Constants
OP_RETURN = b'\x6a'
OP_PUSHDATA1 = b'\x4c'
OP_DUP = b'\x76'
OP_HASH160 = b'\xa9'
OP_EQUALVERIFY = b'\x88'
OP_CHECKSIG = b'\xac'
OP_1 = b'\x51'
OP_2 = b'\x52'
OP_CHECKMULTISIG = b'\xae'

def _encodeVarInt(i):
	if i < 0xfd:
		return struct.pack("<B", i)
	elif i <= 0xffff:
		return b'\xfd' + struct.pack("<H", i)
	elif i <= 0xffffffff:
		return b'\xfe' + struct.pack("<L", i)
	else:
		return b'\xff' + struct.pack("<Q", i)

def _decodeVarInt(data, pos):
	if pos >= len(data):
		raise _RanOutOfData()
	result = Util.intFromBytes(data[pos:pos + 1])
	pos += 1
	if result < 253:
		return pos, result
	byteSize = 2 ** (result - 252)
	if pos + byteSize > len(data):
		raise _RanOutOfData()
	return pos + byteSize, Util.intFromBytes(data[pos:pos + byteSize])

def _opPush(i):
	if i < 0x4c:
		return struct.pack("<B", i)
	elif i <= 0xff:
		return b'\x4c' + struct.pack("<B", i)
	elif i <= 0xffff:
		return b'\x4d' + struct.pack("<H", i)
	else:
		return b'\x4e' + struct.pack("<L", i)

def ScriptPubKeyForPubKeyHash(pubKeyHash):
	assert type(pubKeyHash) == type(b'')
	assert len(pubKeyHash) == 20
	expectedScriptStart = OP_DUP
	expectedScriptStart += OP_HASH160
	expectedScriptStart += _opPush(20)
	expectedScriptEnd = OP_EQUALVERIFY
	expectedScriptEnd += OP_CHECKSIG
	return Util.toHex(expectedScriptStart + pubKeyHash + expectedScriptEnd)
def PubKeyHashForScriptPubKey(scriptPubKey):
	scriptPubKeyBytes = Util.fromHex(scriptPubKey)
	expectedScriptStart = OP_DUP
	expectedScriptStart += OP_HASH160
	expectedScriptStart += _opPush(20)
	expectedScriptEnd = OP_EQUALVERIFY
	expectedScriptEnd += OP_CHECKSIG
	assert scriptPubKeyBytes.startswith(expectedScriptStart)
	assert scriptPubKeyBytes.endswith(expectedScriptEnd)
	pubKeyHash = scriptPubKeyBytes[len(expectedScriptStart):-len(expectedScriptEnd)]
	assert len(pubKeyHash) == 20
	return pubKeyHash

def Create(tx, scriptPubKeyLookup):
	data = struct.pack("<L", 1) # version, 4 byte little endian
	data += _encodeVarInt(int(tx.numberOfInputs()))
	for i in range(tx.numberOfInputs()):
		txid = tx.inputTXID(i)
		vout = tx.inputVOut(i)
		scriptPubKey = scriptPubKeyLookup[(txid, vout)]
		txIDBytes = Util.fromHex(txid)[::-1]
		assert len(txIDBytes) == 32
		data += txIDBytes
		data += struct.pack("<L", vout)
		script = Util.fromHex(scriptPubKey)
		data += _encodeVarInt(int(len(script)))
		data += script
		data += b'\xff' * 4 # sequence
	data += _encodeVarInt(tx.numberOfOutputs())
	for i in range(tx.numberOfOutputs()):
		pubKeyHash = tx.outputPubKeyHash(i)
		value = tx.outputAmount(i)
		assert len(pubKeyHash) == 20
		data += struct.pack("<Q", value)
		script = OP_DUP
		script += OP_HASH160
		script += _opPush(20)
		script += pubKeyHash
		script += OP_EQUALVERIFY
		script += OP_CHECKSIG
		data += _encodeVarInt(int(len(script)))
		data += script
	data += struct.pack("<L", 0) # lock time
	return data

def UnexpectedFormat_Fast(txBytes, controlAddressPrefix):
	assert type(txBytes) is type(b'')
	assert type(controlAddressPrefix) is type(b'')
	assert len(controlAddressPrefix) <= 20
	if len(txBytes) < 6: ## actual minimum is greater than this, work this out!
		return True
	version = struct.unpack("<L", txBytes[:4])[0]
	if version != 1:
		return True
	pos = 4
	try:
		pos, numberOfInputs = _decodeVarInt(txBytes, pos)
		for i in range(numberOfInputs):
			pos += 36
			pos, scriptLen = _decodeVarInt(txBytes, pos)
			pos += scriptLen
			pos += 4
		pos, numberOfOutputs = _decodeVarInt(txBytes, pos)
		if numberOfOutputs == 0:
			return True
		for i in range(numberOfOutputs):
			pos += 8
			pos, scriptLen = _decodeVarInt(txBytes, pos)
			if i == 0:
				script = txBytes[pos:pos + scriptLen]
				expectedScriptStart = OP_DUP
				expectedScriptStart += OP_HASH160
				expectedScriptStart += _opPush(20)
				expectedScriptEnd = OP_EQUALVERIFY
				expectedScriptEnd += OP_CHECKSIG
				if len(script) != len(expectedScriptStart) + 20 + len(expectedScriptEnd):
					return True
				if not script.startswith(expectedScriptStart):
					return True
				if not script[len(expectedScriptStart):].startswith(controlAddressPrefix):
					return True
				if not script.endswith(expectedScriptEnd):
					return True
			pos += scriptLen
	except _RanOutOfData:
		return True
	if pos + 4 != len(txBytes):
		return True
	return False

def Decode(txBytes):
	assert type(txBytes) is type(b'')
	assert not UnexpectedFormat_Fast(txBytes, b'')
	result = HostTransaction.InMemoryTransaction()
	pos = 4
	pos, numberOfInputs = _decodeVarInt(txBytes, pos)
	inputs = []
	for i in range(numberOfInputs):
		txIDBytes = txBytes[pos:pos + 32]
		pos += 32
		txID = Util.toHex(txIDBytes[::-1])
		vOut = struct.unpack("<L", txBytes[pos:pos + 4])[0]
		result.addInput(txID, vOut)
		pos += 4
		pos, scriptLen = _decodeVarInt(txBytes, pos)
		pos += scriptLen
		pos += 4 # sequence
	pos, numberOfOutputs = _decodeVarInt(txBytes, pos)
	scriptPubKeys = []
	for i in range(numberOfOutputs):
		outputAmount = struct.unpack("<Q", txBytes[pos:pos + 8])[0]
		pos += 8
		pos, scriptLen = _decodeVarInt(txBytes, pos)
		scriptPubKeyBytes = txBytes[pos:pos + scriptLen]
		pos += scriptLen
		scriptPubKeys.append(Util.toHex(scriptPubKeyBytes)) # TODO keep this as binary data?
		expectedScriptStart = OP_DUP
		expectedScriptStart += OP_HASH160
		expectedScriptStart += _opPush(20)
		pubKeyHash = scriptPubKeyBytes[len(expectedScriptStart):len(expectedScriptStart)+20]
		assert len(pubKeyHash) == 20
		result.addOutput(pubKeyHash, outputAmount)
	return result, scriptPubKeys

def GetTransactionsInBlock(data):
	assert type(data) is type(b'')
	try:
		pos = 80 # skip block header
		pos, numberOfTransactions = _decodeVarInt(data, pos)
		result = []
		for i in range(numberOfTransactions):
			startPos = pos
			pos += 4 # skip version
			pos, numberOfInputs = _decodeVarInt(data, pos)
			for i in range(numberOfInputs):
				pos += 32 # txid
				pos += 4 # vout
				pos, scriptLen = _decodeVarInt(data, pos)
				pos += scriptLen
				pos += 4 # sequence
			pos, numberOfOutputs = _decodeVarInt(data, pos)
			for i in range(numberOfOutputs):
				pos += 8 # output amount
				pos, scriptLen = _decodeVarInt(data, pos)
				pos += scriptLen
			pos += 4 # lock time
			result.append(data[startPos:pos])
		if pos != len(data):
			raise Exception('bad block data')
		return result
	except _RanOutOfData:
		raise Exception('bad block data')
