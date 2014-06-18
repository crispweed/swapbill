from __future__ import print_function
import ecdsa, hashlib, os
from SwapBill import Address

class DefaultKeyGenerator(object):
	def generatePrivateKey(self):
		return os.urandom(32)
	def privateKeyToPubKeyHash(self, privateKey):
		sk = ecdsa.SigningKey.from_string(privateKey, curve=ecdsa.SECP256k1)
		vk = sk.verifying_key
		publicKey = sk.verifying_key.to_string()
		ripemd160 = hashlib.new('ripemd160')
		ripemd160.update(hashlib.sha256(b'\x04' + publicKey).digest())
		return ripemd160.digest()

class Wallet(object):
	def __init__(self, fileName, privateKeyAddressVersion, keyGenerator=None):
		if keyGenerator is None:
			keyGenerator = DefaultKeyGenerator()
		self._privateKeyAddressVersion = privateKeyAddressVersion
		self._keyGenerator = keyGenerator
		self._fileName = fileName
		self._privateKeys = []
		self._pubKeyHashes = []
		if os.path.exists(fileName):
			with open(fileName, mode='r') as f:
				lines = f.readlines()
				for line in lines:
					privateKeyWIF = line.strip()
					privateKey = Address.PrivateKeyFromWIF(self._privateKeyAddressVersion, privateKeyWIF)
					self._privateKeys.append(privateKey)
					pubKeyHash = self._keyGenerator.privateKeyToPubKeyHash(privateKey)
					self._pubKeyHashes.append(pubKeyHash)

	def addKeyPairAndReturnPubKeyHash(self):
		privateKey = self._keyGenerator.generatePrivateKey()
		privateKeyWIF = Address.PrivateKeyToWIF(privateKey, self._privateKeyAddressVersion)
		pubKeyHash = self._keyGenerator.privateKeyToPubKeyHash(privateKey)
		self._privateKeys.append(privateKey)
		self._pubKeyHashes.append(pubKeyHash)
		with open(self._fileName, mode='a') as f:
			f.write(privateKeyWIF)
			f.write('\n')
		return pubKeyHash

	def hasKeyPairForPubKeyHash(self, pubKeyHash):
		return pubKeyHash in self._pubKeyHashes
	def privateKeyForPubKeyHash(self, pubKeyHash):
		for i in range(len(self._privateKeys)):
			if self._pubKeyHashes[i] == pubKeyHash:
				return self._privateKeys[i]
