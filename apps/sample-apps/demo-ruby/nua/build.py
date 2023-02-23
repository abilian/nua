from nua.agent.nua_config import NuaConfig
from nua.lib.actions import install_nodejs
from nua.lib.backports import chdir
from nua.lib.exec import exec_as_nua
from nua.lib.shell import chown_r, sh


def main():
    config = NuaConfig()
    install_nodejs()
    src = config.fetch_source()
    print(src)
    chown_r(src, "nua")
    print("chown done")
    sh("ls -l")
    with chdir(src):
        sh("pwd")
        sh("ls -l")
        exec_as_nua("cp .env.example .env")
        exec_as_nua("bundle install")
        exec_as_nua("yarn install")
        exec_as_nua("bundle exec rake db:setup")


if __name__ == "__main__":
    main()
