from textwrap import dedent

from devtools import debug
from markupsafe import Markup
from prettyprinter import pformat
from starlite import Template, get

from nua_server.client import get_client
from nua_server.menus import ADMIN_MENU, MAIN_MENU


def get_handlers():
    return [
        admin,
        settings,
        app,
    ]


@get("/admin/")
async def admin() -> Template:
    client = get_client()
    result = client.call("list")
    result.sort(key=lambda app: app["app_id"].lower())

    from webbits.html import html

    body = h = html()
    with h.div(class_=["content", "~neutral"]):
        h.h2("Apps")
        with h.ul():
            for instance in result:
                site_config = instance["site_config"]
                metadata = site_config["image_nua_config"]["metadata"]
                url = f"/admin/apps/{instance['app_id']}/"
                title = metadata["title"]
                h.li(h.a(title, href=url))

    # body = """
    # <div class="content ~neutral">
    # <h2 class="">Apps</h2>
    # <ul class="">
    # """
    # for instance in result:
    #     site_config = instance["site_config"]
    #     metadata = site_config["image_nua_config"]["metadata"]
    #
    #     url = f"/admin/apps/{instance['app_id']}/"
    #     body += dedent(
    #         f"""
    #         <li><a href="{url}">{metadata["title"]}</a></li>
    #     """
    #     )
    # body += "</ul></div>"
    debug(str(body))

    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": "Admin",
        "body": Markup(body),
    }
    return Template(name="admin/index.html", context=context)


@get("/admin/apps/{app_id:str}/")
async def app(app_id: str) -> Template:
    client = get_client()
    result = client.call("list")

    app = None
    for instance in result:
        if instance["app_id"] == app_id:
            app = instance
            break

    body = dedent(
        f"""
        <div class="content ~neutral">
        <h2 class="">Raw output</h2>
        <pre>
        {json_pp(app)}
        </pre>
        </div>
    """
    )

    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": f"App: {app_id}",
        "body": Markup(body),
    }
    return Template(name="admin/index.html", context=context)


@get("/admin/settings/")
async def settings() -> Template:
    client = get_client()
    result = client.call("settings")

    body = dedent(
        f"""
        <div class="content ~neutral">
        <h2 class="">Raw output</h2>
        <pre>
        {json_pp(result)}
        </pre>
        </div>
    """
    )

    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": "Settings",
        "body": Markup(body),
    }
    return Template(name="admin/default.html", context=context)


def json_pp(obj):
    return pformat(obj, indent=4, sort_dict_keys=True)
