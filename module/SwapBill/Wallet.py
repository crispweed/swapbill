from __future__ import print_function
import os
from SwapBill import KeyPair

class Wallet(object):
	def __init__(self, fileName):
		self._fileName = fileName
		self._privateKeys = []
		self._pubKeyHashes = []
		if os.path.exists(fileName):
			with open(fileName, mode='r') as f:
				lines = f.readlines()
				for line in lines:
					readWIF = line.strip()
					privateKey = KeyPair.privateKeyFromWIF(b'\xef', readWIF) # litecoin testnet private key address version
					self._privateKeys.append(readWIF)
					publicKey = KeyPair.privateKeyToPublicKey(privateKey)
					pubKeyHash = KeyPair.publicKeyToPubKeyHash(publicKey)
					self._pubKeyHashes.append(pubKeyHash)

	def addKeyPairAndReturnPubKeyHash(self):
		privateKey = KeyPair.generatePrivateKey()
		testNetWIF = KeyPair.privateKeyToWIF(privateKey, b'\xef') # litecoin testnet private key address version
		publicKey = KeyPair.privateKeyToPublicKey(privateKey)
		pubKeyHash = KeyPair.publicKeyToPubKeyHash(publicKey)
		self._privateKeys.append(testNetWIF)
		self._pubKeyHashes.append(pubKeyHash)
		with open(self._fileName, mode='a') as f:
			f.write(testNetWIF)
			f.write('\n')
		return pubKeyHash

	def hasKeyPairForPubKeyHash(self, pubKeyHash):
		return pubKeyHash in self._pubKeyHashes
	def getAllPrivateKeys(self):
		return self._privateKeys
	def privateKeyForPubKeyHash(self, pubKeyHash):
		for i in range(len(self._privateKeys)):
			if self._pubKeyHashes[i] == pubKeyHash:
				return self._privateKeys[i]
