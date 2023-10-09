"""For debug, print the last deployments."""
import sys

from ..nua_db_setup import setup_nua_db
from ..state_journal import info_last_deployments


def main():
    setup_nua_db()
    if len(sys.argv) > 1:
        number = int(sys.argv[1])
    else:
        number = 10
    deployments = info_last_deployments(number)
    print("\n".join(deployments))


if __name__ == "__main__":
    main()
