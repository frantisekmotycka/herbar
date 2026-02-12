import urllib.request
try:
    req = urllib.request.Request('https://en.wikipedia.org', headers={'User-Agent':'herbar-bot/1.0'})
    r = urllib.request.urlopen(req, timeout=10)
    print('ok', getattr(r, 'status', 'n/a'))
except Exception as e:
    print('err', type(e).__name__, e)
