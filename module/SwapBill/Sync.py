from __future__ import print_function
import sys, binascii
from os import path
from collections import deque
from SwapBill import State, RawTransaction, TransactionEncoding, PickledCache, OwnedAccounts, ControlAddressPrefix, KeyPair, SeedAccounts
from SwapBill import ProtocolParameters
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

stateVersion = 4
ownedAccountsVersion = 1

def _processTransactions(state, wallet, ownedAccounts, secretsWatchList, secretsWallet, transactions, applyToState, reportPrefix, out):
	for txID, hostTXBytes in transactions:
		if RawTransaction.UnexpectedFormat_Fast(hostTXBytes, ControlAddressPrefix.prefix):
			continue
		hostTX, scriptPubKeys = RawTransaction.Decode(hostTXBytes)
		inputsReport = ownedAccounts.updateForSpent(hostTX, state)
		try:
			transactionType, sourceAccounts, outputs, transactionDetails = TransactionEncoding.ToStateTransaction(hostTX)
			appliedSuccessfully = True
		except (TransactionEncoding.NotValidSwapBillTransaction, TransactionEncoding.UnsupportedTransaction):
			if inputsReport != '':
				print(reportPrefix + ': <invalid transaction>', file=out)
				print(inputsReport, end="", file=out)
			continue
		if 'publicKeySecret' in transactionDetails:
			secret = transactionDetails['publicKeySecret']
			secretHash = KeyPair.PublicKeyToPubKeyHash(secret)
			if secretHash in secretsWatchList:
				if not secretsWallet.hasKeyPairForPubKeyHash(secretHash):
					secretHashHex = binascii.hexlify(secretHash).decode('ascii')
					print(reportPrefix + ': storing revealed secret with hash ' + secretHashHex, file=out)
					secretsWallet.addPublicKeySecret(secret)
		if inputsReport != '':
			print(reportPrefix + ': ' + transactionType, file=out)
			print(inputsReport, end="", file=out)
		if not applyToState:
			continue
		#inBetweenReport = ownedAccounts.checkForTradeOfferChanges(state)
		#assert inBetweenReport == ''
		error = state.applyTransaction(transactionType, txID, sourceAccounts=sourceAccounts, transactionDetails=transactionDetails, outputs=outputs)
		outputsReport = ownedAccounts.checkForTradeOfferChanges(state)
		outputsReport += ownedAccounts.updateForNewOutputs(wallet, state, txID, hostTX, outputs, scriptPubKeys)
		if outputsReport:
			if inputsReport == '':
				# didn't print this line yet
				print(reportPrefix + ': ' + transactionType, file=out)
			print(outputsReport, end="", file=out)
		if (outputsReport or inputsReport) and error is not None:
			print(' * failed:', error, file=out)

def _processBlock(host, state, wallet, ownedAccounts, secretsWatchList, secretsWallet, blockHash, reportPrefix, out):
	transactions = host.getBlockTransactions(blockHash)
	_processTransactions(state, wallet, ownedAccounts, secretsWatchList, secretsWallet, transactions, True, reportPrefix, out)
	#inBetweenReport = ownedAccounts.checkForTradeOfferChanges(state)
	#assert inBetweenReport == ''
	state.advanceToNextBlock()
	tradeOffersChanged = ownedAccounts.checkForTradeOfferChanges(state)
	if tradeOffersChanged:
		print('trade offer or pending exchange expired', file=out)

def ForceRescan(cacheDirectory):
	PickledCache.Remove(cacheDirectory, 'State')

