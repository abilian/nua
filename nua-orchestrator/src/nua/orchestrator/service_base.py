from .docker_utils import display_one_docker_img, pull_docker_image
from .state import verbosity


class ServiceBase:
    def __init__(self, options: dict):
        self.options = options

    def aliases(self) -> list:
        return []

    def _pull_docker_image(self, required_image) -> bool:
        if verbosity(1):
            print(f"pulling docker image '{required_image}'")
        image = pull_docker_image(required_image)
        if image:
            if verbosity(1):
                display_one_docker_img(image)
            return True
        else:
            return False

    def check_site_configuration(self, site: dict | None = None) -> bool:
        required_image = self.options.get("image")
        format = self.options.get("format")
        if required_image and format == "docker":
            return self._pull_docker_image(required_image)
        return True

    def restart(self) -> bool:
        return True

    def environment(self, site: dict | None = None) -> dict:
        return {}