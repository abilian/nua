"""For debug, remove all sites instances.
"""
from ..db_setup import setup_db
from ..deploy_utils import deactivate_all_instances
from ..state import set_verbose


def main():
    setup_db()
    set_verbose(2)
    deactivate_all_instances()


if __name__ == "__main__":
    main()
