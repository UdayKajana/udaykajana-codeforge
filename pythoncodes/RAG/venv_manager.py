import atexit
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def install_deps(packages: list[str]) -> None:
    tmp_dir = tempfile.mkdtemp(prefix="venv_tmp_")
    venv_dir = Path(tmp_dir)

    venv.create(venv_dir, with_pip=True)

    python = (
        str(venv_dir / "Scripts" / "python.exe")
        if sys.platform == "win32"
        else str(venv_dir / "bin" / "python")
    )

    if packages:
        result = subprocess.run(
            [python, "-m", "pip", "install", "-qU"] + packages,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error installing packages:\n{result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, "pip install")

    site_packages = (
        venv_dir / "Lib" / "site-packages"
        if sys.platform == "win32"
        else next(venv_dir.glob("lib/python*/site-packages"))
    )
    sys.path.insert(0, str(site_packages))

    atexit.register(shutil.rmtree, tmp_dir, True)
