"""For debug, print the content of the Instance table.
"""
from pprint import pformat, pprint

from .. import config
from ..db import store
from ..db_setup import setup_db


def main():
    setup_db()
    used_domain_ports = store.ports_instances_domains()
    pprint(used_domain_ports)


if __name__ == "__main__":
    main()
