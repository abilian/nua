import logging

import fire

from nua.cli.build import BuildCmd
from nua.utils import console

logging.basicConfig(level=logging.INFO)


class CLI:
    def build(self):
        console.print("Starting build")
        BuildCmd().run()


def main():
    fire.Fire(CLI)
