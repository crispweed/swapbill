from __future__ import print_function
import os
from os import path
from SwapBill import ParseConfig, Host, RPC

def HostFromPrefsByProtocol(protocol, dataDir):
	assert protocol in ('bitcoin', 'litecoin')

	if os.name == 'nt':
		configFile = path.join(path.expanduser("~"), 'AppData', 'Roaming', protocol, protocol + '.conf')
	else:
		configFile = path.join(path.expanduser("~"), '.' + protocol, protocol + '.conf')

	with open(configFile, mode='rb') as f:
		configFileBuffer = f.read()
	config = ParseConfig.Parse(configFileBuffer)

	assert config['testnet'] == '1'
	useTestNet = True

# bitcoin addressVersion = 0
# bitcoin testnet addressVersion = 0x6f
# bitcoin private key address version = 0x80
# bitcoin testnet private key address version = 0xef
# litecoin addressVersion = 0x30
# litecoin testnet addressVersion = 0x6f
# litecoin private key address version = 0xbf
# litecoin testnet private key address version = 0xef

	if useTestNet:
		addressVersion = b'\x6f'
		privateKeyAddressVersion = b'\xef'
	elif protocol == 'bitcoin':
		addressVersion = b'\x00'
		privateKeyAddressVersion = b'\x80'
	else:
		assert protocol == 'litecoin'
		addressVersion = b'\x30'
		privateKeyAddressVersion = b'\xbf'

	externalIP = config.get('externalip', 'localhost')
	
	try:
		rpcPort = int(config['rpcport'])
	except KeyError:
		rpcPort = {'bitcoin':8332, 'litecoin':9332}[protocol]
		if useTestNet:
			rpcPort += 10000
	assert rpcPort > 1 and rpcPort < 65535

	try:
		rpcUser = config['rpcuser']
		rpcPassword = config['rpcpassword']
	except KeyError:
		raise ExceptionReportedToUser('Values must be set for both rpcuser and rpcpassword in your ' + protocol + ' config file.')

	rpcHost = RPC.Host('http://' + rpcUser + ':' + rpcPassword + '@' + externalIP + ':' + str(rpcPort))
	submittedTransactionsLogFileName = path.join(dataDir, 'submittedTransactions_' + protocol + '.txt')
	host = Host.Host(rpcHost=rpcHost, addressVersion=addressVersion, privateKeyAddressVersion=privateKeyAddressVersion, submittedTransactionsLogFileName=submittedTransactionsLogFileName)

	return host
