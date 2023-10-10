from cleez.colors import bold

from ..helpers import sh, ssh
from .base import Stage


class InstallStage(Stage):
    name = "install"

    def run(self):
        print(bold("Installing Nua..."))
        self.install_nua()
        print()

        # Last chance to rsync
        sh("vagrant rsync")

    def install_nua(self):
        # ssh("curl -L https://nua.rocks/install.py | sudo python3")
        ssh("sudo python3 /vagrant/install.py")
        ssh("sudo cp -r .ssh /home/nua/")
        ssh("sudo chown -R nua.nua /home/nua/.ssh")
