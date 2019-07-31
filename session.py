import requests

DEFAULT_SCHEME = 'http+ipip://'

from adapters import IPIPAdapter

class Session(requests.Session):
    def __init__(self, url_scheme=DEFAULT_SCHEME, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.mount(url_scheme, IPIPAdapter())


def request(method, url, **kwargs):
    session = Session()
    return session.request(method=method, url=url, **kwargs)


if __name__ == '__main__':
    request(method='GET', url='http+ipip://8.8.8.8+9.9.9.9/blah')
