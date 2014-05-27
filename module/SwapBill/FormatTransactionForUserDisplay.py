def Format(host, transactionType, outputs, outputPubKeys, details):
	assert len(outputs) == len(outputPubKeys)
	result = transactionType
	for i in range(len(outputs)):
		result += ', ' + outputs[i] + ' output address='
		result += host.formatAddressForEndUser(outputPubKeys[i])
	for key in sorted(details):
		result += ', ' + key + '='
		if key.endswith('Address'):
			result += host.formatAddressForEndUser(details[key])
		else:
			result += str(details[key])
	return result
