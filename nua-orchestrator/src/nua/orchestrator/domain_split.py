"""Class DomainSplit to parse a doman string in valid parts."""

from urllib.parse import urlparse

from nua.lib.panic import Abort


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
            raise Abort(f"Failed to parse hostname from: '{url_string}'")

        self.location = result.path.strip("/")

    def full_path(self) -> str:
        if self.location:
            return f"{self.hostname}/{self.location}"
        else:
            return self.hostname

    def top_domain(self) -> str:
        return ".".join(self.hostname.split(".")[-2:])

    def container_suffix(self) -> str:
        if self.location:
            return f"{self.hostname}-{self.location}"
        else:
            return self.hostname
