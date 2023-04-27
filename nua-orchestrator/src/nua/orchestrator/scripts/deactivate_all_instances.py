"""For debug, remove all apps instances."""
from nua.lib.tool.state import set_verbosity

from ..deploy_utils import deactivate_all_instances
from ..nua_db_setup import setup_nua_db


def main():
    setup_nua_db()
    set_verbosity(1)
    deactivate_all_instances()


if __name__ == "__main__":
    main()
