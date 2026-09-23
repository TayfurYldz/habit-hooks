
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from habit_hooks.project_paths import venv_executable
from wheel_metadata import built, required_from_elsewhere

REPO_ROOT = Path(__file__).resolve().parents[1]


def require_uv() -> str:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is not on PATH")
    return uv


def build_wheels(out_dir: Path, packages: tuple[str, ...]) -> None:
    for package in packages:
        subprocess.run(
            [require_uv(), "build", "--wheel", "--package", package, "--out-dir", str(out_dir)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",  # sensors.spawn's policy
        )


def install_wheels(venv: Path, wheels_dir: Path) -> Path:
    python = _fresh_venv(venv)
    wheels = [str(wheel) for wheel in sorted(wheels_dir.glob("*.whl"))]
    _uv_run("pip", "install", "--python", str(python), "--no-deps", *wheels)
    _install_what_this_repo_does_not_build(python, wheels_dir)
    _assert_the_built_wheels_are_installed(python, wheels_dir)
    return venv_executable(venv, "habit-sensors")


def install_by_name(venv: Path, wheels_dir: Path, name: str) -> Path:
    python = _fresh_venv(venv)
    _install_what_this_repo_does_not_build(python, wheels_dir)
    _uv_run(
        "pip", "install", "--python", str(python),
        "--no-index", "--find-links", str(wheels_dir), name,
    )
    _assert_the_built_wheels_are_installed(python, wheels_dir)
    return python


def installed_packages(python: Path) -> dict[str, str]:
    listed = _uv_run("pip", "list", "--python", str(python), "--format", "json").stdout
    return {package["name"]: package["version"] for package in json.loads(listed)}


def _uv_run(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [require_uv(), *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",  # sensors.spawn's policy
    )
    if result.returncode != 0:
        pytest.fail(f"uv {' '.join(args)} failed:\n{result.stderr}")
    return result


def _fresh_venv(venv: Path) -> Path:
    _uv_run("venv", str(venv))
    return venv_executable(venv, "python")


def _install_what_this_repo_does_not_build(python: Path, wheels_dir: Path) -> None:
    required = required_from_elsewhere(wheels_dir)
    if required:
        _uv_run("pip", "install", "--python", str(python), *required)


def _assert_the_built_wheels_are_installed(python: Path, wheels_dir: Path) -> None:
    from_here = built(wheels_dir)
    installed = installed_packages(python)
    answering = {name: installed.get(name) for name in from_here}
    assert answering == from_here, f"installed {answering}, built {from_here}"
