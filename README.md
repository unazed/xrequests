# xrequests
A lazy, minimalist, but fast requests module for Python

```python
import xrequests

session = xrequests.Session(proxy_url=None)

resp = session.request("GET", "https://google.com/")
print(resp.status)
print(resp.content)
```

# Installation
```bash
pip install -U git+https://github.com/h0nde/xrequests.git
```
