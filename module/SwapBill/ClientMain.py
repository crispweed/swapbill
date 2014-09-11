from __future__ import print_function
import sys
supportedVersions = ('2.7', '3.2', '3.3', '3.4')
thisVersion = str(sys.version_info.major) + '.' + str(sys.version_info.minor)
if not thisVersion in supportedVersions:
	print('This version of python (' + thisVersion + ') is not supported. Supported versions are:', supportedVersions)
	exit()
import argparse, traceback, struct, time, os
PY3 = sys.version_info.major > 2
if PY3:
	import io
else:
	import StringIO as io
from os import path
try:
	from SwapBill import RawTransaction, Address, TransactionFee, ParseConfig, RPC, Amounts, Util
	from SwapBill import TransactionEncoding, BuildHostedTransaction, Sync, Host, TransactionBuildLayer
	from SwapBill import FormatTransactionForUserDisplay
	from SwapBill import FileBackedList, Wallet, SecretsWallet
	from SwapBill import HostTransaction
	from SwapBill.Sync import SyncAndReturnStateAndOwnedAccounts
	from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser
	from SwapBill.State import InsufficientFundsForTransaction, BadlyFormedTransaction, TransactionFailsAgainstCurrentState
	from SwapBill import HostFromPrefsByProtocol
except ImportError as e:
	message = str(e)
	start = 'No module named '
	assert message.startswith(start)
	module = message[len(start):]
	module = module.strip("'")
	print("Please install the '" + module + "' module.")
	print("e.g. (on linux, for this python version) 'sudo pip-{major}.{minor} install {module}'".format(major=sys.version_info.major, minor=sys.version_info.minor, module=module))
	print("or 'easy_install " + module + "'")
	exit()

class BadAddressArgument(ExceptionReportedToUser):
	def __init__(self, address):
		self._address = address
	def __str__(self):
		return 'An address argument is not valid (' + self._address + ').'
class BadAmountArgument(ExceptionReportedToUser):
	pass
class TransactionNotSuccessfulAgainstCurrentState(ExceptionReportedToUser):
	pass
class SourceAddressUnseeded(ExceptionReportedToUser):
	pass

parser = argparse.ArgumentParser(prog='SwapBillClient', description='the reference implementation of the SwapBill protocol')
parser.add_argument('--dataDir', help='the location of the data directory', default='.')
parser.add_argument('--host', help="host blockchain, can currently be either 'litecoin' or 'bitcoin'", choices=['bitcoin', 'litecoin'], default='bitcoin')
subparsers = parser.add_subparsers(dest='action', help='the action to be taken')

sp = subparsers.add_parser('force_rescan', help='delete cached state, forcing a full rescan on the next query invocation')

sp = subparsers.add_parser('burn', help='destroy host coin to create swapbill')
sp.add_argument('--amount', required=True, help='amount of host coin to be destroyed, as a decimal fraction (one satoshi is 0.00000001)')

sp = subparsers.add_parser('pay', help='make a swapbill payment')
sp.add_argument('--amount', required=True, help='amount of swapbill to be paid, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--toAddress', required=True, help='pay to this address')
sp.add_argument('--blocksUntilExpiry', type=int, default=8, help='if the transaction takes longer than this to go through then the transaction expires (in which case no payment is made and the full amount is returned as change)')
sp.add_argument('--onRevealSecret', action='store_true', help='makes the payment dependant on a secret (generated for the transaction and stored locally)')

sp = subparsers.add_parser('counter_pay', help='make a swapbill payment that depends on the same secret as another payment')
sp.add_argument('--amount', required=True, help='amount of swapbill to be paid, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--toAddress', required=True, help='pay to this address')
sp.add_argument('--blocksUntilExpiry', type=int, default=8, help='if the transaction takes longer than this to go through then the transaction expires (in which case no payment is made and the full amount is returned as change)')
sp.add_argument('--pendingPaymentHost', required=True, help="host blockchain for target payment, can currently be either 'litecoin' or 'bitcoin'", choices=['bitcoin', 'litecoin'])
sp.add_argument('--pendingPaymentID', required=True, help='the id of the pending payment, on the specified blockchain')

