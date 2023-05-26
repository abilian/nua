from dataclasses import dataclass

from nua.lib.docker import display_one_docker_img
from nua.lib.panic import vprint
from nua.lib.tool.state import verbosity

from ..docker_utils import pull_docker_image


@dataclass(frozen=True)
class LocalServiceBase:
    def aliases(self) -> list:
        return []

    def _pull_docker_image(self, required_image) -> bool:
        with verbosity(0):
            vprint(f"pulling docker image '{required_image}'")
        image = pull_docker_image(required_image)
        if image:
            with verbosity(0):
                display_one_docker_img(image)
            return True
        else:
            return False

    def restart(self) -> bool:
        return True

    def environment(self, _site: dict | None = None) -> dict:
        return {}
