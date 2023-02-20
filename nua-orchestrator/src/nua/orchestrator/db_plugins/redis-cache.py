"""Function to auto configure a Redis container DB.

(wip : no persistence)
"""

from ..resource import Resource

NUA_PROPERTIES = {
    "name": "redis-cache",  # plugin name
    "container": "docker",  # container type
    "family": "db",  # plugin family
    "assign": True,  # receives dynamic assignment of ENV
    "network": True,  # require docker bridge network
    "meta-packages": [],  # for app-builder infer packages (for future use)
}


def configure_db(resource: Resource):
    resource.docker = {"detach": True, "restart_policy": {"name": "always"}}
    resource.env = {"REDIS_PORT": "6379"}
    # WIP for a persistent redis:
    #  - create a docker volume
    #  - put a redis.conf in it
    #  - docker volume like redis.conf:/etc/redis/redis.conf
    #  - and change start commenad like ["redis-server", "/etc/redis/redis.conf"]
    #
    # resource.assign = [
    #     {"key": "REDIS_PASSWORD", "random": True, "persist": True},
    # ]


# def setup_db(resource: Resource):
#     """Find or create the required DB for an application user."""
#     # nothing to do here: the redis container should have created a DB at start.
