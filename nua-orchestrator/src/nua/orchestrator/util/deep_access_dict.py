from contextlib import suppress
from pprint import pformat


class DeepAccessDict:
    def __init__(self, data=None):
        self._dic = data or {}

    def __len__(self):
        return len(self._dic)

    def __repr__(self) -> str:
        return f"DeepAccessDict({pformat(self._dic)})"

    def __str__(self):
        return pformat(self._dic)

    def read(self, *args):
        current = self._dic
        for arg in args:
            if not isinstance(current, dict):
                return None
            current = current.get(arg)
        return current

    def set(self, *args):
        if len(args) < 2:
            raise ValueError("At least 2 args required")

        key = args[-2]
        value = args[-1]
        current = self._dic
        for arg in args[:-2]:
            next = current.get(arg)
            if isinstance(next, dict):
                current = next
                continue
            current[arg] = {}
            current = current[arg]
        if isinstance(value, DeepAccessDict):
            current[key] = value.read()
        else:
            current[key] = value

    def delete(self, *args):
        if len(args) < 1:
            raise ValueError("At least 1 arg required")

        current = self._dic
        for arg in args[:-1]:
            if isinstance(current, dict):
                current = current.get(arg)
            else:
                return
        if isinstance(current, dict):
            with suppress(KeyError):
                del current[args[-1]]
