"""For debug, remove all sites instances."""
from nua.lib.tool.state import set_verbosity

from ..db_setup import setup_db
from ..deploy_utils import deactivate_all_instances


def main():
    setup_db()
    set_verbosity(2)
    deactivate_all_instances()


if __name__ == "__main__":
    main()
