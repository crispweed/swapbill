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
		for entry in self._offerByExchangeRate:
			offer = entry[2]
			if self._hasExpired(offer.expiry):
				return True
		return False

	def addOffer(self, offer):
		rateForOrdering = offer.rate
		if self._higherExchangeRateIsBetterOffer:
			rateForOrdering = -rateForOrdering
		entry = (rateForOrdering, self._entryCount, offer)
		self._entryCount += 1
		heapq.heappush(self._offerByExchangeRate, entry)

	def advanceToBlock(self, advanceTo):
		assert advanceTo >= self._blockCount
		self._blockCount = advanceTo
		if not self._hasExpiredOffers():
			return []
		expired = []
		unexpired = []
		for entry in self._offerByExchangeRate:
			offer = entry[2]
			if self._hasExpired(offer.expiry):
				expired.append(offer)
			else:
				unexpired.append(entry)
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
		return self._offerByExchangeRate[0][2].rate
	def currentBestExpiry(self):
		assert not self.empty()
		return self._offerByExchangeRate[0][2].expiry

	def peekCurrentBest(self):
		assert not self.empty()
		return self._offerByExchangeRate[0][2]
	def popCurrentBest(self):
		assert not self.empty()
		entry = heapq.heappop(self._offerByExchangeRate)
		return entry[2]

	def getSortedOffers(self):
		result = []
		for entry in sorted(self._offerByExchangeRate):
			offer = entry[2]
			result.append(offer)
		return result
