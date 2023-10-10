from dataclasses import dataclass
from pathlib import Path

from cleez.colors import bold, green, red

from ..helpers import ssh
from .base import Stage


@dataclass(frozen=True)
class BuildResult:
    app_name: str
    success: bool
    output: str


class BuildStage(Stage):
    name = "build"

    def run(self):
        print("Building apps...")
        build_results = self.build_apps()
        print()

        self.report_build_results(build_results)

    def build_apps(self) -> list[BuildResult]:
        if self.config.verbosity:
            v_flag = "-" + self.config.verbosity * "v"
        else:
            v_flag = ""
        results = []
        for app_dir in Path("apps").iterdir():
            app_name = app_dir.name
            completed_process = ssh(
                f"cd /vagrant/apps/{app_name} "
                "&& . /home/nua/env/bin/activate "
                f"&& /home/nua/env/bin/nua-build {v_flag} .",
                user="nua",
            )
            status = completed_process.returncode == 0
            result = BuildResult(app_name, status, completed_process.stdout)
            results.append(result)
        return results

    def report_build_results(self, build_results):
        print(bold("Build results:"))
        for r in build_results:
            if r.success:
                print(f"{r.app_name}: {green('OK')}")
            else:
                print(f"{r.app_name}: {red('KO')}")
        print()
        failed_results = [r for r in build_results if not r.success]
        if failed_results:
            print(bold(red("Failure details:")))
            for r in failed_results:
                print(f"{r.app_name}:")
                print(r.output)
                print()
