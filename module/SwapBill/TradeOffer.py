from __future__ import print_function, division
from SwapBill import Amounts

class OfferIsBelowMinimumExchange(Exception):
	pass

def _ltcToSwapBill(rate, ltc):
	swapBill = ltc * Amounts.percentDivisor // rate
	rounded = (swapBill * rate != ltc * Amounts.percentDivisor)
	if rounded:
		# the actual exact converted amount is in between swapbill and swapbill + 1 in this case
		assert (swapBill + 1) * rate > ltc * Amounts.percentDivisor
	return swapBill, rounded
def _swapBillToLTC(rate, swapBill):
	ltc = swapBill * rate // Amounts.percentDivisor
	rounded = (ltc * Amounts.percentDivisor != swapBill * rate)
	if rounded:
		# the actual exact converted amount is in between ltc and ltc + 1 in this case
		assert (ltc + 1) * Amounts.percentDivisor > swapBill * rate
	return ltc, rounded

def ltcToSwapBill_RoundedUp(rate, ltc):
	swapBill, rounded = _ltcToSwapBill(rate, ltc)
	if rounded:
		swapBill += 1
	return swapBill
def swapBillToLTC_RoundedUp(rate, swapBill):
	ltc, rounded = _swapBillToLTC(rate, swapBill)
	if rounded:
		ltc += 1
	return ltc
def swapBillToLTC_RoundedDown(rate, swapBill):
	ltc, rounded = _swapBillToLTC(rate, swapBill)
	return ltc

def MinimumBuyOfferWithRate(protocolParams, rate):
	swapBillForMinLTC = ltcToSwapBill_RoundedUp(rate, protocolParams['minimumHostExchangeAmount'])
	return max(swapBillForMinLTC, protocolParams['minimumSwapBillBalance'])

def MinimumSellOfferWithRate(protocolParams, rate):
	ltcForMinSwapBill = swapBillToLTC_RoundedUp(rate, protocolParams['minimumSwapBillBalance'])
	return max(ltcForMinSwapBill, protocolParams['minimumHostExchangeAmount'])

def DepositRequiredForLTCSell(protocolParams, rate, hostCoinOffered):
	swapBill = ltcToSwapBill_RoundedUp(rate, hostCoinOffered)
	deposit = swapBill // protocolParams['depositDivisor']
	if deposit * protocolParams['depositDivisor'] != swapBill:
		deposit += 1
	return deposit

class BuyOffer(object):
	def __init__(self, protocolParams, swapBillOffered, rate):
		if swapBillOffered < MinimumBuyOfferWithRate(protocolParams, rate):
			raise OfferIsBelowMinimumExchange()
		self._swapBillOffered = swapBillOffered
		self.rate = rate
	def hasBeenConsumed(self):
		return self._swapBillOffered == 0
	def ltcEquivalent(self):
		return swapBillToLTC_RoundedUp(self.rate, self._swapBillOffered)
	def _canSubtract(self, protocolParams, swapBill):
		if swapBill > self._swapBillOffered:
			return False
		if swapBill == self._swapBillOffered:
			return True
		return self._swapBillOffered - swapBill >= MinimumBuyOfferWithRate(protocolParams, self.rate)

class SellOffer(object):
	def __init__(self, protocolParams, swapBillDeposit, hostCoinOffered, rate):
		if hostCoinOffered < MinimumSellOfferWithRate(protocolParams, rate):
			#print(MinimumSellOfferWithRate(minimumHostExchangeAmount, rate))
			raise OfferIsBelowMinimumExchange()
		self._swapBillDeposit = swapBillDeposit
		self._hostCoinOffered = hostCoinOffered
		self.rate = rate
	def hasBeenConsumed(self):
		return self._hostCoinOffered == 0
	def swapBillEquivalent(self):
		return ltcToSwapBill_RoundedUp(self.rate, self._hostCoinOffered)
	def _canSubtract(self, protocolParams, ltc):
		if ltc > self._hostCoinOffered:
			return False
		if ltc == self._hostCoinOffered:
			return True
		return self._hostCoinOffered - ltc >= MinimumSellOfferWithRate(protocolParams, self.rate)

class Exchange(object):
	pass

def OffersMeetOrOverlap(buy, sell):
	return buy.rate <= sell.rate

def MatchOffers(protocolParams, buy, sell):
	assert OffersMeetOrOverlap(buy, sell)
	appliedRate = (buy.rate + sell.rate) // 2

	ltc, rounded = _swapBillToLTC(appliedRate, buy._swapBillOffered)
	assert ltc >= protocolParams['minimumHostExchangeAmount'] # should be guaranteed by buy and sell both satisfying this minimum requirement

	candidates = [(buy._swapBillOffered, ltc)]
	if rounded:
		# added ensure that posting matching offers based on the displayed other currency equivalent results in a match
		candidates.append((buy._swapBillOffered, ltc + 1))

	swapBill, rounded = _ltcToSwapBill(appliedRate, sell._hostCoinOffered)
	candidates.append((swapBill, sell._hostCoinOffered))

	ltc = sell._hostCoinOffered - MinimumSellOfferWithRate(protocolParams, sell.rate)
	if ltc > 0:
		swapBill, rounded = _ltcToSwapBill(appliedRate, ltc)
		candidates.append((swapBill, ltc))

	swapBill = buy._swapBillOffered - MinimumBuyOfferWithRate(protocolParams, buy.rate)
	if swapBill > 0:
		ltc, rounded = _swapBillToLTC(appliedRate, swapBill)
		candidates.append((swapBill, ltc))

	for swapBill, ltc in candidates:
		if swapBill < protocolParams['minimumSwapBillBalance']:
			continue
		if ltc < protocolParams['minimumHostExchangeAmount']:
			continue
		if buy._canSubtract(protocolParams, swapBill) and sell._canSubtract(protocolParams, ltc):
			exchange = Exchange()
			exchange.swapBillAmount = swapBill
			exchange.ltc = ltc
			exchange.swapBillDeposit = sell._swapBillDeposit * ltc // sell._hostCoinOffered
			buy._swapBillOffered -= swapBill
			sell._hostCoinOffered -= ltc
			sell._swapBillDeposit -= exchange.swapBillDeposit
			assert (sell._hostCoinOffered == 0) == (sell._swapBillDeposit == 0)
			return exchange

	raise OfferIsBelowMinimumExchange()
