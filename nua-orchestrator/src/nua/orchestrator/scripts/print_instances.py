"""For debug, print the content of the Instance table."""
from pprint import pprint

from ..db import store
from ..nua_db_setup import setup_nua_db


def main():
    setup_nua_db()
    instances = store.list_instances_all()
    for instance in instances:
        pprint(instance.to_dict())


if __name__ == "__main__":
    main()
