#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass

from cleez.colors import bold

from .cli import Config, get_config, make_parser
from .constants import STAGES
from .stages.registry import STAGE_CLASSES


@dataclass(frozen=True)
class TestRunner:
    config: Config

    def run(self):
        stage_names = self.config.stages or STAGES

        stages = [STAGE_CLASSES[name](self.config) for name in stage_names]

        # Must be run after "prepare" stage
        # sh("vagrant rsync")

        for stage in stages:
            print(bold(f"Running stage {stage.name}..."))
            stage.run()
            print()
            print()


def main():
    parser = make_parser()
    args = parser.parse_args()
    config = get_config(args)
    config.show()

    test_runner = TestRunner(config)
    test_runner.run()
