from __future__ import print_function
from SwapBill import HostTransaction
from SwapBill.ChooseInputs import ChooseInputs
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
	if baseInputAmount + sum(unspentAmounts) < totalRequired:
		raise InsufficientFunds('Not enough funds available for the transaction, total required:', totalRequired, 'transaction fee:', transactionFee, 'sum of unspent:', sum(unspentAmounts))

	if baseInputAmount < totalRequired:
		outputAssignments, outputsTotal = ChooseInputs(maxInputs=len(unspentAmounts), unspentAmounts=unspentAmounts, amountRequired=totalRequired - baseInputAmount)
		for i in outputAssignments:
			filledOutTX.addInput(unspentAsInputs[i][0], unspentAsInputs[i][1])
	else:
		outputsTotal = 0

	if baseInputAmount + outputsTotal > totalRequired:
		overSupply = baseInputAmount + outputsTotal - totalRequired
		if overSupply >= dustLimit:
			filledOutTX.addOutput(changePubKeyHash, overSupply)

	return filledOutTX
