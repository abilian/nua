def elapsed(delta: float) -> str:
    """Readable time string from duration in seconds.
    >>> elapsed(123.456)
    '2min 3s'
    >>> elapsed(23.456)
    '23.46s'
    """

    seconds = int(delta)
    cent = int(round((delta - seconds) * 100))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        message = f"{days}d {hours}h {minutes}min"
    elif hours > 0:
        message = f"{hours}h {minutes}min {seconds}s"
    elif minutes > 0:
        message = f"{minutes}min {seconds}s"
    else:
        message = f"{seconds}.{cent:02d}s"
    return message
