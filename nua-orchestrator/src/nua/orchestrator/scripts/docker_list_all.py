"""For debug, list all docker containers."""
from nua.lib.tool.state import set_verbosity

from ..docker_utils import list_containers


def main():
    set_verbosity(1)
    print("Docker containers:")
    list_containers()


if __name__ == "__main__":
    main()
