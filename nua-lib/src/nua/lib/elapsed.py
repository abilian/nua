def elapsed(delta: float) -> str:
    """Readable time string from duration in seconds."""
    seconds = int(delta)
    cent = int(round((delta - seconds) * 100))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        message = f"{days}d {hours}h {minutes}min {seconds}s"
    elif hours > 0:
        message = f"{hours}h {minutes}min {seconds}s"
    elif minutes > 0:
        message = f"{minutes}min {seconds}s"
    else:
        message = f"{seconds}.{cent:02d}s"
    return message
