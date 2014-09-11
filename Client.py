from __future__ import print_function
import sys
from os import path
scriptPath = path.dirname(path.abspath(__file__))
sys.path.append(path.join(scriptPath, 'module'))
sys.dont_write_bytecode = True
from SwapBill import ClientMain
from SwapBill.ExceptionReportedToUser import ExceptionReportedToUser

try:
	result = ClientMain.Main()
except ExceptionReportedToUser as e:
	print("Operation failed:", e)
else:
	print('Operation successful')
	if type(result) is dict:
		for key in result:
			print(key, ':', result[key])
	else:
		if len(result) == 0:
			print('No entries')
		for entry in result:
			print(entry[0], ':', entry[1])
			for key in entry[2]:
				print('   ', key, ':', entry[2][key])
