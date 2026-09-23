from __future__ import annotations

from dataclasses import dataclass
import tomllib
from pathlib import Path

import pathspec
import pytest


PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins"

@dataclass(frozen=True)
class DeclaredFilesCase:
    plugin: str
    package: str
    source_paths: tuple[str, ...]
    excluded_paths: tuple[str, ...]


CASES = (
    pytest.param(DeclaredFilesCase("typescript", "habit_hooks_typescript", ("src/billing.ts", "src/app.tsx", "packages/api/src/handler.ts"), ("node_modules/left-pad/index.ts", "node_modules/@types/node/index.d.ts", "packages/api/node_modules/lodash/index.ts")), id="typescript-source-not-node-modules"),
    pytest.param(DeclaredFilesCase("python", "habit_hooks_python", ("src/billing.py", "tests/test_billing.py", "conftest.py"), (".venv/lib/python3.12/site-packages/attrs/__init__.py", "venv/lib/python3.11/site-packages/jinja2/environment.py", ".tox/py312/lib/python3.12/site-packages/pytest/__init__.py", ".venv/bin/activate_this.py", "venv/bin/activate_this.py")), id="python-source-not-installed-packages"),
    pytest.param(DeclaredFilesCase("php", "habit_hooks_php", ("src/Billing.php", "tests/BillingTest.php"), ("vendor/symfony/console/Application.php", "vendor/autoload.php")), id="php-source-not-vendor"),
    pytest.param(DeclaredFilesCase("java", "habit_hooks_java", ("src/main/java/com/example/Billing.java", "src/test/java/com/example/BillingTest.java"), ("target/generated-sources/annotations/com/example/Generated.java", "build/generated/sources/annotationProcessor/java/main/com/example/Generated.java")), id="java-source-not-build-output"),
    pytest.param(DeclaredFilesCase("ruby", "habit_hooks_ruby", ("app/models/billing.rb", "lib/tasks/import.rake", "spec/billing_spec.rb", "Rakefile", "Gemfile", "acme.gemspec", "engines/shop/Gemfile"), ("vendor/bundle/ruby/3.4.0/gems/rails-8.0.0/lib/rails.rb", "vendor/cache/rack-3.1.0/lib/rack.rb", "vendor/cache/rack-3.1.0/rack.gemspec", "vendor/cache/rack-3.1.0/Rakefile", "vendor/bundle/ruby/3.4.0/gems/rails-8.0.0/tasks/engine.rake", "vendor/Gemfile", "tmp/cache/bootsnap/compile-cache-iseq/a.rb", "tmp/scratch.gemspec", "tmp/Rakefile", "tmp/cache/assets/import.rake", "tmp/cache/Gemfile", "db/schema.rb")), id="ruby-source-not-installed-gems"),
)


def _declared_files(plugin: str, package: str) -> pathspec.PathSpec:
    config_path = PLUGIN_ROOT / plugin / "src" / package / "config.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    return pathspec.PathSpec.from_lines("gitignore", config["files"])


@pytest.mark.parametrize("case", CASES)
def test_declared_source_paths_match_and_dependencies_miss(case: DeclaredFilesCase) -> None:
    spec = _declared_files(case.plugin, case.package)

    assert [path for path in case.source_paths if spec.match_file(path)] == list(case.source_paths)
    assert [path for path in case.excluded_paths if spec.match_file(path)] == []
