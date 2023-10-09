"""For debug, print the content of the Instance table."""
import sys
from pprint import pprint

from nua.lib.docker import docker_sanitized_name

from ..db import store
from ..nua_db_setup import setup_nua_db


def main():
    if len(sys.argv) > 1:
        filter = sys.argv[1]
    else:
        filter = None
    if filter:
        filter = docker_sanitized_name(filter)
    setup_nua_db()
    instances = store.list_instances_all()
    for instance in instances:
        content = instance.to_dict()
        if filter and filter not in content["site_config"]["label_id"]:
            continue
        pprint(content)


if __name__ == "__main__":
    main()
