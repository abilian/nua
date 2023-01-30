from nua.autobuild.docker_build_utils import display_one_docker_img
from nua.lib.panic import vprint
from nua.lib.tool.state import verbosity

from ..docker_utils import pull_docker_image


class ServiceBase:
    def __init__(self, options: dict):
        self.options = options

    def aliases(self) -> list:
        return []

    def _pull_docker_image(self, required_image) -> bool:
        with verbosity(1):
            vprint(f"pulling docker image '{required_image}'")
        image = pull_docker_image(required_image)
        if image:
            with verbosity(1):
                display_one_docker_img(image)
            return True
        else:
            return False

    def check_site_configuration(self, _site: dict | None = None) -> bool:
        required_image = self.options.get("image")
        opt_format = self.options.get("format")
        if required_image and opt_format == "docker":
            return self._pull_docker_image(required_image)
        return True

    def restart(self) -> bool:
        return True

    def environment(self, _site: dict | None = None) -> dict:
        return {}
