from __future__ import annotations

import argparse
import importlib
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
    args: list
    options: list
    cli: CLI

    arguments = []

    def __init__(self, args, cli):
        self.args = args
        self.cli = cli

    @abstractmethod
    def run(self):
        raise NotImplementedError


class Argument:
    def __init__(self, name: str, default=None, **kwargs):
        self.name = name
        self.kwargs = kwargs


class Option:
    def __init__(self, *args: list[str], **kwargs):
        self.args = args
        self.kwargs = kwargs


class CLI:
    def __init__(self):
        self.commands = []

    def __call__(self):
        return self.run()

    def run(self):
        command = self.find_command()
        print(f"Running command: {command.name}")

        parser = argparse.ArgumentParser()
        for argument in command.arguments:
            parser.add_argument(argument.name, **argument.kwargs)
        argv = sys.argv[len(command.name.split()) + 1 :]
        args = parser.parse_args(argv)

        try:
            cmd = command(args, self)
            cmd.run()
        except (BadArgument, CommandError) as e:
            print(red(e))
            sys.exit(1)

    def find_command(self):
        args = sys.argv[1:]
        args_str = " ".join(args)
        commands = sorted(self.commands, key=lambda command: -len(command.name))
        for command in commands:
            if args_str.startswith(command.name):
                return command

    def scan(self, module_name: str):
        root_module = importlib.import_module(module_name)
        root_module_name = root_module.__name__
        root_path = Path(root_module.__file__).parent
        for _, module_name, _ in iter_modules([root_path]):
            module = importlib.import_module(f"{root_module_name}.{module_name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)

                if isclass(attribute) and issubclass(attribute, Command):
                    self.add_command(attribute)

    def add_command(self, command_class: type[Command]):
        if isabstract(command_class):
            return
        self.commands.append(command_class)

    def print_help(self):
        self.print_version()
        self.print_usage()
        self.print_commands()

    def print_version(self):
        version = get_version()
        print(f"{bold('Nua CLI')} ({version})")
        print()

    def print_usage(self):
        print(bold("Usage:"))
        print("  nua <command> [options] [arguments]")
        print()

    def print_commands(self):
        print(bold("Available commands:"))

        def sorter(command):
            return len(command.name.split(" ")), command.name

        commands = [command for command in self.commands if command.name]
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
