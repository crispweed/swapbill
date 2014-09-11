from __future__ import print_function
import ecdsa, hashlib, os
from SwapBill import Util

class FileBackedList(object):
	def __init__(self, fileName):
		self._fileName = fileName
		self._l = []
		if os.path.exists(fileName):
			with open(fileName, mode='r') as f:
				lines = f.readlines()
				for line in lines:
					assert line[-1:] == '\n'
					lineHex = line[:-1]
					byteBuffer = Util.fromHex(lineHex)
					self._l.append(byteBuffer)

	def append(self, byteBuffer):
		self._l.append(byteBuffer)
		with open(self._fileName, mode='a') as f:
			f.write(Util.toHex(byteBuffer))
			f.write('\n')

	def __len__(self):
		return len(self._l)
	def __getitem__(self, key):
		return self._l.__getitem__(key)
	def __iter__(self):
		#return __iter__(self._l)
		for entry in self._l:
			yield entry

