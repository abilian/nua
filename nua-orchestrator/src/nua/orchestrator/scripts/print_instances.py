"""For debug, print the content of the Instance table."""
import sys
from pprint import pprint

from ..db import store
from ..nua_db_setup import setup_nua_db


def main():
    if len(sys.argv) > 1:
        filter = sys.argv[1]
    setup_nua_db()
    instances = store.list_instances_all()
    for instance in instances:
        content = instance.to_dict()
        if filter and content["site_config"]["instance_name"] != filter:
            continue
        pprint(instance.to_dict())


if __name__ == "__main__":
    main()
