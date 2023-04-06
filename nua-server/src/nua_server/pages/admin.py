from prettyprinter import pformat
from textwrap import dedent

from markupsafe import Markup
from starlite import Template, get

from nua_server.client import get_client
from nua_server.menus import MAIN_MENU, ADMIN_MENU


def get_handlers():
    return [
        admin,
        settings,
    ]


@get("/admin/")
async def admin() -> Template:
    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": "Admin",
        "body": "TODO",
    }
    return Template(name="admin/index.html", context=context)


@get("/admin/settings/")
async def settings() -> Template:
    client = get_client()
    result = client.call("settings")

    body = dedent(f"""
        <h2 class="">Raw output</h2>
        <pre>
        {json_pp(result)}
        </pre>
    """)

    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": "Settings",
        "body": Markup(body),
    }
    return Template(name="admin/default.html", context=context)


def json_pp(obj):
    return pformat(obj, indent=4, sort_dict_keys=True)
