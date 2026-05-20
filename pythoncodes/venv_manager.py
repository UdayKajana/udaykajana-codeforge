import importlib.metadata
import re
import subprocess
import sys
import time
from pathlib import Path

_CACHE_FILE = Path.home() / ".cache" / "venv_manager_verified"
_CACHE_TTL = 2 * 60 * 60  # 2 hours in seconds


def _is_cache_valid() -> bool:
    if not _CACHE_FILE.exists():
        return False
    return (time.time() - _CACHE_FILE.stat().st_mtime) < _CACHE_TTL


def _touch_cache() -> None:
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.touch()


def _check_packages(packages: list[str]) -> list[str]:
    missing = []
    for pkg in packages:
        name = re.split(r"[><=!~\s\[]", pkg)[0].strip()
        try:
            dist = importlib.metadata.distribution(name)
            print(f"[deps] {name} already installed (version {dist.version})")
        except importlib.metadata.PackageNotFoundError:
            print(f"[deps] {name} not installed — will install")
            missing.append(pkg)
    return missing


def install_deps(packages: list[str]) -> None:
    if not packages:
        return

    if _is_cache_valid():
        print("[deps] all dependencies verified recently — skipping checks")
        return

    missing = _check_packages(packages)

    for pkg in missing:
        name = re.split(r"[><=!~\s\[]", pkg)[0].strip()
        print(f"[deps] installing {name}...", end="", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-qU", pkg],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f" failed!\n[deps] error: {result.stderr.strip()}")
            raise subprocess.CalledProcessError(result.returncode, "pip install")
        print(" done!")

    _touch_cache()
