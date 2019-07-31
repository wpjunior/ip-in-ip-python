import socket

from requests.adapters import HTTPAdapter
from requests.compat import urlparse, unquote

try:
    import http.client as httplib
except ImportError:
    import httplib

try:
    from requests.packages import urllib3
except ImportError:
    import urllib3


class IPIPSocket(object):
    def __init__(self, outer_ip, inner_ip, timeout):
        self.outer_ip = outer_ip
        self.inner_ip = inner_ip

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.sock.settimeout(timeout)

    def close(self):
        pass

    def sendall(self, *args, **kwargs):
        pass

    def settimeout(self, *args, **kwargs):
        pass

    def makefile(self, *args, **kwargs):
        pass


class IPIPHTTPConnection(httplib.HTTPConnection, object):

    def __init__(self, unix_socket_url, timeout=60):
        """Create an HTTP connection to a unix domain socket
        :param unix_socket_url: A URL with a scheme of 'http+unix' and the
        netloc is a percent-encoded path to a unix domain socket. E.g.:
        'http+unix://%2Ftmp%2Fprofilesvc.sock/status/pid'
        """
        super(IPIPHTTPConnection, self).__init__('localhost', timeout=timeout)
        self.url = urlparse(unix_socket_url)
        self.outer_ip, self.inner_ip = self.url.netloc.split('+')
        self.timeout = timeout
        self.sock = None

    def __del__(self):  # base class does not have d'tor
        if self.sock:
            self.sock.close()

    def connect(self):
        self.sock = IPIPSocket(self.outer_ip, self.inner_ip, self.timeout)

class IPIPHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):

    def __init__(self, socket_path, timeout=60):
        super(IPIPHTTPConnectionPool, self).__init__(
            'localhost', timeout=timeout)

        self.socket_path = socket_path
        self.timeout = timeout

    def _new_conn(self):
        conn = IPIPHTTPConnection(self.socket_path, self.timeout)
        conn.connect()

        return conn


class IPIPAdapter(HTTPAdapter):

    def __init__(self, timeout=60, pool_connections=25):
        super(IPIPAdapter, self).__init__()
        self.timeout = timeout
        self.pools = urllib3._collections.RecentlyUsedContainer(
            pool_connections, dispose_func=lambda p: p.close()
        )

    def get_connection(self, url, proxies=None):
        proxies = proxies or {}
        proxy = proxies.get(urlparse(url.lower()).scheme)

        if proxy:
            raise ValueError('%s does not support specifying proxies'
                             % self.__class__.__name__)

        with self.pools.lock:
            pool = self.pools.get(url)
            if pool:
                return pool

            pool = IPIPHTTPConnectionPool(url, self.timeout)
            self.pools[url] = pool

        return pool

    def request_url(self, request, proxies):
        return request.path_url

    def close(self):
        self.pools.clear()
