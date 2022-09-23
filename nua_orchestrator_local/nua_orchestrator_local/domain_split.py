"""Class DomainSplit to parse a doman string in valid parts.
"""

from urllib.parse import urlparse

from .panic import error


class DomainSplit:
    """Split a domain string into domain and prefix (path) parts."""

    def __init__(self, url_string: str):
        url_string = url_string.strip("/")
        result = urlparse(url_string)
        # we expect a domain/prefix without protocol, so just add it:
        if not result.scheme:
            result = urlparse(f"http://{url_string}")
        self.hostname = result.hostname
        if not self.hostname:
            error(f"Fail to parse hostname from: '{url_string}'")
        self.prefix = result.path.strip("/")

    def full_path(self):
        if self.prefix:
            return f"{self.hostname}/{self.prefix}"
        else:
            return self.hostname

    def containner_suffix(self):
        if self.prefix:
            return f"{self.hostname}-{self.prefix}"
        else:
            return self.hostname
