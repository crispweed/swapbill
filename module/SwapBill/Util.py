import struct, binascii

def intFromBytes(data):
	multiplier = 1
	result = 0
	# need to be careful when working with bytes to ensure this does the same thing in python 2 and 3
	for i in range(len(data)):
		byteValue = struct.unpack('<B', data[i:i + 1])[0]
		result += byteValue * multiplier
		multiplier = multiplier << 8
	return result

def toHex(data):
	assert type(data) is type(b'')
	return binascii.hexlify(data).decode('ascii')

def fromHex(s):
	try:	
		return binascii.unhexlify(s.encode('ascii'))
	except binascii.Error:
		raise TypeError
	