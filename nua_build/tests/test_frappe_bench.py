import shlex
import subprocess as sp  # noqa, required.
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from time import perf_counter, sleep

import docker


class TestFrappeBench:
    def test_build_frappe_bench(self):
        src_path = Path(__file__).parent / "apps" / "frappe-bench"
        image_target = "nua-frappe-bench:1.0-1"
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdirname:
            build_dir = Path(tmpdirname) / "build"
            copytree(src_path, build_dir)
            dock = docker.from_env()
            print("Time now:", datetime.now(timezone.utc).isoformat(" "))
            cmd = shlex.split(f"nua-build {build_dir}")
            print(f"'{cmd}'")
            t0 = perf_counter()
            result = sp.run(cmd, capture_output=True)
            print("Time now:", datetime.now(timezone.utc).isoformat(" "))
            print("elapsed (s):", perf_counter() - t0)
            print(" ========= result.stdout ===========")
            print(result.stdout.decode("utf8"))
            print(result.stderr.decode("utf8"))
            print(" ===================================")
            assert result.returncode == 0
            assert dock.images.list(image_target)

        print("Testing the container:")
        # clean previous run if any
        for previous in dock.containers.list(filters={"ancestor": image_target}):
            previous.kill()
        container = dock.containers.run(
            image_target,
            detach=False,
        )
        assert container.decode().split() == ["v16.18.0", "8.19.2", "1.22.19", "5.14.4"]
