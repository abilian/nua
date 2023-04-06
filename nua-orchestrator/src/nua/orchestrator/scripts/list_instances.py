"""For debug, print the list of instance names."""

from ..db import store
from ..nua_db_setup import setup_nua_db


def main():
    setup_nua_db()
    instances = store.list_instances_all()
    for instance in instances:
        print(instance.to_dict()["site_config"]["instance_name_internal"])


if __name__ == "__main__":
    main()
