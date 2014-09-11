from __future__ import print_function
import sys, os
PY3 = sys.version_info.major > 2
if PY3:
	import pickle
else:
	import cPickle as pickle
from os import path

class LoadFailedException(Exception):
	pass

if PY3:
	cacheSuffix = '.py3.cache'
else:
	cacheSuffix = '.cache'

def Load(cacheDirectory, cacheName, desiredVersion):
	assert path.isdir(cacheDirectory)
	cacheFile = path.join(cacheDirectory, cacheName + cacheSuffix)
	if not path.exists(cacheFile):
		raise LoadFailedException('no cache file found')
	with open(cacheFile, mode='rb') as f:
		savedCacheVersion = pickle.load(f)
		if savedCacheVersion != desiredVersion:
			raise LoadFailedException('cached data version does not match desired version')
		return pickle.load(f)

def Save(data, dataVersion, cacheDirectory, cacheName):
	assert path.isdir(cacheDirectory)
	cacheFile = path.join(cacheDirectory, cacheName + cacheSuffix)
	try:
		with open(cacheFile, mode='wb') as f:
			pickle.dump(dataVersion, f, 2)
			pickle.dump(data, f, 2)
	except:
		print("Error, failed to write cache:", sys.exc_info()[0])

def Remove(cacheDirectory, cacheName):
	assert path.isdir(cacheDirectory)
	cacheFile = path.join(cacheDirectory, cacheName + cacheSuffix)
	os.remove(cacheFile)
