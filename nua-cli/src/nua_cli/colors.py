from termcolor import colored


# Color helpers
def blue(text):
    return colored(text, "blue")


def green(text):
    return colored(text, "green")


def red(text):
    return colored(text, "red")


def yellow(text):
    return colored(text, "yellow")


def bold(text):
    return colored(text, attrs=["bold"])


def dim(text):
    return colored(text, attrs=["dark"])
