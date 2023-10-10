import platform
from dataclasses import dataclass
from pathlib import Path

from cleez.colors import bold

from ..constants import BOXES
from ..helpers import sh
from .base import Stage


@dataclass(frozen=True)
class PrepareStage(Stage):
    name = "prepare"

    def run(self):
        print(bold("Preparing Vagrant VM and testing environment..."))
        self.prepare_vagrant_dir()
        self.generate_vagrantfile()
        self.vagrant_up()
        print("Vagrant is up and running.")

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
        vagrantfile_tpl = Path(__file__).parent.parent / "etc" / "Vagrantfile.tpl"
        Path("Vagrantfile").write_text(
            vagrantfile_tpl.read_text().replace("##BOXNAME##", boxname)
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
