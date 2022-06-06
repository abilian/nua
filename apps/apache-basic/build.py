from shutil import copytree

from nua_build.scripting import *


def main():
    print("apache2-basic build script")
    packages = ["apache2"]
    install_package_list(packages)

    rm_fr("/var/www/html")
    copytree("/nua/build/html", "/var/www/html")


main()
