"""For debug, list all docker containers.
"""
from nua.lib.tool.state import set_verbose

from ..docker_utils import list_containers


def main():
    set_verbose(2)
    print("Docker containers:")
    list_containers()


if __name__ == "__main__":
    main()
