#!/usr/bin/env python3

from __future__ import annotations

import argparse
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import toml
from cleez.colors import bold, dim, green, red

BOXES = {
    "x86_64": "generic/ubuntu2204",
    "arm": "perk/ubuntu-2204-arm64",
}
STAGES = ["prepare", "install", "build", "deploy"]


@dataclass(frozen=True)
class TestRunner:
    config: Config

    def run(self):
        stages = self.config.stages or STAGES
        if "prepare" in stages:
            self.run_prepare()

        # Last chance to rsync
        sh("vagrant rsync")

        if "install" in stages:
            self.run_install()

        if "build" in stages:
            self.run_build()

        if "deploy" in stages:
            self.run_deploy()

    def run_prepare(self):
        print(bold("Preparing Vagrant VM and testing environment..."))
        self.prepare_vagrant_dir()
        self.generate_vagrantfile()
        self.vagrant_up()
        print()

    def run_install(self):
        print(bold("Installing Nua..."))
        self.install_nua()
        print()

        # Last chance to rsync
        sh("vagrant rsync")

    def run_build(self):
        print(bold("Building apps..."))
        build_results = self.build_apps()
        print()

        self.report_build_results(build_results)

    def run_deploy(self):
        print(bold("Deploying apps..."))
        self.deploy_apps()

    def prepare_vagrant_dir(self):
        sh("rm -rf apps")
        sh("mkdir apps")
        if self.config.apps_dir:
            apps_dir = Path(self.config.apps_dir)
        else:
            apps_dir = Path("../../apps/real-apps")

        sh(f"cp -r {apps_dir}/* apps/")
        sh("cp ../../installer/install.py .")
        for file in Path("apps").iterdir():
            if file.is_file():
                file.unlink()

    def generate_vagrantfile(self):
        proc = platform.processor()
        boxname = BOXES[proc]
        Path("Vagrantfile").write_text(
            Path("Vagrantfile.tpl").read_text().replace("##BOXNAME##", boxname)
        )

    def vagrant_up(self):
        if "running" in sh("vagrant status", capture=True).stdout:
            print("Vagrant is already running")
            return

        if platform.system() == "Darwin":
            sh("vagrant up --provider qemu")
        else:
            sh("vagrant up")

        ssh_config = sh("vagrant ssh-config", capture=True).stdout
        Path("ssh-config").write_text(ssh_config)

    def install_nua(self):
        # ssh("curl -L https://nua.rocks/install.py | sudo python3")
        ssh("sudo python3 /vagrant/install.py")
        ssh("sudo cp -r .ssh /home/nua/")
        ssh("sudo chown -R nua.nua /home/nua/.ssh")

    def build_apps(self) -> list[BuildResult]:
        v_flag = "-" + self.config.verbosity * "v"
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

    def deploy_apps(self):
        i = 0
        for app_dir in Path("apps").iterdir():
            i += 1
            config_file = app_dir / "nua-config.toml"
            if not config_file.exists():
                config_file = app_dir / "nua" / "nua-config.toml"
            app_id = toml.load(config_file)["metadata"]["id"]
            domain = f"test{i}.tests.nua.rocks"
            ssh(f"python3 /vagrant/deploy-app.py {app_id} {domain}", user="nua")


@dataclass(frozen=True)
class BuildResult:
    app_name: str
    success: bool
    output: str


#
# Helpers
#
def sh(cmd: str, cwd: str = "", capture=False, **kw) -> subprocess.CompletedProcess:
    """Run a shell command."""
    if not cwd:
        print(dim(f'Running "{cmd}" locally...'))
    else:
        print(dim(f'Running "{cmd}" locally in "{cwd}"...'))
    # args = shlex.split(cmd)
    opts = {
        "capture_output": capture,
        "text": True,
        "shell": True,
    }
    opts.update(kw)
    if cwd:
        opts["cwd"] = cwd
    # args_str = shlex.join(args)
    # assert args_str == cmd, (args_str, cmd)
    return subprocess.run(cmd, **opts)


def ssh(cmd: str, user="vagrant", check=True) -> subprocess.CompletedProcess:
    """Run a ssh command."""
    if user == "vagrant":
        print(dim(f'Running "{cmd}" on vagrant...'))
    else:
        print(dim(f'Running "{cmd}" on vagrant as "{user}"...'))

    # args = shlex.split(cmd)
    cmd = ["ssh", "-F", "ssh-config", f"{user}@default", cmd]  # type: ignore
    return subprocess.run(cmd, check=check)


#
# Args parsing & Config
#
def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbosity", default=0, action="count", help="Increase output verbosity"
    )
    parser.add_argument(
        "-a", "--apps-dir", default="", help="Directory containing the apps to test"
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


def get_config(args):
    return Config.from_args(args)


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    config = get_config(args)
    test_runner = TestRunner(config)
    test_runner.run()
