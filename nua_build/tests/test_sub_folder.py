from pathlib import Path

from .build_image import build_test_image

root = Path(__file__).parent


def test_flask_sub_folder():
    build_test_image(root / "apps" / "flask_sub_folder")


def test_flask_sub_folder2():
    build_test_image(root / "apps" / "flask_sub_folder2")