sp = subparsers.add_parser('buy_offer', help='make an offer to buy host coin with swapbill')
sp.add_argument('--swapBillOffered', required=True, help='amount of swapbill offered, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--blocksUntilExpiry', type=int, default=8, help='after this number of blocks the offer expires (and swapbill remaining in any unmatched part of the offer is returned)')
sp.add_argument('--exchangeRate', required=True, help='the exchange rate host coin/swapbill as a decimal fraction (e.g. 0.5 means one host coin for two swapbill), must be greater than 0.0 and less than 1.0')

sp = subparsers.add_parser('sell_offer', help='make an offer to sell host coin for swapbill')
sp.add_argument('--hostCoinOffered', required=True, help='amount of host coin offered, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--exchangeRate', required=True, help='the exchange rate host coin/swapbill as a decimal fraction (e.g. 0.5 means one host coin for two swapbill), must be greater than 0.0 and less than 1.0')
sp.add_argument('--backerID', help='the id of the sell backer to be used for the exchange, if a backed sell is desired')
sp.add_argument('--blocksUntilExpiry', type=int, default=2, help="(doesn't apply to backed sells) after this number of blocks the offer expires (and swapbill remaining in any unmatched part of the offer is returned)")
sp.add_argument('--includesCommission', action='store_true', help='(only applies to backed sells) specifies that backer commission is to be taken out of the amount specified for hostCoinOffered (otherwise backer commission will be paid on top of this amount)')

sp = subparsers.add_parser('complete_sell', help='complete a exchange with host coin by fulfilling a pending exchange payment')
sp.add_argument('--pendingExchangeID', required=True, help='the id of the pending exchange payment to fulfill')

sp = subparsers.add_parser('reveal_secret_for_pending_payment', help='provide the secret public key required for a pending payment to go through')
sp.add_argument('--pendingPaymentID', required=True, help='the id of the pending payment')

sp = subparsers.add_parser('back_sells', help='commit swapbill to back exchanges with host coin')
sp.add_argument('--backingSwapBill', required=True, help='amount of swapbill to commit, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--transactionsBacked', required=True, help='the number of transactions you want to back, which then implies a maximum backing amount per transaction')
sp.add_argument('--blocksUntilExpiry', type=int, default=200, help='number of blocks for which the backing amount should remain committed')
sp.add_argument('--commission', required=True, help='the rate of commission for backed transactions, as a decimal fraction (must be greater than 0.0 and less than 1.0)')

subparsers.add_parser('make_seed_output', help='make a transaction for use as a seed output')

subparsers.add_parser('get_receive_address', help='generate a new key pair for the swapbill wallet and display the corresponding public payment address')

sp = subparsers.add_parser('get_balance', help='get current SwapBill balance')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_buy_offers', help='get list of currently active host coin buy offers')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_sell_offers', help='get list of currently active host coin sell offers')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_pending_exchanges', help='get current SwapBill pending exchange payments')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_sell_backers', help='get information about funds currently commited to backing host coin sell transactions')
sp.add_argument('--withExchangeRate', help='an exchange rate (host coin/swapbill, as a decimal fraction), if specified maximum exchange amounts will also be displayed in host currency based on this exchange rate')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_pending_payments', help='get information payments currently pending proof of receipt')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_state_info', help='get some general state information')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

def DoSync(dataDir, protocol, includePending, secretsWatchList, secretsWallet, out):
	dataDir = path.join(dataDir, protocol)
	if not path.exists(dataDir):
		try:
			os.mkdir(dataDir)
		except Exception as e:
			raise ExceptionReportedToUser("Failed to create directory " + dataDir + ":", e)
	host = HostFromPrefsByProtocol.HostFromPrefsByProtocol(protocol=protocol, dataDir=dataDir)
	walletPrivateKeys = FileBackedList.FileBackedList(path.join(dataDir, 'wallet.txt'))
	wallet = Wallet.Wallet(walletPrivateKeys)
	state, ownedAccounts = SyncAndReturnStateAndOwnedAccounts(dataDir, protocol, wallet, host, secretsWatchList=secretsWatchList, secretsWallet=secretsWallet, includePending=includePending, out=out)
	return host, wallet, state, ownedAccounts

