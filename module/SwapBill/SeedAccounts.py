from SwapBill import Util

def GetSeedAccountInfo(protocol):
	infoByProtocol = {
        'bitcoin':(
	        ('22b88bd6e123d2207ebcee1d2134ecfafee4c84858eecd80bc0c2ba5bb2949f9',0),
	        100000,
	        Util.fromHex('a7e1b5ee524d075ec433a7d1329a209d723ba199'),
	        '76a914a7e1b5ee524d075ec433a7d1329a209d723ba19988ac',
	        20000000000,
	        ),
        'litecoin':(
	        ('ca85714ebe76bd64e7c2b1284e8f3ef91e2db90a1447cb278ac2900c9143debf',0),
	        100000,	        
	        Util.fromHex('391f828e816ede9281ef45b9f967b24097263503'), 
	        '76a914391f828e816ede9281ef45b9f967b2409726350388ac',
	        2000000000000,
	        ),
    }
	return infoByProtocol[protocol]
