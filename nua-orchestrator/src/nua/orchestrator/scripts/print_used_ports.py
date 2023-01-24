"""For debug, print the content of the Instance table."""
from pprint import pprint

from ..db import store
from ..nua_db_setup import setup_nua_db


def main():
    setup_nua_db()
    used_domain_ports = store.ports_instances_domains()
    pprint(used_domain_ports)


if __name__ == "__main__":
    main()
