from __future__ import print_function
import sys
supportedVersions = ('2.7', '3.2', '3.3', '3.4')
thisVersion = str(sys.version_info.major) + '.' + str(sys.version_info.minor)
if not thisVersion in supportedVersions:
	print('This version of python (' + thisVersion + ') is not supported. Supported versions are:', supportedVersions)
	exit()
import argparse, binascii, traceback, struct, time, os
PY3 = sys.version_info.major > 2
if PY3:
	import io
else:
	import StringIO as io
from os import path
try:
	from SwapBill import RawTransaction, Address, TransactionFee, ParseConfig, RPC, Amounts
	from SwapBill import TransactionEncoding, BuildHostedTransaction, Sync, Host, TransactionBuildLayer, Wallet
	from SwapBill import FormatTransactionForUserDisplay
	from SwapBill.Sync import SyncAndReturnStateAndOwnedAccounts
	from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser
	from SwapBill.State import InsufficientFundsForTransaction, BadlyFormedTransaction, TransactionFailsAgainstCurrentState
	from SwapBill.HardCodedProtocolConstraints import Constraints
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
parser.add_argument('--configFile', help='the location of the configuration file')
parser.add_argument('--dataDir', help='the location of the data directory', default='.')
parser.add_argument('--forceRescan', help='force a full block chain rescan', action='store_true')
subparsers = parser.add_subparsers(dest='action', help='the action to be taken')

sp = subparsers.add_parser('burn', help='destroy litecoin to create swapbill')
sp.add_argument('--amount', required=True, help='amount of litecoin to be destroyed, as a decimal fraction (one satoshi is 0.00000001)')

sp = subparsers.add_parser('pay', help='make a swapbill payment')
sp.add_argument('--amount', required=True, help='amount of swapbill to be paid, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--toAddress', required=True, help='pay to this address')
sp.add_argument('--blocksUntilExpiry', type=int, default=8, help='if the transaction takes longer than this to go through then the transaction expires (in which case no payment is made and the full amount is returned as change)')

sp = subparsers.add_parser('post_ltc_buy', help='make an offer to buy litecoin with swapbill')
sp.add_argument('--swapBillOffered', required=True, help='amount of swapbill offered, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--blocksUntilExpiry', type=int, default=8, help='after this number of blocks the offer expires (and swapbill remaining in any unmatched part of the offer is returned)')
sp.add_argument('--exchangeRate', required=True, help='the exchange rate LTC/SWP as a decimal fraction (e.g. 0.5 means one LTC for two swapbill), must be greater than 0.0 and less than 1.0')

sp = subparsers.add_parser('post_ltc_sell', help='make an offer to sell litecoin for swapbill')
sp.add_argument('--ltcOffered', required=True, help='amount of ltc offered, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--exchangeRate', required=True, help='the exchange rate LTC/SWP as a decimal fraction (e.g. 0.5 means one LTC for two swapbill), must be greater than 0.0 and less than 1.0')
sp.add_argument('--backerID', help='the id of the ltc sell backer to be used for the exchange, if a backed sell is desired')
sp.add_argument('--blocksUntilExpiry', type=int, default=2, help="(doesn't apply to backed sells) after this number of blocks the offer expires (and swapbill remaining in any unmatched part of the offer is returned)")
sp.add_argument('--includesCommission', help='(only applies to backed sells) specifies that backer commission is to be taken out of ltcOffered (otherwise backed commission will be paid on top of ltcOffered)', action='store_true')

sp = subparsers.add_parser('complete_ltc_sell', help='complete an ltc exchange by fulfilling a pending exchange payment')
sp.add_argument('--pendingExchangeID', required=True, help='the id of the pending exchange payment to fulfill')

sp = subparsers.add_parser('back_ltc_sells', help='commit swapbill to back ltc exchanges')
sp.add_argument('--backingSwapBill', required=True, help='amount of swapbill to commit, as a decimal fraction (one satoshi is 0.00000001)')
sp.add_argument('--transactionsBacked', required=True, help='the number of transactions you want to back, which then implies a maximum backing amount per transaction')
sp.add_argument('--blocksUntilExpiry', type=int, default=200, help='number of blocks for which the backing amount should remain committed')
sp.add_argument('--commission', required=True, help='the rate of commission for backed transactions, as a decimal fraction (must be greater than 0.0 and less than 1.0)')

subparsers.add_parser('get_receive_address', help='generate a new key pair for the swapbill wallet and display the corresponding public payment address')

sp = subparsers.add_parser('get_balance', help='get current SwapBill balance')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_buy_offers', help='get list of currently active litecoin buy offers')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_sell_offers', help='get list of currently active litecoin sell offers')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_pending_exchanges', help='get current SwapBill pending exchange payments')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_ltc_sell_backers', help='get information about funds currently commited to backing ltc sell operations')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

