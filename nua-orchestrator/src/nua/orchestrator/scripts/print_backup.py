"""For debug, print the content of the backup requirements of app instances."""
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
        conf = content["site_config"]
        if filter and filter not in conf["label_id"]:
            continue
        print(conf["label_id"], ":")
        if "backup" in conf:
            pprint(conf["backup"])
        else:
            print("<none>")
        for provider in conf.get("providers", []):
            print("    ", provider["container_name"], ":")
            if "backup" in provider:
                pprint(provider["backup"])
            else:
                print("    <none>")


if __name__ == "__main__":
    main()
