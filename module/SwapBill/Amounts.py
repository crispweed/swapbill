def e(power):
	return 10**power
def ToSatoshis(value):
	assert type(value) is float
	return int(value * e(8))