sp = subparsers.add_parser('get_state_info', help='get some general state information')
sp.add_argument('-i', '--includepending', help='include transactions that have been submitted but not yet confirmed (based on host memory pool)', action='store_true')

def Main(startBlockIndex, startBlockHash, useTestNet, commandLineArgs=sys.argv[1:], host=None, keyGenerator=None, out=sys.stdout):
	args = parser.parse_args(commandLineArgs)

	if not path.isdir(args.dataDir):
		raise ExceptionReportedToUser("The following path (specified for data directory parameter) is not a valid path to an existing directory: " + args.dataDir)

	dataDir = path.join(args.dataDir, 'swapBillData')
	if not path.exists(dataDir):
		try:
			os.mkdir(dataDir)
		except Exception as e:
			raise ExceptionReportedToUser("Failed to create directory " + dataDir + ":", e)

	if useTestNet:
		addressVersion = b'\x6f'
		privateKeyAddressVersion = b'\xef'
	else:
		addressVersion = b'\x30'
		privateKeyAddressVersion = b'\xbf'

	wallet = Wallet.Wallet(path.join(dataDir, 'wallet.txt'), privateKeyAddressVersion=privateKeyAddressVersion, keyGenerator=keyGenerator) # litecoin testnet private key address version

	if host is None:
		configFile = args.configFile
		if configFile is None:
			if os.name == 'nt':
				configFile = path.join(path.expanduser("~"), 'AppData', 'Roaming', 'Litecoin', 'litecoin.conf')
			else:
				configFile = path.join(path.expanduser("~"), '.litecoin', 'litecoin.conf')
		with open(configFile, mode='rb') as f:
			configFileBuffer = f.read()
		clientConfig = ParseConfig.Parse(configFileBuffer)
		RPC_HOST = clientConfig.get('externalip', 'localhost')
		try:
			RPC_PORT = clientConfig['rpcport']
		except KeyError:
			if useTestNet:
				RPC_PORT = 19332
			else:
				RPC_PORT = 9332
		assert int(RPC_PORT) > 1 and int(RPC_PORT) < 65535
		try:
			RPC_USER = clientConfig['rpcuser']
			RPC_PASSWORD = clientConfig['rpcpassword']
		except KeyError:
			raise ExceptionReportedToUser('Values for rpcuser and rpcpassword must both be set in your config file.')
		rpcHost = RPC.Host('http://' + RPC_USER + ':' + RPC_PASSWORD + '@' + RPC_HOST + ':' + str(RPC_PORT))
		submittedTransactionsLogFileName = path.join(dataDir, 'submittedTransactions.txt')
		host = Host.Host(rpcHost=rpcHost, addressVersion=addressVersion, privateKeyAddressVersion=privateKeyAddressVersion, submittedTransactionsLogFileName=submittedTransactionsLogFileName)

	includePending = hasattr(args, 'includepending') and args.includepending

	if args.action == 'get_state_info':
		syncOut = io.StringIO()
		startTime = time.clock()
		state, ownedAccounts = SyncAndReturnStateAndOwnedAccounts(dataDir, startBlockIndex, startBlockHash, wallet, host, includePending=includePending, forceRescan=args.forceRescan, out=syncOut)
		elapsedTime = time.clock() - startTime
		formattedBalances = {}
		for account in state._balances.balances:
			key = host.formatAccountForEndUser(account)
			formattedBalances[key] = state._balances.balanceFor(account)
		info = {
		    'totalCreated':state._totalCreated,
		    'atEndOfBlock':state._currentBlockIndex - 1, 'balances':formattedBalances, 'syncOutput':syncOut.getvalue(),
		    'syncTime':elapsedTime,
		    'numberOfLTCBuyOffers':state._ltcBuys.size(),
		    'numberOfLTCSellOffers':state._ltcSells.size(),
		    'numberOfPendingExchanges':len(state._pendingExchanges),
		    'numberOfOutputs':len(ownedAccounts.accounts)
		}
		return info

	state, ownedAccounts = SyncAndReturnStateAndOwnedAccounts(dataDir, startBlockIndex, startBlockHash, wallet, host, includePending=includePending, forceRescan=args.forceRescan, out=out)

	transactionBuildLayer = TransactionBuildLayer.TransactionBuildLayer(host, ownedAccounts)

	def SetFeeAndSend(baseTX, baseTXInputsAmount, unspent):
		change = host.getNewNonSwapBillAddress()
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
		change = host.getNewNonSwapBillAddress()
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
			pubKeyHash = host.addressFromEndUserFormat(address)
		except Address.BadAddress as e:
			raise BadAddressArgument(address)
		return pubKeyHash

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
		transactionType = 'Pay'
		outputs = ('change', 'destination')
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(), CheckAndReturnPubKeyHash(args.toAddress))
		details = {
		    'amount':Amounts.FromString(args.amount),
		    'maxBlock':state._currentBlockIndex + args.blocksUntilExpiry
		}
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'post_ltc_buy':
		transactionType = 'LTCBuyOffer'
		outputs = ('ltcBuy',)
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(),)
		details = {
		    'swapBillOffered':Amounts.FromString(args.swapBillOffered),
		    'exchangeRate':Amounts.PercentFromString(args.exchangeRate),
		    'receivingAddress':host.getNewNonSwapBillAddress(),
		    'maxBlock':state._currentBlockIndex + args.blocksUntilExpiry
		}
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'post_ltc_sell':
		details = {'exchangeRate':Amounts.PercentFromString(args.exchangeRate)}
		if args.backerID is None:
			transactionType = 'LTCSellOffer'
			outputs = ('ltcSell',)
			details['maxBlock'] = state._currentBlockIndex + args.blocksUntilExpiry
			details['ltcOffered'] = Amounts.FromString(args.ltcOffered)
		else:
			backerID = int(args.backerID)
			if not backerID in state._ltcSellBackers:
				raise ExceptionReportedToUser('No backer with the specified ID.')
			backer = state._ltcSellBackers[backerID]
			transactionType = 'BackedLTCSellOffer'
			outputs = ('sellerReceive',)
			ltc = Amounts.FromString(args.ltcOffered)
			if args.includesCommission:
				details['ltcOfferedPlusCommission'] = ltc
			else:
				ltcCommission = ltc * backer.commission // Amounts.percentDivisor
				details['ltcOfferedPlusCommission'] = ltc + ltcCommission
			details['backerIndex'] = int(args.backerID)
			details['backerLTCReceiveAddress'] = backer.ltcReceiveAddress
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(),)
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'complete_ltc_sell':
		transactionType = 'LTCExchangeCompletion'
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

	elif args.action == 'back_ltc_sells':
		transactionType = 'BackLTCSells'
		outputs = ('ltcSellBacker',)
		outputPubKeyHashes = (wallet.addKeyPairAndReturnPubKeyHash(),)
		details = {
		    'backingAmount':Amounts.FromString(args.backingSwapBill),
		    'transactionsBacked':int(args.transactionsBacked),
		    'ltcReceiveAddress':host.getNewNonSwapBillAddress(),
		    'commission':Amounts.PercentFromString(args.commission),
		    'maxBlock':state._currentBlockIndex + args.blocksUntilExpiry
		}
		return CheckAndSend_Funded(transactionType, outputs, outputPubKeyHashes, details)

	elif args.action == 'get_receive_address':
		pubKeyHash = wallet.addKeyPairAndReturnPubKeyHash()
		return {'receive_address': host.formatAddressForEndUser(pubKeyHash)}

	elif args.action == 'get_balance':
		total = 0
		for account in ownedAccounts.accounts:
			total += state._balances.balanceFor(account)
		return {'balance':Amounts.ToString(total)}

	elif args.action == 'get_buy_offers':
		result = []
		for offer in state._ltcBuys.getSortedOffers():
			mine = offer.refundAccount in ownedAccounts.tradeOfferChangeCounts
			exchangeAmount = offer._swapBillOffered
			ltc = offer.ltcEquivalent()
			details = {'swapbill offered':Amounts.ToString(exchangeAmount), 'ltc equivalent':Amounts.ToString(ltc), 'mine':mine}
			result.append(('exchange rate', Amounts.PercentToString(offer.rate), details))
		return result

	elif args.action == 'get_sell_offers':
		result = []
		for offer in state._ltcSells.getSortedOffers():
			mine = offer.receivingAccount in ownedAccounts.tradeOfferChangeCounts
			ltc = offer._ltcOffered
			depositAmount = offer._swapBillDeposit
			swapBillEquivalent = offer.swapBillEquivalent()
			details = {'ltc offered':Amounts.ToString(ltc), 'deposit':Amounts.ToString(depositAmount), 'swapbill equivalent':Amounts.ToString(swapBillEquivalent), 'mine':mine}
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
			d['outstanding ltc payment amount'] = Amounts.ToString(exchange.ltc)
			d['expires on block'] = exchange.expiry
			d['blocks until expiry'] = exchange.expiry - state._currentBlockIndex + 1
			if exchange.backerIndex != -1:
				d['backer id'] = exchange.backerIndex
			result.append(('pending exchange index', key, d))
		return result

	elif args.action == 'get_ltc_sell_backers':
		result = []
		for key in state._ltcSellBackers:
			d = {}
			backer = state._ltcSellBackers[key]
			d['I am backer'] = backer.refundAccount in ownedAccounts.tradeOfferChangeCounts
			d['backing amount'] = Amounts.ToString(backer.backingAmount)
			d['maximum per transaction'] = Amounts.ToString(backer.transactionMax)
			d['expires on block'] = backer.expiry
			d['blocks until expiry'] = backer.expiry - state._currentBlockIndex + 1
			d['commission'] = Amounts.PercentToString(backer.commission)
			result.append(('ltc sell backer index', key, d))
		return result

	else:
		parser.print_help()
