class InMemoryTransaction(object):
	def __init__(self):
		self._inputs = []
		self._outputs = []
	# construction
	def addInput(self, txID, vOut):
		self._inputs.append((txID, vOut))
	def addOutput(self, pubKeyHash, amount):
		assert type(amount) is int
		assert amount >= 0
		self._outputs.append((pubKeyHash, amount))
	# helper
	def sumOfOutputs(self):
		result = 0
		for pkh, amount in self._outputs:
			result += amount
		return result
	# actual transaction interface
	def numberOfInputs(self):
		return len(self._inputs)
	def inputTXID(self, i):
		return self._inputs[i][0]
	def inputVOut(self, i):
		return self._inputs[i][1]
	def numberOfOutputs(self):
		return len(self._outputs)
	def outputPubKeyHash(self, i):
		return self._outputs[i][0]
	def outputAmount(self, i):
		return self._outputs[i][1]

def AsData(tx):
	inputs = []
	for i in range(tx.numberOfInputs()):
		inputs.append((tx.inputTXID(i), tx.inputVOut(i)))
	outputs = []
	for i in range(tx.numberOfOutputs()):
		outputs.append((tx.outputPubKeyHash(i), tx.outputAmount(i)))
	return (inputs, outputs)

def FromData(data):
	result = InMemoryTransaction()
	result._inputs, result._outputs = data
	return result
