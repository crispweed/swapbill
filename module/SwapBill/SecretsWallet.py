from __future__ import print_function
from SwapBill import KeyPair

class SecretsWallet(object):
	def __init__(self, publicKeys):
		self._publicKeys = publicKeys
		self._pubKeyHashes = list(map(KeyPair.PublicKeyToPubKeyHash, publicKeys))

	def addPublicKeySecret(self, publicKey=None):
		if publicKey is None:
			publicKey = KeyPair.GenerateRandomPublicKeyForUseAsSecret()
		self._publicKeys.append(publicKey)
		pubKeyHash = KeyPair.PublicKeyToPubKeyHash(publicKey)
		self._pubKeyHashes.append(pubKeyHash)
		return pubKeyHash

	def hasKeyPairForPubKeyHash(self, pubKeyHash):
		return pubKeyHash in self._pubKeyHashes
	def publicKeyForPubKeyHash(self, pubKeyHash):
		for storedHash, publicKey in zip(self._pubKeyHashes, self._publicKeys):
			if storedHash == pubKeyHash:
				return publicKey

