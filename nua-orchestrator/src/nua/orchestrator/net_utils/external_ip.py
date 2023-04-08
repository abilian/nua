from urllib.request import urlopen


def external_ip() -> str:
    """Detect the host external IPv4 address, by calling server
    icanhazip.com."""
    try:
        return (
            urlopen("https://ipv4.icanhazip.com", timeout=30)  # noqa s310
            .read()
            .strip()
            .decode("utf8")
        )
    except OSError:
        return ""
