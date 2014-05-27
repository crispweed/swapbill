from __future__ import print_function
import ecdsa, hashlib, os
from SwapBill import Base58Check

class OwnedAccounts(object):
	def __init__(self):
		self.spendableAccounts = {}
		self.buyOffers = {}
		self.sellOffers = {}

	def updateForSpent(self, hostTX, state):
		report = ''
		for i in range(hostTX.numberOfInputs()):
			spentAccount = (hostTX.inputTXID(i), hostTX.inputVOut(i))
			assert not spentAccount in self.sellOffers
			assert not spentAccount in self.buyOffers
			if spentAccount in self.spendableAccounts:
				self.spendableAccounts.pop(spentAccount)
				report += ' - ' + str(state._balances[spentAccount]) + ' swapbill output consumed\n'
		return report

	def _checkForTradeOfferChanges(self, state, offers, offerType):
		report = ''
		toRemove = []
		for account in offers:
			changeCount, outputDetails = offers[account]
			if not account in state._tradeOfferChangeCounts:
				self.spendableAccounts[account] = outputDetails
				toRemove.append(account)
				report += ' - ' + offerType + ' offer completed, receiving output with ' + str(state._balances[account]) + ' swapbill unlocked\n'
			elif state._tradeOfferChangeCounts[account] != changeCount:
				assert state._tradeOfferChangeCounts[account] == changeCount + 1
				offers[account][0] = state._tradeOfferChangeCounts[account]
				report += ' - ' + offerType + ' offer updated (receiving output contains ' + str(state._balances[account]) + ' swapbill)\n'
		for accountToRemove in toRemove:
			offers.pop(accountToRemove)
		return report
	def checkForTradeOfferChanges(self, state):
		return self._checkForTradeOfferChanges(state, self.buyOffers, 'buy') + self._checkForTradeOfferChanges(state, self.sellOffers, 'sell')

	def updateForNewOutputs(self, host, state, txID, hostTX, outputs, scriptPubKeys):
		report = ''
		for i in range(len(outputs)):
			newOwnedAccount = (txID, i + 1)
			if not newOwnedAccount in state._balances:
				continue # output not created by transaction
			privateKey = host.privateKeyForPubKeyHash(hostTX.outputPubKeyHash(i + 1))
			if privateKey is None:
				continue # output not ours (e.g. pay destination)
			affected = True
			outputDetails = (hostTX.outputAmount(i + 1), privateKey, scriptPubKeys[i + 1])
			if outputs[i] == 'ltcBuy':
				self.buyOffers[newOwnedAccount] = [state._tradeOfferChangeCounts[newOwnedAccount], outputDetails]
				report += ' - created buy offer, refund output seeded with ' + str(state._balances[newOwnedAccount]) + ' swapbill and locked until trade completed\n'
				continue
			if outputs[i] == 'ltcSell':
				self.sellOffers[newOwnedAccount] = [state._tradeOfferChangeCounts[newOwnedAccount], outputDetails]
				report += ' - created sell offer, receiving output seeded with ' + str(state._balances[newOwnedAccount]) + ' swapbill and locked until trade completed\n'
				continue
			self.spendableAccounts[newOwnedAccount] = outputDetails
			report += ' - ' + str(state._balances[newOwnedAccount]) + ' swapbill output added\n'
		return report