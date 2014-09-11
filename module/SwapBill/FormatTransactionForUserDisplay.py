from SwapBill import Address

def Format(host, transactionType, outputs, outputPubKeys, details):
	assert len(outputs) == len(outputPubKeys)
	result = transactionType
	for address, pubKey in zip(outputs, outputPubKeys):
		result += ', ' + address + ' output address='
		result += Address.FromPubKeyHash(host.getAddressVersion(), pubKey)
	for key in sorted(details):
		result += ', ' + key + '='
		if key.endswith('Address'):
			result += Address.FromPubKeyHash(host.getAddressVersion(), details[key])
		else:
			result += str(details[key])
	return result
