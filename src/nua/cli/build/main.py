import logging
import os

import fire
import rich.console

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

console = rich.console.Console()


class CLI:
    def build(self):
        print("Starting build")


def sh(cmd):
    print(cmd)
    os.system(cmd)



def main():
    print("Hello build")

    fire.Fire(CLI)
