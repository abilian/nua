"""Script to build a nua package (experimental)

- information come from a mandatory local file: "nua-config" (.toml, .json, .yaml)
- origin may be a source tar.gz or a git repository or a docker image...
- build locally or wrap docker image

Note: **currently use "nua-build ..." for command line**.
See later if move this to "nua ...".
"""
import argparse
import sys
import time
import traceback

import snoop
from cleez.actions import VERSION

from nua.lib.panic import Abort
from nua.lib.tool.state import set_color, set_verbosity
from nua.agent.nua_config import NuaConfigError

from . import __version__
from .builders import BuilderError, get_builder

snoop.install()


def main():
    t0 = time.time()

    parser = argparse.ArgumentParser()

    # Generic / classic options
    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action="count",
        help="Show more informations, until -vvv.",
    )
    parser.add_argument(
        "--color",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Enable (default) / disable colorized messages.",
    )
    parser.add_argument(
        "--version",
        "-V",
        action=VERSION,
        version=f"nua-build version: {__version__}",
        help="Show nua-build version and exit.",
    )

    # Specific options / arguments
    parser.add_argument(
        "config_file", help="Path to the package dir or 'nua-config' file."
    )
    parser.add_argument("-t", "--time", action="store_true", help="Print timing info")
    parser.add_argument(
        "-s",
        "--save",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Save image locally after the build (defaults to True).",
    )

    args = parser.parse_args(sys.argv[1:])

    set_verbosity(args.verbose)
    set_color(args.color)

    opts = {
        "save_image": args.save,
    }

    try:
        builder = get_builder(args.config_file or ".", **opts)
    except NuaConfigError as e:
        # FIXME: not for production
        traceback.print_exc(file=sys.stderr)
        raise Abort(e.args[0])

    try:
        builder.run()
    except BuilderError as e:
        # FIXME: not for production
        traceback.print_exc(file=sys.stderr)
        raise Abort from e

    if args.time or args.verbose >= 1:
        t1 = time.time()
        print(f"Build time (clock): {t1 - t0:.2f} seconds")


# Backwards compatibility
app = main

if __name__ == "__main__":
    main()
