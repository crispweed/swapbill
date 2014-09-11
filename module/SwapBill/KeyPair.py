import ecdsa, hashlib, os

def _generatePrivateKey():
	return os.urandom(32)
def _generateRandomPublicKeyForUseAsSecret():
	return os.urandom(64)
def _privateKeyToPublicKey(privateKey):
	assert type(privateKey) is type(b'')
	assert len(privateKey) == 32
	sk = ecdsa.SigningKey.from_string(privateKey, curve=ecdsa.SECP256k1)
	vk = sk.verifying_key
	result = sk.verifying_key.to_string()
	assert len(result) == 64
	return result
def _publicKeyToPubKeyHash(publicKey):
	assert type(publicKey) is type(b'')
	assert len(publicKey) == 64
	ripemd160 = hashlib.new('ripemd160')
	ripemd160.update(hashlib.sha256(b'\x04' + publicKey).digest())
	return ripemd160.digest()

def GeneratePrivateKey():
	return _generatePrivateKey()
def GenerateRandomPublicKeyForUseAsSecret():
	return _generateRandomPublicKeyForUseAsSecret()
def PrivateKeyToPublicKey(privateKey):
	return _privateKeyToPublicKey(privateKey)
def PublicKeyToPubKeyHash(publicKey):
	return _publicKeyToPubKeyHash(publicKey)

def PrivateKeyToPubKeyHash(privateKey):
	publicKey = PrivateKeyToPublicKey(privateKey)
	return PublicKeyToPubKeyHash(publicKey)
