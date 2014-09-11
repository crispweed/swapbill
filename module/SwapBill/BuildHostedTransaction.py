from __future__ import print_function
from SwapBill import HostTransaction
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

class InsufficientFunds(ExceptionReportedToUser):
	pass

def AddPaymentFeesAndChange(baseTX, baseInputAmount, dustLimit, transactionFee, unspent, changePubKeyHash):
	unspentAmounts, unspentAsInputs = unspent

	filledOutTX = HostTransaction.InMemoryTransaction()

	for i in range(baseTX.numberOfOutputs()):
		amount = baseTX.outputAmount(i)
		if amount < dustLimit:
			amount = dustLimit
		filledOutTX.addOutput(baseTX.outputPubKeyHash(i), amount)

	for i in range(baseTX.numberOfInputs()):
		txID = baseTX.inputTXID(i)
		vOut = baseTX.inputVOut(i)
		filledOutTX.addInput(txID, vOut)

	totalRequired = filledOutTX.sumOfOutputs() + transactionFee
	
	inputsSum = baseInputAmount
	i = 0
	while inputsSum < totalRequired :
		if i == len(unspentAsInputs):
			raise InsufficientFunds('Not enough funds available for the transaction, total required:', totalRequired, 'transaction fee:', transactionFee, 'sum of unspent:', sum(unspentAmounts))			
		filledOutTX.addInput(unspentAsInputs[i][0], unspentAsInputs[i][1])
		inputsSum += unspentAmounts[i]
		i += 1
	
	if inputsSum > totalRequired:
		overSupply = inputsSum - totalRequired
		if overSupply >= dustLimit:
			filledOutTX.addOutput(changePubKeyHash, overSupply)

	return filledOutTX
