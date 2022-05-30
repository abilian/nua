import logging

import fire

from nua.utils import panic

logging.basicConfig(level=logging.INFO)


class CLI:
    def start(self):
        panic("Not implemented")

    def stop(self):
        panic("Not implemented")


def main():
    fire.Fire(CLI)
