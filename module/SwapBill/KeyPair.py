from __future__ import print_function
import ecdsa, hashlib, os
from SwapBill import Base58Check

class BadVersionNumber(Exception):
	pass

def generatePrivateKey():
	return os.urandom(32)
def privateKeyFromWIF(addressVersion, wif):
	data = Base58Check.Decode(wif)
	if data[:1] != addressVersion:
		raise BadVersionNumber()
	return data[1:]
def privateKeyToWIF(data, addressVersion):
	assert type(addressVersion) is type(b'.')
	assert type(data) is type(b'.')
	assert len(addressVersion) == 1
	assert len(data) == 32
	return Base58Check.Encode(addressVersion + data)

def privateKeyToPublicKey(privateKey):
	sk = ecdsa.SigningKey.from_string(privateKey, curve=ecdsa.SECP256k1)
	vk = sk.verifying_key
	return sk.verifying_key.to_string()

def publicKeyToPubKeyHash(publicKey):
	ripemd160 = hashlib.new('ripemd160')
	ripemd160.update(hashlib.sha256(b'\x04' + publicKey).digest())
	return ripemd160.digest()
