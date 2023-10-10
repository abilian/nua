import argparse
from dataclasses import dataclass, field

from .constants import STAGES


#
# Args parsing & Config
#
def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbosity",
        default=0,
        action="count",
        help="Increase output verbosity",
    )
    parser.add_argument(
        "-a",
        "--apps-dir",
        default="",
        help="Directory containing the apps to test",
    )
    parser.add_argument(
        "stages",
        nargs="*",
        default=STAGES,
        help=f"Stages to run ({', '.join(STAGES)}). Default: all stages",
    )
    return parser


@dataclass(frozen=True)
class Config:
    verbosity: int = 0
    stages: list[str] = field(default_factory=list)
    apps_dir: str = ""

    @classmethod
    def from_args(cls, args):
        return cls(**vars(args))

    def show(self):
        print("Config:")
        print(f"verbosity: {self.verbosity}")
        print(f"stages: {self.stages}")
        print(f"apps_dir: {self.apps_dir}")
        print()


def get_config(args):
    return Config.from_args(args)
