"""Script to build a nua package (experimental)

- information come from a mandatory local file: "nua-config" (.toml, .json, .yaml)
- origin may be a source tar.gz or a git repository or a docker image...
- build locally or wrap docker image

Note: **currently use "nua-build ..." for command line**.
See later if move this to "nua ...".
"""
import argparse
import sys
import traceback
from time import perf_counter
from typing import Any
import snoop
from cleez.actions import VERSION, COUNT, STORE_TRUE
from nua.lib.nua_config import NuaConfigError, NuaConfig
from nua.lib.elapsed import elapsed
from nua.lib.panic import Abort, red_line, show, info
from nua.lib.tool.state import set_color, set_verbosity, verbosity
import pydantic

from . import __version__
from .builders import BuilderError, get_builder

snoop.install()


def app(argv: list | None = None):
    t0 = perf_counter()
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()

    # Generic / classic options
    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action=COUNT,
        help="Show more informations, until -vvv.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        default=False,
        action="store_true",
        help="Suppress non-error messages.",
    )
    parser.add_argument(
        "--color",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Enable / disable colorized messages.",
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
        "config_file",
        nargs="?",
        default=".",
        help="Path to the package dir or 'nua-config' file.",
    )
    parser.add_argument("-t", "--time", action=STORE_TRUE, help="Print timing info.")
    parser.add_argument(
        "-s",
        "--save",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Save image locally after the build.",
    )
    parser.add_argument(
        "--validate",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Validate the nconfig.toml file, no build.",
    )

    args = parser.parse_args(argv)

    if args.quiet:
        set_verbosity(-1)
    else:
        set_verbosity(args.verbose)
    set_color(args.color)

    config = parse_nua_config(args.config_file, args.validate)
    opts = {
        "save_image": args.save,
        "show_elapsed_time": args.time,
        "verbosity": args.verbose,
        "start_time": t0,
    }
    build_app(config, opts)


def parse_nua_config(config_file: str | None, validate_only: bool) -> NuaConfig:
    try:
        config = NuaConfig(config_file or ".")
    except pydantic.error_wrappers.ValidationError as valid_error:
        print(valid_error)
        red_line("Some error in nua config file.")
        raise SystemExit(1)
    except NuaConfigError as e:
        # FIXME: not for production
        traceback.print_exc(file=sys.stderr)
        raise Abort(e.args[0])
    if validate_only:
        show("No error in nua config file.")
        raise SystemExit(0)
    return config


def build_app(config: NuaConfig, opts: dict[str, Any]):
    save = opts["save_image"]
    for provider in config.providers:
        if provider.get("type") == "app":
            build_sub_app(config, provider, save_image=save)
    build_main_app(config, save_image=save)
    if opts["show_elapsed_time"] or opts["verbosity"] >= 1:
        t1 = perf_counter()
        print(f"Build time (clock): {elapsed(t1-opts['start_time'])}")


def build_sub_app(config: NuaConfig, provider: dict[str, Any], save_image: bool):
    builder = get_builder(config, provider=provider, save_image=save_image)
    try:
        print("WIP building sub app...")
        print(builder)
    except BuilderError as e:
        # FIXME: not for production
        traceback.print_exc(file=sys.stderr)
        raise Abort from e


def build_main_app(config: NuaConfig, save_image: bool):
    builder = get_builder(config, save_image=save_image)
    with verbosity(2):
        info(f"Using builder: {builder.__class__.__name__}")
    try:
        builder.run()
    except BuilderError as e:
        # FIXME: not for production
        traceback.print_exc(file=sys.stderr)
        raise Abort from e


def main():
    app(sys.argv)


if __name__ == "__main__":
    main()
