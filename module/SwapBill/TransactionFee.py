
# to simplify fee calculations, all outputs should be greater than or equal to dustLimit
dustLimit = 100000

# and then transaction fee requirements depend purely on byte size
sizeStep = 1000
feeStep = 100000
startingMaximumSize = sizeStep - 1
startingFee = feeStep

def CalculateRequired_FromSizeAndOutputs(byteSize, outputAmounts):
	multiplier = (1 + int(byteSize / sizeStep))
	for amount in outputAmounts:
		assert amount >= dustLimit
		#if amount < 100000: ## soft dust limit
			#multiplier += 1
	return multiplier * feeStep


