from __future__ import print_function
import ecdsa, hashlib, os
from SwapBill import Base58Check, Amounts

class OwnedAccounts(object):
	def __init__(self):
		self.accounts = {}
		self.tradeOfferChangeCounts = {}

	def updateForSpent(self, hostTX, state):
		report = ''
		for i in range(hostTX.numberOfInputs()):
			spentAccount = (hostTX.inputTXID(i), hostTX.inputVOut(i))
			if spentAccount in self.accounts:
				self.accounts.pop(spentAccount)
				report += ' - ' + Amounts.ToString(state._balances.balanceFor(spentAccount)) + ' swapbill output consumed\n'
		return report

	def checkForTradeOfferChanges(self, state):
		report = ''
		toRemove = []
		for account in self.tradeOfferChangeCounts:
			changeCount = self.tradeOfferChangeCounts[account]
			if not account in state._balances.changeCounts:
				toRemove.append(account)
				report += ' - trade offer completed\n'
			elif state._balances.changeCounts[account] != changeCount:
				self.tradeOfferChangeCounts[account] = state._balances.changeCounts[account]
				report += ' - trade offer updated\n'
		for accountToRemove in toRemove:
			self.tradeOfferChangeCounts.pop(accountToRemove)
			if accountToRemove in self.accounts and not accountToRemove in state._balances.balances:
				self.accounts.pop(accountToRemove)
		return report

	def updateForNewOutputs(self, wallet, state, txID, hostTX, outputs, scriptPubKeys):
		report = ''
		for i in range(len(outputs)):
			newOwnedAccount = (txID, i + 1)
			if not state._balances.accountHasBalance(newOwnedAccount):
				continue # output not created by transaction
			privateKey = wallet.privateKeyForPubKeyHash(hostTX.outputPubKeyHash(i + 1))
			if privateKey is None:
				continue # output not ours (e.g. pay destination)
			if newOwnedAccount in state._balances.changeCounts:
				self.tradeOfferChangeCounts[newOwnedAccount] = state._balances.changeCounts[newOwnedAccount]
			self.accounts[newOwnedAccount] = (hostTX.outputAmount(i + 1), privateKey, scriptPubKeys[i + 1])
			report += ' - ' + Amounts.ToString(state._balances.balanceFor(newOwnedAccount)) + ' swapbill output added\n'
		return report