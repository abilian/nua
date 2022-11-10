"""For debug, remove all docker containers.
"""
from docker import from_env
from docker.errors import APIError, NotFound

from ..docker_utils import docker_network_prune, list_containers
from ..state import set_verbose


def stop_containers():
    client = from_env()
    print("Stopping containers:")
    for ctn in client.containers.list(all=True):
        try:
            print(f"Stopping {ctn.name}")
            ctn.stop()
        except (APIError, NotFound) as e:
            print(f"Error while stopping: {e}")


def remove_containers():
    client = from_env()
    print("Removing containers:")
    for ctn in client.containers.list(all=True):
        try:
            print(f"Remove {ctn.name}")
            ctn.remove(force=True)
        except (APIError, NotFound) as e:
            print(f"Error while stopping: {e}")


def main():
    set_verbose(2)
    print("Docker containers:")
    list_containers()
    stop_containers()
    print("Docker containers after stop:")
    list_containers()
    remove_containers()
    print("Docker containers after remove:")
    list_containers()
    print("Docker prune netwotk")
    docker_network_prune()


if __name__ == "__main__":
    main()