"""Class DomainSplit to parse a doman string in valid parts.
"""

from urllib.parse import urlparse

from nua.lib.common.panic import error


class DomainSplit:
    """Split a domain string into domain and location (path) parts."""

    def __init__(self, url_string: str):
        url_string = url_string.strip("/")
        result = urlparse(url_string)
        # we expect a domain/location without protocol, so just add it:
        if not result.scheme:
            result = urlparse(f"http://{url_string}")
        self.hostname = result.hostname
        if not self.hostname:
            error(f"Fail to parse hostname from: '{url_string}'")
        self.location = result.path.strip("/")

    def full_path(self):
        if self.location:
            return f"{self.hostname}/{self.location}"
        else:
            return self.hostname

    def containner_suffix(self):
        if self.location:
            return f"{self.hostname}-{self.location}"
        else:
            return self.hostname
