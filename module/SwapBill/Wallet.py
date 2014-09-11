from __future__ import print_function
from SwapBill import KeyPair

class Wallet(object):
	def __init__(self, privateKeys):
		self._privateKeys = privateKeys
		self._pubKeyHashes = list(map(KeyPair.PrivateKeyToPubKeyHash, privateKeys))

	def addKeyPairAndReturnPubKeyHash(self):
		privateKey = KeyPair.GeneratePrivateKey()
		self._privateKeys.append(privateKey)
		pubKeyHash = KeyPair.PrivateKeyToPubKeyHash(privateKey)
		self._pubKeyHashes.append(pubKeyHash)
		return pubKeyHash

	def hasKeyPairForPubKeyHash(self, pubKeyHash):
		return pubKeyHash in self._pubKeyHashes
	def privateKeyForPubKeyHash(self, pubKeyHash):
		for storedHash, privateKey in zip(self._pubKeyHashes, self._privateKeys):
			if storedHash == pubKeyHash:
				return privateKey
