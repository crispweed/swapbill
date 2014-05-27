from __future__ import print_function
import time, requests, json

class RPCFailureException(Exception):
	pass
class MethodNotFoundException(RPCFailureException):
	pass
class RPCFailureWithMessage(RPCFailureException):
	pass

class Host(object):
	def __init__(self, url):
		self._session = requests.Session()
		self._url = url
		self._headers = {'content-type': 'application/json'}
	def call(self, rpcMethod, *params):
		payload = json.dumps({"method": rpcMethod, "params": list(params), "jsonrpc": "2.0"})
		hadConnectionFailures = False
		while True:
			try:
				response = self._session.get(self._url, headers=self._headers, data=payload)
			except requests.exceptions.ConnectionError:
				hadFailedConnections = True
				print("Couldn't connect for remote procedure call, will sleep for ten seconds and then try again.")
				time.sleep(10)
			else:
				if hadConnectionFailures:
					print('Connected for remote procedure call on retry after connection failure.')
				break
		if response.status_code == -32601:
			raise MethodNotFoundException(rpcMethod)
		if not response.status_code in (200, 500):
			raise RPCFailureException('status code: ' + str(response.status_code) + ', reason: ' + response.reason)
		responseJSON = response.json()
		if 'error' in responseJSON and responseJSON['error'] != None:
			if 'message' in responseJSON['error']:
				raise RPCFailureWithMessage(responseJSON['error']['message'])
			raise RPCFailureException('error json: ' + str(responseJSON['error']))
		if response.status_code == 500:
			raise RPCFailureException('status code: ' + str(response.status_code) + ', reason: ' + response.reason)
		return responseJSON['result']
