from .exceptions import *
from .structures import CaseInsensitiveDict
from .models import Response
from urllib.parse import urlparse
import socks
import ssl
import brotli
import gzip
import zlib

protocol_to_proxy_type = {
    "http": socks.HTTP,
    "https": socks.HTTP,
    "socks": socks.SOCKS4,
    "socks5": socks.SOCKS5,
    "socks5h": socks.SOCKS5
}

class Session:
    def __init__(self, proxy_url=None, timeout=None, chunk_size=None,
                 decode_content=None, encode_content=None, ssl_verify=None):
        timeout = timeout if timeout is not None else 5
        chunk_size = chunk_size if chunk_size is not None else (1024 ** 2)
        decode_content = decode_content if decode_content is not None else True
        encode_content = encode_content if encode_content is not None else True
        ssl_verify = ssl_verify if ssl_verify is not None else True

        self.timeout = timeout
        self.proxy_url = proxy_url
        self.addr_to_conn = {}
        self.max_chunk_size = chunk_size
        self.decode_content = decode_content
        self.encode_content = encode_content
        self.ssl_verify = ssl_verify


    def _create_socket(self, dest_addr, timeout=None, ssl_wrap=True,
                           ssl_verify=True):
        sock = socks.socksocket()

        if timeout or self.timeout:
            sock.settimeout(timeout or self.timeout)
        
        if self.proxy_url is not None:
            proxy_url = urlparse(self.proxy_url)
            proxy_type = protocol_to_proxy_type.get(proxy_url.scheme.lower())

            if proxy_type is None:
                raise Exception("'%s' is not a supported proxy scheme" % (
                    proxy_url.scheme))

            sock.set_proxy(
                proxy_type,
                addr=proxy_url.hostname,
                port=proxy_url.port,
                username=proxy_url.username,
                password=proxy_url.password,
                rdns=False
            )

        sock.connect(dest_addr)

        if ssl_wrap:
            if ssl_verify:
                context = ssl.create_default_context()
            else:
                context = ssl._create_unverified_context()

            sock = context.wrap_socket(
                sock,
                server_side=False,
                server_hostname=dest_addr[0]
            )

        return sock


    def _encode_content(self, content, encoding):
        encoding = encoding.lower()

        if encoding == "br":
            content = brotli.compress(content)
        elif encoding == "gzip":
            content = gzip.compress(content)
        elif encoding == "deflate":
            content = zlib.compress(content)
        
        return content

    def _decode_content(self, content, encoding):
        encoding = encoding.lower()

        if encoding == "br":
            content = brotli.decompress(content)
        elif encoding == "gzip":
            content = gzip.decompress(content)
        elif encoding == "deflate":
            content = zlib.decompress(content)
        
        return content


    def _prepare_request(self, version, method, path, headers, content):
        request = "%s %s HTTP/%s\r\n" % (
            method, path, version)

        for header, value in headers.items():
            request += "%s: %s\r\n" % (header, value)

        request += "\r\n"
        request = request.encode("UTF-8")

        if content:
            if "content-encoding" in headers and self.encode_content:
                content = self._encode_content(content, headers["content-encoding"])
            request += content

        return request


    def _send(self, conn, data):
        conn.send(data)

    
    def _get_response(self, conn):
        resp = conn.recv(self.max_chunk_size)

        if len(resp) <= 10:
            raise RequestException("Invalid response", resp)

        resp, data = resp.split(b"\r\n\r\n", 1)
        resp = resp.decode()
        status, raw_headers = resp.split("\r\n", 1)
        _, status, message = status.split(" ", 2)

        headers = CaseInsensitiveDict()
        for header in raw_headers.splitlines():
            header, value = header.split(":", 1)
            if value.startswith(" "):
                value = value[1:]
            headers[header] = value
        del raw_headers
        
        if headers.get("transfer-encoding") == "chunked":
            while True:
                chunk = conn.recv(self.max_chunk_size)
                if chunk == b"" or chunk == b"0\r\n\r\n":
                    break
                data += chunk

            raw = data
            data = b""

            while raw:
                length, raw = raw.split(b"\r\n", 1)
                length = int(length, 16)
                chunk, raw = raw[:length], raw[length+2:]
                data += chunk
                
        else:
            goal = int(headers["content-length"])
            while goal > len(data):
                chunk = conn.recv(min(goal-len(data), self.max_chunk_size))
                if len(chunk) == 0:
                    raise RequestException("Malformed chunk")
                data += chunk

        if "content-encoding" in headers and self.decode_content:
            data = self._decode_content(data, headers["content-encoding"])

        return int(status), message, headers, data
    

    def request(self, method, url, headers=None, content=None):
        parsed_url = urlparse(url)
        ssl_enabled = "https" == parsed_url.scheme
        addr = (
            parsed_url.hostname.lower(),
            parsed_url.port or {"s":443,"":80}.get(parsed_url.scheme[4:])
        )
        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)

        request = self._prepare_request(
            version="1.1",
            method=method,
            path=parsed_url.path \
                + ("?" + parsed_url.query if parsed_url.query else ""),
            headers=headers,
            content=content
        )
        
        conn_reused = addr in self.addr_to_conn

        while True:
            try:
                if addr in self.addr_to_conn:
                    conn = self.addr_to_conn[addr]
                else:
                    conn = self._create_socket(
                        addr,
                        ssl_wrap=ssl_enabled,
                        ssl_verify=self.ssl_verify)
                    self.addr_to_conn[addr] = conn
                
                self._send(conn, request)
                return Response(*self._get_response(conn))

            except Exception as err:
                if addr in self.addr_to_conn:
                    self.addr_to_conn.pop(addr)
                if not conn_reused:
                    if not isinstance(err, RequestException):
                        err = RequestException(err)
                    raise
                conn_reused = False
