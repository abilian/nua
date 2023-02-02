"""Function to auto configure a Redis container DB.

(wip : no persistence)
"""

from ..resource import Resource

# from ..volume import Volume

NUA_PROPERTIES = {
    "name": "redis",  # plugin name
    "container": "docker",  # container type
    "family": "db",  # plugin family
    "assign": True,  # use the "assign" keyword"
    "network": True,  # require docker bridge network
    "meta-packages": [],  # for app-builder infer packages (for future use)
}


def configure_db(resource: Resource):
    # resource.image was set earlier at detect requirement stage
    # create volume:
    # resource.volume = [_make_volume(resource)]
    # other options
    # docker params:
    resource.docker = {"detach": True, "restart_policy": {"name": "always"}}
    # env
    resource.env = {"REDIS_PORT": "6379"}
    # assign keys in (env) for create or retrieve persistent values
    #
    # WIP:
    #  - create a docker volume
    #  - put a redis.conf in it
    #  - docker volume like redis.conf:/etc/redis/redis.conf
    #  - and change start commenad like ["redis-server", "/etc/redis/redis.conf"]
    #
    # resource.assign = [
    #     {"key": "REDIS_PASSWORD", "random_str": True, "persist": True},
    # ]
    resource.assign_priority = 0


#
# def _make_volume(resource: Resource) -> dict:
#     volume = Volume()
#     volume.type = "volume"
#     volume.driver = "local"
#     # at this stage, network_name is defined
#     volume.source = f"{resource.resource_name}_{resource.network_name}"
#     # target of Postgres images default configuration
#     volume.target = "/var/lib/postgresql/data"
#     return volume.as_dict()


# def setup_db(resource: Resource):
#     """Find or create the required DB for an application user."""
#     # nothing to do here: the redis container should have created a DB at start.
