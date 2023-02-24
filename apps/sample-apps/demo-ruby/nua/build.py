from nua.agent.nua_config import NuaConfig
from nua.lib.actions import install_nodejs
from nua.lib.backports import chdir
from nua.lib.exec import exec_as_nua
from nua.lib.shell import chown_r


def main():
    config = NuaConfig()
    install_nodejs()
    src = config.fetch_source()
    chown_r(src, "nua")
    with chdir(src):
        exec_as_nua(
            [
                "cp .env.example .env",
                "bundle install",
                "bundle add tzinfo-data",
                "yarn install",
                "bundle exec rake db:setup",
            ]
        )


if __name__ == "__main__":
    main()
