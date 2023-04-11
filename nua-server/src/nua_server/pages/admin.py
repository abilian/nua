from markupsafe import Markup
from prettyprinter import pformat
from webbits.html import html

from nua_server.app import app
from nua_server.client import get_client
from nua_server.menus import ADMIN_MENU, MAIN_MENU


@app.get("/admin/")
@app.ext.template("admin/index.html")
async def admin_view(request) -> dict:
    client = get_client()
    result = client.call("list")
    result.sort(key=lambda app: app["app_id"].lower())

    body = h = html()
    with h.div(class_="content ~neutral"):
        h.h2("Apps")
        with h.ul():
            for instance in result:
                site_config = instance["site_config"]
                metadata = site_config["image_nua_config"]["metadata"]
                url = f"/admin/apps/{instance['app_id']}/"
                title = metadata["title"]
                # Should be: h.li(h.a(title, href=url))
                with h.li():
                    h.a(title, href=url)

    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": "Admin",
        "body": Markup(str(body)),
    }
    return context


@app.get("/admin/apps/<app_id:str>/")
@app.ext.template("admin/index.html")
async def app_view(request, app_id: str) -> dict:
    client = get_client()
    result = client.call("list")

    app = None
    for instance in result:
        if instance["app_id"] == app_id:
            app = instance
            break

    body = h = html()
    with h.div(class_="content ~neutral"):
        h.h2("Raw output")
        h.pre(json_pp(app))

    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": f"App: {app_id}",
        "body": Markup(str(body)),
    }
    return context


@app.get("/admin/settings/")
@app.ext.template("admin/default.html")
async def settings_view(request) -> dict:
    client = get_client()
    result = client.call("settings")

    body = h = html()
    with h.div(class_="content ~neutral"):
        h.h2("Raw output")
        h.pre(json_pp(result))

    context = {
        "main_menu": MAIN_MENU,
        "admin_menu": ADMIN_MENU,
        "title": "Settings",
        "body": Markup(str(body)),
    }
    return context


def json_pp(obj):
    return pformat(obj, indent=4, sort_dict_keys=True)
