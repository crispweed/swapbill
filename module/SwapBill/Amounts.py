from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

def e(power):
	return 10**power
def ToSatoshis(value):
	assert type(value) is float
	return int(value * e(8))

def _toString(i, decimalDigits):
	s = str(i)
	l = len(s)
	if l <= decimalDigits:
		s = '0' * (decimalDigits + 1 - l) + s
	result = s[:-decimalDigits]
	after = s[-decimalDigits:]
	while after[-1:] == '0':
		after = after[:-1]
	if after:
		result = result + '.' + after
	return result
def _fromString(s, decimalDigits):
	if s[0] == '-':
		raise ExceptionReportedToUser('Bad decimal string (negative values are not permitted).')
	pos = s.find('.')
	if pos == -1:
		integerString = s + '0' * decimalDigits
	else:
		digitsAfter = len(s) - 1 - pos
		if digitsAfter > decimalDigits:
			raise ExceptionReportedToUser('Too much precision in decimal string (a maximum of {} digits are allowed after the decimal point).'.format(decimalDigits))
		digitsToAdd = decimalDigits - digitsAfter
		integerString = s[:pos] + s[pos+1:] + '0' * digitsToAdd
	return int(integerString)

def ToString(satoshis):
	return _toString(satoshis, 8)
def FromString(s):
	return _fromString(s, 8)

percentBytes = 4
percentDivisor = 1000000000
_percentDigits = 9

def PercentToString(value):
	return _toString(value, _percentDigits)
def PercentFromString(s):
	result = _fromString(s, _percentDigits)
	if result == 0 or result >= percentDivisor:
		raise ExceptionReportedToUser('Bad percentage string (value must be greater than 0.0 and less than 1.0).')
	return result

