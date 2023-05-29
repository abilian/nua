# TODO: duplicated

from typing import TypeAlias

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
JsonDict: TypeAlias = dict[str, JSON]
JsonList: TypeAlias = list[JSON]
