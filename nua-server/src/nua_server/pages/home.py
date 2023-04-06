from pprint import pp

from starlite import Template, get

from nua_server.client import get_client
from nua_server.menus import MAIN_MENU


def get_handlers():
    return [
        home,
    ]


@get("/")
async def home() -> Template:
    client = get_client()

    result = client.call("list")
    pp(result)

    apps = []
    for instance in result:
        metadata = instance["site_config"]["image_nua_config"]["metadata"]
        apps.append({
            "app_id": instance["app_id"],
            "name": metadata["title"],
            "tagline": metadata["tagline"],
        })
    apps.sort(key=lambda app: app["name"].lower())

    context = {
        "main_menu": MAIN_MENU,
        "apps": apps,
    }
    return Template(name="home/index.html", context=context)
