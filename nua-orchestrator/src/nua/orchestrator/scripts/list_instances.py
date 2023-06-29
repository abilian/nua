"""For debug, print the list of instance."""

from ..db import store
from ..nua_db_setup import setup_nua_db


def main():
    setup_nua_db()
    instances = store.list_instances_all_short()
    print("\n".join(instances))


if __name__ == "__main__":
    main()
