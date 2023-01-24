"""Function to auto configure a Postgres container DB.
"""
from ..resource import Resource
from ..volume import Volume


def configure(resource: Resource):
    # resource.image was set earlier at detect requirement stage
    # create volume:
    resource.volume = [_make_volume(resource)]
    # other options
    resource.run_env["detach"] = True
    resource.run_env["restart_policy"] = {}
    resource.run_env["restart_policy"]["name"] = "always"
    # assign keys in (env) for create or retrieve persistent values
    # Note: POSTGRES_DB could be same as POSTGRES_USER, but prefer to assign both
    # to let the using app retrieving the both values if needed.
    resource.assign = [
        {"key": "POSTGRES_PASSWORD", "random_str": True, "persist": True},
        {"key": "POSTGRES_USER", "unique_user": True, "persist": True},
        {"key": "POSTGRES_DB", "unique_db": True, "persist": True},
    ]


def _make_volume(resource: Resource) -> dict:
    volume = Volume()
    volume.type = "volume"
    volume.driver = "local"
    # at this stage, network_name is defined
    volume.source = f"{resource.resource_name}_{resource.network_name}"
    # target of Postgres images default configuration
    volume.target = "/var/lib/postgresql/data"
    return volume.as_dict()
