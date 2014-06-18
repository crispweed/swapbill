from __future__ import print_function

class Balances(object):
	def __init__(self):
		self.balances = {}
		self._directRefCounts = {} # the number of references targetting this balance directly
		self.changeCounts = {} # maintained while there are direct refs
		self._redirects = {} # maintained while the redirect sources have direct refs
		self._redirectRefCounts = {} # counts the number of redirects feeding into a balance

	def _removeRedirectRef(self, account):
		assert self._redirectRefCounts[account] > 0
		if self._redirectRefCounts[account] > 1:
			self._redirectRefCounts[account] -= 1
			return
		# removed last redirect ref to account
		self._redirectRefCounts.pop(account)
		if account in self._directRefCounts:
			# this node now becomes a leaf node
			return
		if not account in self._redirects:
			# terminal node
			assert account in self.balances
			if self.balances[account] == 0:
				# balance removal is triggered here
				self.balances.pop(account)
			return
		assert not account in account in self.balances
		childAccount = self._redirects.pop(account)
		self._removeRedirectRef(childAccount)

	def accountHasBalance(self, account):
		return account in self.balances
	def balanceFor(self, account):
		return self.balances[account]
	def balanceFor_IfAny(self, account):
		return self.balances.get(account, 0)

	def add(self, account, amount):
		assert not account in self.balances
		self.balances[account] = amount
	def addTo(self, account, amount):
		self.balances[account] += amount
	def addOrAddTo(self, account, amount):
		if account in self.balances:
			self.balances[account] += amount
		else:
			self.balances[account] = amount

	#def consume(self, account):
		#self.balances.pop(account)

	def consumeContents_IfAny(self, account):
		if not account in self.balances:
			return 0
		contents = self.balances[account]
		self.balances[account] = 0
		if not self.isReferenced(account):
			self.balances.pop(account)
		return contents

	def removeIfZeroBalanceAndUnreferenced(self, account):
		if self.balances[account] > 0:
			return
		if not self.isReferenced(account):
			self.balances.pop(account)

	def addFirstRef(self, account):
		assert account in self.balances
		assert not account in self._directRefCounts
		self._directRefCounts[account] = 1
		self.changeCounts[account] = 0
	def addRef(self, account):
		assert account in self._directRefCounts
		self._directRefCounts[account] += 1
	def removeRef(self, account):
		assert self._directRefCounts[account] > 0
		if self._directRefCounts[account] > 1:
			self._directRefCounts[account] -= 1
			return
		# removed last direct ref
		self._directRefCounts.pop(account)
		self.changeCounts.pop(account)
		if account in self._redirectRefCounts:
			# still redirect target from other nodes
			return
		if not account in self._redirects:
			# terminal node
			assert account in self.balances
			if self.balances[account] == 0:
				# balance removal is triggered here
				self.balances.pop(account)
			return
		assert not account in self.balances
		childAccount = self._redirects.pop(account)
		self._removeRedirectRef(childAccount)

	def addStateChange(self, account):
		self.changeCounts[account] += 1

	def isReferenced(self, account):
		assert account in self.balances
		return account in self._directRefCounts or account in self._redirectRefCounts

	#def consumeAndForwardRefs(self, fromAccounts, toAccount):
		#assert not toAccount in self._redirectRefCounts
		#redirectRefCount = 0
		#for account in fromAccounts:
			#if self.isReferenced(account):
				#self._redirects[account] = toAccount
				#redirectRefCount += 1
			#self.consume(account)
		#if redirectRefCount > 0:
			#self._redirectRefCounts[toAccount] = redirectRefCount

	def consumeAndForward(self, fromAccounts, toAccount):
		amount = self.balances[toAccount]
		redirectRefCount = self._redirectRefCounts.get(toAccount, 0)
		for account in fromAccounts:
			if not account in self.balances:
				continue
			if self.isReferenced(account):
				self._redirects[account] = toAccount
				redirectRefCount += 1
			amount += self.balances.pop(account)
		if redirectRefCount > 0:
			self._redirectRefCounts[toAccount] = redirectRefCount
		self.balances[toAccount] = amount

	def getEndOfForwardingChainFrom(self, account):
		assert account in self.balances or account in self._directRefCounts
		while account in self._redirects:
			account = self._redirects[account]
		return account

	def addTo_Forwarded(self, account, amount):
		account = self.getEndOfForwardingChainFrom(account)
		self.balances[account] += amount
