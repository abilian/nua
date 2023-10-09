"""For debug, reset Nua's nginx configuration."""
from nua.lib.tool.state import set_verbosity

from ..nginx.commands import nginx_restart, nginx_stop
from ..nginx.render_default import clean_nua_nginx_default_site


def main():
    set_verbosity(1)
    nginx_stop(allow_fail=True)
    clean_nua_nginx_default_site()
    nginx_restart(allow_fail=True)


if __name__ == "__main__":
    main()
