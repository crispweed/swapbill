from __future__ import print_function
from hashlib import sha256
from SwapBill import Util

class CharacterNotPermittedInEncodedData(Exception):
	pass
class ChecksumDoesNotMatch(Exception):
	pass

digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def CheckSum(data):
	return sha256(sha256(data).digest()).digest()[:4]

def Encode(data):
	assert type(data) is type(b'')
	withChecksum = data + CheckSum(data)
	n = int('0x0' + Util.toHex(withChecksum), 16)
	base58 = ''
	while n > 0:
		n, r = divmod(n, 58)
		base58 += digits[r]
	pad = 0
	while data[pad:pad+1] == b'\x00':
		pad += 1
	return digits[0] * pad + base58[::-1]

def Decode(string):
	n = 0
	for c in string:
		n *= 58
		if c not in digits:
			raise CharacterNotPermittedInEncodedData()
		digit = digits.index(c)
		n += digit
	h = '%x' % n
	if len(h) % 2:
		h = '0' + h
	base58 = Util.fromHex(h)
	pad = 0
	for c in string[:-1]:
		if c == digits[0]: pad += 1
		else: break
	withCheckSum = b'\x00' * pad + base58
	data = withCheckSum[:-4]
	checkSum = withCheckSum[-4:]
	if checkSum != CheckSum(data):
		raise ChecksumDoesNotMatch()
	return data
