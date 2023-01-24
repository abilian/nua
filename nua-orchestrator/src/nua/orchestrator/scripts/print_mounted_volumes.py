"""For debug, print the list of mounted local volumes (from DB)."""
from pprint import pprint

from ..db import store
from ..nua_db_setup import setup_nua_db


def main():
    setup_nua_db()
    mounted = store.list_instances_container_local_active_volumes()
    pprint(mounted)


if __name__ == "__main__":
    main()
