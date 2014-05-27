from __future__ import print_function, division

class Exchange(object):
	pass

minimumExchangeLTC = 1000000
depositDivisor = 16

def LTCWithExchangeRate(exchangeRate, swapBillAmount):
	return swapBillAmount * exchangeRate // 0x100000000

def SatisfiesMinimumExchange(rate, amount):
	return LTCWithExchangeRate(rate, amount) >= minimumExchangeLTC

def Match(buyRate, buyExpiry, buyDetails, sellRate, sellExpiry, sellDetails):
	assert SatisfiesMinimumExchange(buyRate, buyDetails.swapBillAmount) ## should not have been added to buys
	assert SatisfiesMinimumExchange(sellRate, sellDetails.swapBillAmount) ## should not have been added to sells
	appliedRate = (buyRate + sellRate) // 2
	exchange = Exchange()
	exchange.ltcReceiveAddress = buyDetails.receivingAccount
	exchange.buyerAddress = buyDetails.refundAccount
	exchange.sellerReceivingAccount = sellDetails.receivingAccount
	outstandingBuy = None
	outstandingSell = None
	if buyDetails.swapBillAmount > sellDetails.swapBillAmount:
		exchange.swapBillAmount = sellDetails.swapBillAmount
		exchange.swapBillDeposit = sellDetails.swapBillDeposit
		buyDetails.swapBillAmount -= exchange.swapBillAmount
		outstandingBuy = buyDetails
	else:
		exchange.swapBillAmount = buyDetails.swapBillAmount
		if buyDetails.swapBillAmount == sellDetails.swapBillAmount:
			exchange.swapBillDeposit = sellDetails.swapBillDeposit
		else:
			exchange.swapBillDeposit = sellDetails.swapBillDeposit * exchange.swapBillAmount // sellDetails.swapBillAmount
			sellDetails.swapBillAmount -= exchange.swapBillAmount
			sellDetails.swapBillDeposit -= exchange.swapBillDeposit
			outstandingSell = sellDetails
	exchange.ltc = LTCWithExchangeRate(appliedRate, exchange.swapBillAmount)
	assert exchange.ltc >= minimumExchangeLTC ## should be guaranteed by buy and sell both satisfying this minimum requirement
	return exchange, outstandingBuy, outstandingSell