def Main(commandLineArgs=sys.argv[1:], out=sys.stdout):
	args = parser.parse_args(commandLineArgs)

	if not path.isdir(args.dataDir):
		raise ExceptionReportedToUser("The following path (specified for data directory parameter) is not a valid path to an existing directory: " + args.dataDir)

	dataDir = path.join(args.dataDir, 'swapBillData')
	if not path.exists(dataDir):
		try:
			os.mkdir(dataDir)
		except Exception as e:
			raise ExceptionReportedToUser("Failed to create directory " + dataDir + ":", e)

	if args.action == 'force_rescan':
		dataDir = path.join(dataDir, args.host)
		Sync.ForceRescan(dataDir)
		return []
		
	secretsWalletSecrets = FileBackedList.FileBackedList(path.join(dataDir, 'secretsWallet.txt'))
	secretsWallet = SecretsWallet.SecretsWallet(secretsWalletSecrets)
	secretsWatchList = FileBackedList.FileBackedList(path.join(dataDir, 'secretsWatchList.txt'))

	if args.action == 'get_state_info':
		syncOut = io.StringIO()
	else:
		syncOut = out

	includePending = hasattr(args, 'includepending') and args.includepending

	#startTime = time.clock()
	host, wallet, state, ownedAccounts = DoSync(dataDir=dataDir, protocol=args.host, includePending=includePending, secretsWatchList=secretsWatchList, secretsWallet=secretsWallet, out=syncOut)
	#elapsedTime = time.clock() - startTime
	
	if args.action == 'get_state_info':
		formattedBalances = {}
		for account in state._balances.balances:
			key = host.formatAccountForEndUser(account)
			formattedBalances[key] = state._balances.balanceFor(account)
		info = {
		    'totalCreated':state._totalCreated,
		    'atEndOfBlock':state._currentBlockIndex - 1, 'balances':formattedBalances, 'syncOutput':syncOut.getvalue(),
		    #'syncTime':elapsedTime,
		    'numberOfHostCoinBuyOffers':state._hostCoinBuys.size(),
		    'numberOfHostCoinSellOffers':state._hostCoinSells.size(),
		    'numberOfPendingExchanges':len(state._pendingExchanges),
		    'numberOfOutputs':len(ownedAccounts.accounts)
		}
		return info

	transactionBuildLayer = TransactionBuildLayer.TransactionBuildLayer(host, ownedAccounts)

	def SetFeeAndSend(baseTX, baseTXInputsAmount, unspent):
		change = host.getManagedAddress()
		maximumSignedSize = TransactionFee.startingMaximumSize
		transactionFee = TransactionFee.startingFee
		while True:
			try:
				filledOutTX = BuildHostedTransaction.AddPaymentFeesAndChange(baseTX, baseTXInputsAmount, TransactionFee.dustLimit, transactionFee, unspent, change)
				return transactionBuildLayer.sendTransaction(filledOutTX, maximumSignedSize)
			except Host.MaximumSignedSizeExceeded:
				print("Transaction fee increased.", file=out)
				maximumSignedSize += TransactionFee.sizeStep
				transactionFee += TransactionFee.feeStep

	def CheckAndSend_Common(transactionType, sourceAccounts, outputs, outputPubKeys, details):
		print('attempting to send ' + FormatTransactionForUserDisplay.Format(host, transactionType, outputs, outputPubKeys, details), file=out)
		baseTX = TransactionEncoding.FromStateTransaction(transactionType, sourceAccounts, outputs, outputPubKeys, details)
		backingUnspent = transactionBuildLayer.getUnspent()
		baseInputsAmount = 0
		for i in range(baseTX.numberOfInputs()):
			txID = baseTX.inputTXID(i)
			vOut = baseTX.inputVOut(i)
			baseInputsAmount += ownedAccounts.accounts[(txID, vOut)][0]
		txID = SetFeeAndSend(baseTX, baseInputsAmount, backingUnspent)
		return {'transaction id':txID}

	def CheckAndSend_Funded(transactionType, outputs, outputPubKeys, details):
		TransactionEncoding.FromStateTransaction(transactionType, [], outputs, outputPubKeys, details) # for initial parameter checking
		transactionBuildLayer.startTransactionConstruction()
		swapBillUnspent = transactionBuildLayer.getSwapBillUnspent(state)
		sourceAccounts = []
		while True:
			try:
				state.checkTransaction(transactionType, outputs=outputs, transactionDetails=details, sourceAccounts=sourceAccounts)
			except InsufficientFundsForTransaction:
				pass
			except TransactionFailsAgainstCurrentState as e:
				raise TransactionNotSuccessfulAgainstCurrentState('Transaction would not complete successfully against current state: ' + str(e))
			except BadlyFormedTransaction as e:
				raise ExceptionReportedToUser('Transaction does not meet protocol constraints: ' + str(e))
			else:
				break
			if not swapBillUnspent:
				raise ExceptionReportedToUser('Insufficient swapbill for transaction.')
			transactionBuildLayer.swapBillUnspentUsed(swapBillUnspent[0])
			sourceAccounts.append(swapBillUnspent[0])
			swapBillUnspent = swapBillUnspent[1:]
		return CheckAndSend_Common(transactionType, sourceAccounts, outputs, outputPubKeys, details)

	def CheckAndSend_UnFunded(transactionType, outputs, outputPubKeys, details):
		TransactionEncoding.FromStateTransaction(transactionType, None, outputs, outputPubKeys, details) # for initial parameter checking
		transactionBuildLayer.startTransactionConstruction()
		try:
			state.checkTransaction(transactionType, outputs=outputs, transactionDetails=details, sourceAccounts=None)
		except TransactionFailsAgainstCurrentState as e:
			raise TransactionNotSuccessfulAgainstCurrentState('Transaction would not complete successfully against current state: ' + str(e))
		except BadlyFormedTransaction as e:
			raise ExceptionReportedToUser('Transaction does not follow protocol rules: ' + str(e))
		return CheckAndSend_Common(transactionType, None, outputs, outputPubKeys, details)

	def CheckAndReturnPubKeyHash(address):
		try:
			pubKeyHash = Address.ToPubKeyHash(host.getAddressVersion(), address)
		except Address.BadAddress as e:
			raise BadAddressArgument(address)
		return pubKeyHash
	def CheckAndReturnPubKeyHash_AnyVersion(address):
		try:
			pubKeyHash = Address.ToPubKeyHash_AnyVersion(address)
		except Address.BadAddress as e:
			raise BadAddressArgument(address)
		return pubKeyHash

	def CheckedConvertFromHex(hexString):
		try:
			return Util.fromHex(hexString)
		except TypeError:
			raise ExceptionReportedToUser("Bad hex string '" + hexString + "'")

	if args.action == 'burn':
		amount = Amounts.FromString(args.amount)
		if amount < TransactionFee.dustLimit:
			raise ExceptionReportedToUser('Burn amount is below dust limit.')
		transactionType = 'Burn'
		outputs = ('destination',)
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(),)
		details = {'amount':amount}
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'pay':
		outputs = ('change', 'destination')
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(), CheckAndReturnPubKeyHash(args.toAddress))
		details = {
		    'amount':Amounts.FromString(args.amount),
		    'maxBlock':state._currentBlockIndex + args.blocksUntilExpiry
		}
		if args.onRevealSecret:
			transactionType = 'PayOnRevealSecret'
			details['secretAddress'] = secretsWallet.addPublicKeySecret()
		else:
			# standard pay transaction
			transactionType = 'Pay'
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'counter_pay':
		outputs = ('change', 'destination')
		if args.host == args.pendingPaymentHost:
			altState = state
		else:
			print("(Syncing on target blockchain.)", file=out)
			syncResults = DoSync(dataDir=dataDir, protocol=args.pendingPaymentHost, secretsWatchList=secretsWatchList, secretsWallet=secretsWallet, includePending=False, out=out)
			altState = syncResults[2]
		if not int(args.pendingPaymentID) in altState._pendingPays:
			raise ExceptionReportedToUser('No pending payment with the specified ID on the target blockchain.')
		pay = altState._pendingPays[int(args.pendingPaymentID)]
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(), CheckAndReturnPubKeyHash(args.toAddress))
		details = {
		'amount':Amounts.FromString(args.amount),
		'maxBlock':state._currentBlockIndex + args.blocksUntilExpiry
		}
		transactionType = 'PayOnRevealSecret'
		details['secretAddress'] = pay.secretHash
		secretsWatchList.append(pay.secretHash)
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'buy_offer':
		transactionType = 'BuyOffer'
		outputs = ('hostCoinBuy',)
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(),)
		details = {
		    'swapBillOffered':Amounts.FromString(args.swapBillOffered),
		    'exchangeRate':Amounts.PercentFromString(args.exchangeRate),
		    'receivingAddress':host.getManagedAddress(),
		    'maxBlock':state._currentBlockIndex + args.blocksUntilExpiry
		}
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'sell_offer':
		details = {'exchangeRate':Amounts.PercentFromString(args.exchangeRate)}
		if args.backerID is None:
			transactionType = 'SellOffer'
			outputs = ('hostCoinSell',)
			details['maxBlock'] = state._currentBlockIndex + args.blocksUntilExpiry
			details['hostCoinOffered'] = Amounts.FromString(args.hostCoinOffered)
		else:
			backerID = int(args.backerID)
			if not backerID in state._hostCoinSellBackers:
				raise ExceptionReportedToUser('No backer with the specified ID.')
			backer = state._hostCoinSellBackers[backerID]
			transactionType = 'BackedSellOffer'
			outputs = ('sellerReceive',)
			ltc = Amounts.FromString(args.hostCoinOffered)
			if args.includesCommission:
				details['hostCoinOfferedPlusCommission'] = ltc
			else:
				ltcCommission = ltc * backer.commission // Amounts.percentDivisor
				details['hostCoinOfferedPlusCommission'] = ltc + ltcCommission
			details['backerIndex'] = int(args.backerID)
			details['backerHostCoinReceiveAddress'] = backer.hostCoinReceiveAddress
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(),)
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'complete_sell':
		transactionType = 'ExchangeCompletion'
		pendingExchangeID = int(args.pendingExchangeID)
		if not pendingExchangeID in state._pendingExchanges:
			raise ExceptionReportedToUser('No pending exchange with the specified ID.')
		exchange = state._pendingExchanges[pendingExchangeID]
		details = {
		    'pendingExchangeIndex':pendingExchangeID,
		    'destinationAddress':exchange.buyerLTCReceive,
		    'destinationAmount':exchange.ltc
		}
		return CheckAndSend_UnFunded(transactionType, (), (), details)

	elif args.action == 'reveal_secret_for_pending_payment':
		transactionType = 'RevealPendingPaymentSecret'
		pendingPaymentID = int(args.pendingPaymentID)
		if not pendingPaymentID in state._pendingPays:
			raise ExceptionReportedToUser('No pending payment with the specified ID.')
		pay = state._pendingPays[pendingPaymentID]
		if not secretsWallet.hasKeyPairForPubKeyHash(pay.secretHash):
			raise ExceptionReportedToUser('The secret for this pending payment is not known.')		
		details = {
		    'pendingPayIndex':pendingPaymentID,
		    'publicKeySecret':secretsWallet.publicKeyForPubKeyHash(pay.secretHash)
		}
		return CheckAndSend_UnFunded(transactionType, (), (), details)

	elif args.action == 'back_sells':
		transactionType = 'BackLTCSells'
		outputs = ('hostCoinSellBacker',)
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(),)
		details = {
		    'backingAmount':Amounts.FromString(args.backingSwapBill),
		    'transactionsBacked':int(args.transactionsBacked),
		    'hostCoinReceiveAddress':host.getManagedAddress(),
		    'commission':Amounts.PercentFromString(args.commission),
		    'maxBlock':state._currentBlockIndex + args.blocksUntilExpiry
		}
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'make_seed_output':
		tx = HostTransaction.InMemoryTransaction()
		pubKeyHash = wallet.addKeyPairAndReturnPubKeyHash()
		tx.addOutput(pubKeyHash, 0)
		transactionBuildLayer.startTransactionConstruction()
		backingUnspent = transactionBuildLayer.getUnspent()		
		txID = SetFeeAndSend(tx, 0, backingUnspent)
		return {'transaction id':txID, 'pubKeyHash':Util.toHex(pubKeyHash)}

	elif args.action == 'get_receive_address':
		pubKeyHash = wallet.addKeyPairAndReturnPubKeyHash()
		address = Address.FromPubKeyHash(host.getAddressVersion(), pubKeyHash)
		return {'receive_address': address}

	elif args.action == 'get_balance':
		total = 0
		for account in ownedAccounts.accounts:
			total += state._balances.balanceFor(account)
		return {'balance':Amounts.ToString(total)}

	elif args.action == 'get_buy_offers':
		result = []
		for offer in state._hostCoinBuys.getSortedOffers():
			mine = offer.refundAccount in ownedAccounts.tradeOfferChangeCounts
			exchangeAmount = offer._swapBillOffered
			ltc = offer.ltcEquivalent()
			details = {'swapbill offered':Amounts.ToString(exchangeAmount), 'host coin equivalent':Amounts.ToString(ltc), 'mine':mine}
			result.append(('exchange rate', Amounts.PercentToString(offer.rate), details))
		return result

	elif args.action == 'get_sell_offers':
		result = []
		for offer in state._hostCoinSells.getSortedOffers():
			mine = offer.receivingAccount in ownedAccounts.tradeOfferChangeCounts
			ltc = offer._hostCoinOffered
			depositAmount = offer._swapBillDeposit
			swapBillEquivalent = offer.swapBillEquivalent()
			details = {'host coin offered':Amounts.ToString(ltc), 'deposit':Amounts.ToString(depositAmount), 'swapbill equivalent':Amounts.ToString(swapBillEquivalent), 'mine':mine}
			if offer.isBacked:
				details['backer id'] = offer.backerIndex
			result.append(('exchange rate', Amounts.PercentToString(offer.rate), details))
		return result

	elif args.action == 'get_pending_exchanges':
		result = []
		for key in state._pendingExchanges:
			d = {}
			exchange = state._pendingExchanges[key]
			d['I am seller (and need to complete)'] = exchange.sellerAccount in ownedAccounts.tradeOfferChangeCounts
			d['I am buyer (and waiting for payment)'] = exchange.buyerAccount in ownedAccounts.tradeOfferChangeCounts
			d['deposit paid by seller'] = Amounts.ToString(exchange.swapBillDeposit)
			d['swap bill paid by buyer'] = Amounts.ToString(exchange.swapBillAmount)
			d['outstanding host coin payment amount'] = Amounts.ToString(exchange.ltc)
			d['expires on block'] = exchange.expiry
			d['blocks until expiry'] = exchange.expiry - state._currentBlockIndex + 1
			d['confirmations'] = state._protocolParams['blocksForExchangeCompletion'] - (exchange.expiry - state._currentBlockIndex)
			if exchange.backerIndex != -1:
				d['backer id'] = exchange.backerIndex
			result.append(('pending exchange index', key, d))
		return result

	elif args.action == 'get_sell_backers':
		result = []
		for key in state._hostCoinSellBackers:
			d = {}
			backer = state._hostCoinSellBackers[key]
			d['I am backer'] = backer.refundAccount in ownedAccounts.tradeOfferChangeCounts
			d['backing amount'] = Amounts.ToString(backer.backingAmount)
			d['backing amount per transaction'] = Amounts.ToString(backer.transactionMax)
			d['transactions covered'] = backer.backingAmount // backer.transactionMax
			d['expires on block'] = backer.expiry
			d['blocks until expiry'] = backer.expiry - state._currentBlockIndex + 1
			d['commission'] = Amounts.PercentToString(backer.commission)
			d['maximum exchange swapbill'] = Amounts.ToString(state.calculateBackerMaximumExchange(backer))
			if args.withExchangeRate is not None:
				rate = Amounts.PercentFromString(args.withExchangeRate)
				d['maximum exchange host coin'] = Amounts.ToString(state.calculateBackerMaximumExchangeInHostCoin(backer, rate))
			result.append(('host coin sell backer index', key, d))
		return result

	elif args.action == 'get_pending_payments':
		result = []
		for key in state._pendingPays:
			d = {}
			pay = state._pendingPays[key]
			d['paid by me'] = pay.refundAccount in ownedAccounts.tradeOfferChangeCounts
			d['paid to me'] = pay.destinationAccount in ownedAccounts.tradeOfferChangeCounts
			d['amount'] = Amounts.ToString(pay.amount)
			d['expires on block'] = pay.expiry
			d['blocks until expiry'] = pay.expiry - state._currentBlockIndex + 1
			d['confirmations'] = state._currentBlockIndex - pay.confirmedOnBlock
			if secretsWallet.hasKeyPairForPubKeyHash(pay.secretHash):
				d['I hold secret'] = True
			result.append(('pending payment index', key, d))
		return result

	else:
		parser.print_help()
