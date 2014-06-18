from SwapBill import Base58Check

class BadAddress(Exception):
	pass
class BadPrivateKeyWIF(Exception):
	pass

def FromPubKeyHash(addressVersion, data):
	assert type(addressVersion) is type(b'.')
	assert type(data) is type(b'.')
	assert len(addressVersion) == 1
	assert len(data) == 20
	return Base58Check.Encode(addressVersion + data)

def ToPubKeyHash(addressVersion, address):
	assert type(addressVersion) is type(b'.')
	assert len(addressVersion) == 1
	try:
		data = Base58Check.Decode(address)
	except Base58Check.CharacterNotPermittedInEncodedData as e:
		raise BadAddress('invalid base58 character encountered')
	except Base58Check.ChecksumDoesNotMatch as e:
		raise BadAddress('checksum mismatch')
	if data[:1] != addressVersion:
		raise BadAddress('incorrect version byte:', data[:1], 'expected:', addressVersion)
	return data[1:]

def PrivateKeyFromWIF(addressVersion, wif):
	data = Base58Check.Decode(wif)
	if data[:1] != addressVersion:
		raise BadPrivateKeyWIF('incorrect version byte:', data[:1], 'expected:', addressVersion)
	return data[1:]
def PrivateKeyToWIF(data, addressVersion):
	assert type(addressVersion) is type(b'.')
	assert type(data) is type(b'.')
	assert len(addressVersion) == 1
	assert len(data) == 32
	return Base58Check.Encode(addressVersion + data)
