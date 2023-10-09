#!/usr/bin/env python

import os

import tomli
from git import Repo


def main():
    repo = Repo(".")

    current_version = ""

    prev_commits = reversed(list(repo.iter_commits()))
    for commit in prev_commits:
        tree = commit.tree
        for entry in tree:
            if entry.name != "pyproject.toml":
                continue

            content = entry.data_stream.read()
            data = tomli.loads(content.decode())
            version = data["tool"]["poetry"]["version"]
            if version != current_version:
                current_version = version
                cmd = f"git tag v{version} {hash}"
                print(cmd)
                os.system(cmd)  # noqa: S605


if __name__ == "__main__":
    main()
