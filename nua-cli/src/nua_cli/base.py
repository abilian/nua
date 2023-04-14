"""
Simple framework for building command line applications with multiple
commands and subcommands.

Similar to Cleo.

Based on the stdlib argparse module.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from abc import ABC, abstractmethod
from inspect import isabstract, isclass
from itertools import groupby
from pathlib import Path
from pkgutil import iter_modules

from nua_cli.colors import blue, bold, green, red
from nua_cli.exceptions import BadArgument, CommandError
from nua_cli.version import get_version


class Command(ABC):
    name: str
    cli: CLI

    arguments: list[Argument] = []
    options: list[Option] = []

    def __init__(self, cli):
        self.cli = cli
        # self.arguments = []
        # self.options = []

    @abstractmethod
    def run(self, *args, **kwargs):
        raise NotImplementedError


class Argument:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Option:
    def __init__(self, *args: list[str], **kwargs):
        self.args = args
        self.kwargs = kwargs


class CLI:
    def __init__(self, help_maker=None):
        self.commands = []
        self.options = []
        if help_maker:
            self.help_maker = help_maker
        else:
            self.help_maker = HelpMaker()

    #
    # Public API
    #
    def __call__(self):
        # Convenience. Needed?
        return self.run()

    def run(self):
        command = self.find_command()
        try:
            args = self.parse_args(command)
        except argparse.ArgumentError as e:
            print(red(f"Argument parsing error: {e}\n"))
            print("Usage:\n")
            self.help_maker.print_help(self)
            sys.exit(1)
        self.common_options(args)
        self.run_command(args, command)

    def scan(self, module_name: str):
        root_module = importlib.import_module(module_name)
        root_module_name = root_module.__name__
        root_path = Path(root_module.__file__).parent  # type: ignore
        for _, module_name, _ in iter_modules([str(root_path)]):
            module = importlib.import_module(f"{root_module_name}.{module_name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)

                if isclass(attribute) and issubclass(attribute, Command):
                    self.add_command(attribute)

    def add_option(self, *args, **kwargs):
        if args and isinstance(args[0], Option):
            option = args[0]
            self.options.append(option)
        else:
            self.options.append(Option(*args, **kwargs))

    #
    # Internal API
    #
    def find_command(self) -> Command:
        args = sys.argv[1:]
        args = [arg for arg in args if not arg.startswith("-")]
        args_str = " ".join(args)
        commands = sorted(self.commands, key=lambda command: -len(command.name))
        for command in commands:
            if args_str.startswith(command.name):
                return command(self)
        raise CommandError("No command found")

    def parse_args(self, command: Command):
        parser = MyArgParser(add_help=False, exit_on_error=False)
        for argument in command.arguments:
            parser.add_argument(*argument.args, **argument.kwargs)
        for option in self.options:
            parser.add_argument(*option.args, **option.kwargs)
        argv = sys.argv[len(command.name.split()) + 1 :]
        args = parser.parse_args(argv)
        return args

    def run_command(self, args: argparse.Namespace, command: Command):
        try:
            self.call_command(command, args)
        except (BadArgument, CommandError) as e:
            print(red(e))
            sys.exit(1)

    def call_command(self, command: Command, args: argparse.Namespace):
        # Inject arguments into the command `run` method.
        sign = inspect.signature(command.run)
        kwargs = {}
        for name, parameter in sign.parameters.items():
            # Needed ?
            if name == "self":
                continue
            if name in args:
                value = getattr(args, name)
            else:
                value = parameter.default
            kwargs[name] = value

        command.run(**kwargs)

    def add_command(self, command_class: type[Command]):
        if isabstract(command_class):
            return
        self.commands.append(command_class)

    def common_options(self, args: argparse.Namespace):
        if args.help:
            self.help_maker.print_help(self)
            sys.exit(0)
        if args.version:
            print(get_version())
            sys.exit(0)

    def print_help(self):
        self.help_maker.print_help(self)


class MyArgParser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)


class HelpMaker:
    def print_help(self, cli):
        self.print_version()
        self.print_usage()
        self.print_options(cli.options)
        self.print_commands(cli.commands)

    def print_version(self):
        version = get_version()
        print(f"{bold('Nua CLI')} ({version})")
        print()

    def print_usage(self):
        print(bold("Usage:"))
        print("  nua <command> [options] [arguments]")
        print()

    def print_options(self, options: list[Option]):
        print(bold("Options:"))
        for option in options:
            print(f"  {blue(option.args[0])}  {option.kwargs['help']}")
        print()

    def print_commands(self, commands: list[Command]):
        print(bold("Available commands:"))

        def sorter(command):
            return len(command.name.split(" ")), command.name

        commands = [command for command in commands if command.name]
        commands = sorted(commands, key=sorter)
        simple_commands = [command for command in commands if " " not in command.name]
        complex_commands = [command for command in commands if " " in command.name]
        max_command_length = max(len(command.name) for command in commands)
        w = max_command_length

        for command in simple_commands:
            cmd_name = f"{command.name:<{w}}"
            print(f"  {blue(cmd_name)}  {command.__doc__}")

        groups = groupby(complex_commands, lambda command: command.name.split(" ")[0])
        for group_name, group in groups:
            print()
            print(f" {green(group_name)}")

            for command in group:
                if not command.name:
                    continue
                cmd_name = f"{command.name:<{w}}"
                print(f"  {blue(cmd_name)}  {command.__doc__}")
