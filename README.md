# xrequests
A lazy, minimalist, but fast HTTP request module for Python 3.4+

```python
import xrequests

session = xrequests.Session(proxy_url=None, timeout=5)

resp = session.request("GET", "https://api.ipify.org/?format=json",
                       headers={"Host": "api.ipify.org"})
print(resp.status)
print(resp.content)
```

Some quirks:
- Host headers are to be included manually
- No retry attempts will be made, unless a connection is established from another request
- All exceptions are wrapped under RequestException, even ones from third-party modules

Supports:
- HTTP, SOCKS4 and SOCKS5 proxies
- Chunked transfer encoding
- Brotli, gzip and deflate content en/decoding
- Unverified SSL

To be implemented:


# Installation
```bash
pip install -U git+https://github.com/h0nde/xrequests.git
```
