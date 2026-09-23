
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

PACKAGE_DIRS = [
    REPO,
    REPO / "plugins/generic",
    REPO / "plugins/python",
    REPO / "plugins/typescript",
    REPO / "plugins/php",
    REPO / "plugins/java",
    REPO / "plugins/ruby",
]

published = pytest.mark.parametrize(
    "package_dir", PACKAGE_DIRS, ids=lambda path: path.name
)


def _project(package_dir: Path) -> dict:
    pyproject = tomllib.loads((package_dir / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["project"]


@published
def test_the_readme_it_declares_exists(package_dir: Path) -> None:
    readme = _project(package_dir).get("readme")
    assert readme
    assert (package_dir / readme).is_file()


@published
def test_it_declares_keywords(package_dir: Path) -> None:
    assert _project(package_dir).get("keywords")


@published
def test_it_declares_classifiers(package_dir: Path) -> None:
    assert _project(package_dir).get("classifiers")


@published
def test_it_declares_a_license(package_dir: Path) -> None:
    assert _project(package_dir).get("license")


@published
def test_it_declares_a_homepage_url(package_dir: Path) -> None:
    assert _project(package_dir).get("urls", {}).get("Homepage")
