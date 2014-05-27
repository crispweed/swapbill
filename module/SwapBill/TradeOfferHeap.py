from __future__ import print_function
import heapq

class Heap(object):
	def __init__(self, startBlockCount, higherExchangeRateIsBetterOffer):
		self._blockCount = startBlockCount
		self._higherExchangeRateIsBetterOffer = higherExchangeRateIsBetterOffer
		self._offerByExchangeRate = []
		self._entryCount = 0 # used to avoid priority ties

	def _hasExpired(self, expiry):
		return self._blockCount > expiry
	def _hasExpiredOffers(self):
		for offer in self._offerByExchangeRate:
			if self._hasExpired(offer[2]):
				return True
		return False

	#details = address, amount, extraData=None
	def addOffer(self, exchangeRate, expiry, details):
		if self._higherExchangeRateIsBetterOffer:
			exchangeRate = -exchangeRate
		entry = (exchangeRate, self._entryCount, expiry, details)
		self._entryCount += 1
		heapq.heappush(self._offerByExchangeRate, entry)

	def advanceToBlock(self, advanceTo):
		assert advanceTo >= self._blockCount
		self._blockCount = advanceTo
		if not self._hasExpiredOffers():
			return []
		expired = []
		unexpired = []
		for offer in self._offerByExchangeRate:
			if self._hasExpired(offer[2]):
				expired.append(offer[3])
			else:
				unexpired.append(offer)
		heapq.heapify(unexpired)
		self._offerByExchangeRate = unexpired
		return expired
	def advanceToNextBlock(self):
		return self.advanceToBlock(self._blockCount + 1)

	def size(self):
		return len(self._offerByExchangeRate)
	def empty(self):
		return len(self._offerByExchangeRate) == 0

	def currentBestExchangeRate(self):
		assert not self.empty()
		if self._higherExchangeRateIsBetterOffer:
			return -self._offerByExchangeRate[0][0]
		return self._offerByExchangeRate[0][0]
	def currentBestExpiry(self):
		assert not self.empty()
		return self._offerByExchangeRate[0][2]

	def peekCurrentBest(self):
		assert not self.empty()
		exchangeRate, entryCount, expiry, details = self._offerByExchangeRate[0]
		return details
	def popCurrentBest(self):
		assert not self.empty()
		entry = heapq.heappop(self._offerByExchangeRate)
		exchangeRate, entryCount, expiry, details = entry
		return details

	def getSortedExchangeRateAndDetails(self):
		result = []
		for entry in sorted(self._offerByExchangeRate):
			exchangeRate, entryCount, expiry, details = entry
			if self._higherExchangeRateIsBetterOffer:
				exchangeRate = -exchangeRate
			result.append((exchangeRate, details))
		return result
