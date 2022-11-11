from pathlib import Path

from .build_image import build_test_image


def test_flask_sub_folder():
    root = Path(__file__).parent
    build_test_image(root / "apps" / "flask_sub_folder")
