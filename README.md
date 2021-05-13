# xrequests
A lazy, minimalist, but fast requests module for Python

```python
import xrequests

session = xrequests.Session(
 proxy_url="http://127.0.0.1:8888", ssl_verify=False)

resp = session.request("GET", "https://google.com/")
print(resp.status)
print(resp.content)
```

# Installation
```bash
pip install -U git+https://github.com/h0nde/xrequests.git
```