def SyncAndReturnStateAndOwnedAccounts(cacheDirectory, protocol, wallet, host, secretsWatchList, secretsWallet, includePending, out):
	params = ProtocolParameters.byHost[protocol]

	loaded = False
	try:
		(blockIndex, blockHash, state) = PickledCache.Load(cacheDirectory, 'State', stateVersion)
		ownedAccounts = PickledCache.Load(cacheDirectory, 'OwnedAccounts', ownedAccountsVersion)
		loaded = True
	except PickledCache.LoadFailedException as e:
		print('Failed to load from cache, full index generation required (' + str(e) + ')', file=out)
	if loaded and host.getBlockHashAtIndexOrNone(blockIndex) != blockHash:
		print('The block corresponding with cached state has been orphaned, full index generation required.', file=out)
		loaded = False
	if loaded and not state.parametersMatch(params):
		print('Start config does not match config from loaded state, full index generation required.', file=out)
		loaded = False
	if loaded:
		print('Loaded cached state data successfully', file=out)
	else:
		blockIndex = params['startBlock']
		blockHash = host.getBlockHashAtIndexOrNone(blockIndex)
		if blockHash is None:
			raise ExceptionReportedToUser('Block chain has not reached the swapbill start block (' + str(blockIndex) + ').')
		if blockHash != params['startBlockHash']:
			raise ExceptionReportedToUser('Block hash for swapbill start block does not match.')
		ownedAccounts = OwnedAccounts.OwnedAccounts()
		seedAccount,seedOutputAmount,seedPubKeyHash,seedAccountScriptPubKey,seedAmount = SeedAccounts.GetSeedAccountInfo(protocol)
		if wallet.hasKeyPairForPubKeyHash(seedPubKeyHash):
			seedAccountPrivateKey = wallet.privateKeyForPubKeyHash(seedPubKeyHash)
			ownedAccounts.addSeedOutput(seedAccount, seedOutputAmount, seedAccountPrivateKey, seedAccountScriptPubKey)
		state = State.State(params, seedAccount=seedAccount, seedAmount=seedAmount)

	print('State update starting from block', blockIndex, file=out)

	toProcess = deque()
	mostRecentHash = blockHash
	while True:
		nextBlockHash = host.getNextBlockHash(mostRecentHash)
		if nextBlockHash is None:
			break
		## hard coded value used here for number of blocks to lag behind with persistent state
		if len(toProcess) == 20:
			## advance cached state
			_processBlock(host, state, wallet, ownedAccounts, secretsWatchList, secretsWallet, blockHash, 'committed', out=out)
			popped = toProcess.popleft()
			blockIndex += 1
			blockHash = popped
		mostRecentHash = nextBlockHash
		toProcess.append(mostRecentHash)

	PickledCache.Save((blockIndex, blockHash, state), stateVersion, cacheDirectory, 'State')
	PickledCache.Save(ownedAccounts, ownedAccountsVersion, cacheDirectory, 'OwnedAccounts')

	print("Committed state updated to start of block {}".format(state._currentBlockIndex), file=out)

	while len(toProcess) > 0:
		## advance in memory state
		_processBlock(host, state, wallet, ownedAccounts, secretsWatchList, secretsWallet, blockHash, 'in memory', out=out)
		popped = toProcess.popleft()
		blockIndex += 1
		blockHash = popped
	_processBlock(host, state, wallet, ownedAccounts, secretsWatchList, secretsWallet, blockHash, 'in memory', out=out)
	blockIndex += 1

	assert state._currentBlockIndex == blockIndex
	print("In memory state updated to end of block {}".format(state._currentBlockIndex - 1), file=out)

	# note that the best block chain may have changed during the above
	# and so the following set of memory pool transactions may not correspond to the actual block chain endpoint we synchronised to
	# and this may then result in us trying to make double spends, in certain situations
	# the host should then refuse these transactions, and so this is not a disaster
	# (and double spend situations can probably also arise more generally in the case of block chain forks, with it not possible for us to always prevent this)
	# but we can potentially be more careful about this by checking best block chain after getting memory pool transactions
	# and restarting the block chain traversal if this does not match up
	memPoolTransactions = host.getMemPoolTransactions()
	_processTransactions(state, wallet, ownedAccounts, secretsWatchList, secretsWallet, memPoolTransactions, includePending, 'in memory pool', out)

	return state, ownedAccounts

#def LoadAndReturnStateWithoutUpdate(config):
	#try:
		#blockIndex, blockHash, state = _load()
	#except ReindexingRequiredException as e:
		#print('Could not load cached state, so returning empty initial state! (' + str(e) + ')')
	#return state
