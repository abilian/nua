#!/usr/bin/env python3

from __future__ import annotations

import argparse
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

import toml
from cleez.colors import bold, dim, green, red

BOXES = {
    "x86_64": "generic/ubuntu2204",
    "arm": "perk/ubuntu-2204-arm64",
}
STAGES = ["prepare", "install", "build", "deploy"]


def main(stages: list[str], verbosity: int = 1):
    v_flag = verbosity * "-v"

    if "prepare" in stages:
        print(bold("Preparing Vagrant VM and testing environment..."))
        prepare_vagrant_dir()
        generate_vagrantfile()
        vagrant_up()
        print()

    # Last chance to rsync
    sh("vagrant rsync")

    if "install" in stages:
        print(bold("Installing Nua..."))
        install_nua()
        print()

    if "build" in stages:
        print(bold("Building apps..."))
        build_results = build_apps(v_flag)
        print()

        report_build_results(build_results)

    if "deploy" in stages:
        print(bold("Deploying apps..."))
        deploy_apps(v_flag)

    # TODO: deploy apps
    # succesful_results = [r for r in build_results if r.success]
    # for i, result in enumerate(succesful_results):
    #     app_id = result.app_name
    #     domain = f"test{i}.example.com"
    #     result = ssh(f"/vagrant/deploy-app.py {app_id} {domain}", user="nua")
    # deploy_results = deploy_apps(v_flag, succesful_results)


def prepare_vagrant_dir():
    sh("mkdir -p apps")
    sh("cp -r ../../apps/real-apps/* apps/")
    sh("cp ../../installer/install.py .")
    for file in Path("apps").iterdir():
        if file.is_file():
            file.unlink()


def generate_vagrantfile():
    proc = platform.processor()
    boxname = BOXES[proc]
    Path("Vagrantfile").write_text(
        Path("Vagrantfile.tpl").read_text().replace("##BOXNAME##", boxname)
    )


def vagrant_up():
    if "running" in sh("vagrant status", capture=True).stdout:
        print("Vagrant is already running")
        return

    if platform.system() == "Darwin":
        sh("vagrant up --provider qemu")
    else:
        sh("vagrant up")

    ssh_config = sh("vagrant ssh-config", capture=True).stdout
    Path("ssh-config").write_text(ssh_config)


def install_nua():
    # ssh("curl -L https://nua.rocks/install.py | sudo python3")
    ssh("sudo python3 /vagrant/install.py")
    ssh("sudo cp -r .ssh /home/nua/")
    ssh("sudo chown -R nua.nua /home/nua/.ssh")


def build_apps(v_flag) -> list[BuildResult]:
    results = []
    for app_dir in Path("apps").iterdir():
        app_name = app_dir.name
        completed_process = ssh(
            f"cd /vagrant/apps/{app_name} "
            "&& . /home/nua/env/bin/activate "
            f"&& /home/nua/env/bin/nua-build {v_flag}",
            user="nua",
        )
        status = completed_process.returncode == 0
        result = BuildResult(app_name, status, completed_process.stdout)
        results.append(result)
    return results


def report_build_results(build_results):
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


def deploy_apps(v_flag):
    i = 0
    for app_dir in Path("apps").iterdir():
        i += 1
        config_file = app_dir / "nua-config.toml"
        if not config_file.exists():
            config_file = app_dir / "nua" / "nua-config.toml"
        app_id = toml.load(config_file)["metadata"]["id"]
        domain = f"test{i}.tests.nua.rocks"
        result = ssh(f"python3 /vagrant/deploy-app.py {app_id} {domain}", user="nua")

    # succesful_results = [r for r in build_results if r.success]
    # for i, result in enumerate(succesful_results):
    #     app_id = result.app_name


# @dataclass(frozen=True)
# class Builder:
#     app_name: str
#
#     def build(self):
#        completed_process = ssh(
#             f"cd /vagrant/apps/{self.app_name} "
#             "&& . /home/nua/env/bin/activate "
#             f"&& /home/nua/env/bin/nua-build {v_flag}",
#             user="nua",
#         )
#         result = BuildResult(app_name, True, "")
#         pass


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


def ssh(cmd: str, user="vagrant") -> subprocess.CompletedProcess:
    """Run a ssh command."""
    if user == "vagrant":
        print(dim(f'Running "{cmd}" on vagrant...'))
    else:
        print(dim(f'Running "{cmd}" on vagrant as "{user}"...'))

    # args = shlex.split(cmd)
    cmd = ["ssh", "-F", "ssh-config", f"{user}@default", cmd]  # type: ignore
    return subprocess.run(cmd, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbosity", action="count", help="Increase output verbosity"
    )
    parser.add_argument(
        "stages",
        help=f"Stages to run ({', '.join(STAGES)}). Default: all stages",
    )
    args = parser.parse_args()
    stages = args.stages or STAGES
    verbosity = args.verbosity or 0

    main(stages, verbosity=verbosity)
