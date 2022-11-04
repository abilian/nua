"""For debug, list all docker containers.
"""
from ..docker_utils import list_containers
from ..state import set_verbose


def main():
    set_verbose(2)
    print("Docker containers:")
    list_containers()


if __name__ == "__main__":
    main()
