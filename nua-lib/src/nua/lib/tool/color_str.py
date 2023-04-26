"""Return text string colorized.

from color_str import ColorStr as C print(C.green_bright('Take') +
C.blue(' it ', underline=True)       + C.yellow_bold('easy',
bgcolor='red'))
"""
from functools import cache, partialmethod


class ColorStr:
    COL = {
        "black": "\u001b[30",
        "red": "\u001b[31",
        "green": "\u001b[32",
        "yellow": "\u001b[33",
        "blue": "\u001b[34",
        "magenta": "\u001b[35",
        "cyan": "\u001b[36",
        "white": "\u001b[37",
        "reset": "\u001b[0m",
        "bright": ";1",
        "suffix": "m",
        "bold": "\u001b[1m",
        "underline": "\u001b[4m",
        "reversed": "\u001b[7m",
        "bg_black": "\u001b[40",
        "bg_red": "\u001b[41",
        "bg_green": "\u001b[42",
        "bg_yellow": "\u001b[43",
        "bg_blue": "\u001b[44",
        "bg_magenta": "\u001b[45",
        "bg_cyan": "\u001b[46",
        "bg_white": "\u001b[47",
    }

    @classmethod
    def _color(cls, cmd: list, color: str, bright: bool):
        cmd.append(cls.COL[color])
        if bright:
            cmd.append(cls.COL["bright"])
        cmd.append(cls.COL["suffix"])

    @classmethod
    @cache
    def _command(cls, color: str = "", bgcolor: str = "", **kwargs) -> str:
        cmd = []
        for key in ("bold", "underline", "reversed"):
            if key in kwargs:
                cmd.append(cls.COL[key])
        if color:
            cls._color(cmd, color, bool(kwargs.get("bright")))
        if bgcolor:
            cls._color(cmd, f"bg_{bgcolor}", bool(kwargs.get("bright")))
        return "".join(cmd)

    @classmethod
    def colorize(
        cls,
        txt: str,
        color: str = "",
        bgcolor: str = "",
        **kwargs,
    ) -> str:
        """Return text string colorized.

        kwargs are bools for keys "bright", "bold", "underline" and
        "reversed".
        """
        cmd = cls._command(color=color, bgcolor=bgcolor, **kwargs)
        return f"{cmd}{txt}{cls.COL['reset']}"

    black = partialmethod(colorize, color="black")
    gray = partialmethod(colorize, color="black", bright=True)
    red = partialmethod(colorize, color="red")
    green = partialmethod(colorize, color="green")
    yellow = partialmethod(colorize, color="yellow")
    blue = partialmethod(colorize, color="blue")
    magenta = partialmethod(colorize, color="magenta")
    cyan = partialmethod(colorize, color="cyan")
    white = partialmethod(colorize, color="white")
    black_bold = partialmethod(colorize, color="black", bold=True)
    red_bold = partialmethod(colorize, color="red", bold=True)
    green_bold = partialmethod(colorize, color="green", bold=True)
    yellow_bold = partialmethod(colorize, color="yellow", bold=True)
    blue_bold = partialmethod(colorize, color="blue", bold=True)
    magenta_bold = partialmethod(colorize, color="magenta", bold=True)
    cyan_bold = partialmethod(colorize, color="cyan", bold=True)
    white_bold = partialmethod(colorize, color="white", bold=True)
    black_bright = partialmethod(colorize, color="black", bright=True)
    red_bright = partialmethod(colorize, color="red", bright=True)
    green_bright = partialmethod(colorize, color="green", bright=True)
    yellow_bright = partialmethod(colorize, color="yellow", bright=True)
    blue_bright = partialmethod(colorize, color="blue", bright=True)
    magenta_bright = partialmethod(colorize, color="magenta", bright=True)
    cyan_bright = partialmethod(colorize, color="cyan", bright=True)
    white_bright = partialmethod(colorize, color="white", bright=True)
