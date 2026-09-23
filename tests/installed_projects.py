
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TYPESCRIPT_PLUGIN = REPO_ROOT / "plugins" / "typescript"

OVERSIZED_LINES = 205
MAX_ALLOWED_LINES = 200

ESM_MANIFEST = '{ "name": "demo", "version": "0.0.0", "type": "module" }\n'

TYPESCRIPT_SOURCE = "src/helper.ts"
PYTHON_SOURCE = "billing.py"
PHP_SOURCE = "billing.php"
JAVA_SOURCE = "Billing.java"
RUBY_SOURCE = "billing.rb"


def _project(tmp_path: Path, name: str, config: str) -> Path:
    project = tmp_path / name
    (project / ".habit-hooks").mkdir(parents=True)
    (project / ".habit-hooks" / "config.toml").write_text(config, encoding="utf-8")
    return project


def oversized_project(tmp_path: Path, name: str) -> Path:
    project = _project(
        tmp_path,
        name,
        'plugins = ["generic"]\n'
        'files = ["**/*.py"]\n\n'
        "[sensors.jscpd]\n"
        "disabled = true\n",
    )
    lines = "".join(f"x{n} = 0\n" for n in range(1, OVERSIZED_LINES + 1))
    (project / "big.py").write_text(lines, encoding="utf-8")
    return project


def java_project(tmp_path: Path) -> Path:
    project = _project(tmp_path, "java-proj", 'plugins = ["java"]\n')
    (project / JAVA_SOURCE).write_text(
        "import java.io.File;\n"
        "import java.io.IOException;\n"
        "class Billing {\n"
        "    double charge(double a, double b, double c, double d, double e) {\n"
        "        int dead = 1;\n"
        "        if (a > 0) {\n"
        "            if (b > 0) {\n"
        "                if (c > 0) {\n"
        "                    a += 1;\n"
        "                }\n"
        "            }\n"
        "        }\n"
        "        return a + b + c + d + e;\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    return project


def php_project(tmp_path: Path) -> Path:
    project = _project(tmp_path, "php-proj", 'plugins = ["php"]\n')
    (project / PHP_SOURCE).write_text(
        "<?php\n"
        "function charge($a, $b, $c, $d, $e, $f, $g, $h, $i, $j, $k) {\n"
        "    $unused = 1;\n"
        "    return $a + $b + $c + $d + $e + $f + $g + $h + $i + $j + $k;\n"
        "}\n",
        encoding="utf-8",
    )
    return project


def ruby_project(tmp_path: Path) -> Path:
    project = _project(tmp_path, "ruby-proj", 'plugins = ["ruby"]\n')
    (project / ".rubocop.yml").write_text(
        "AllCops:\n"
        "  DisabledByDefault: true\n"
        "  TargetRubyVersion: 3.1\n"
        "Metrics/ParameterLists:\n"
        "  Enabled: true\n"
        "Lint/UselessAssignment:\n"
        "  Enabled: true\n",
        encoding="utf-8",
    )
    (project / RUBY_SOURCE).write_text(
        "def charge(a, b, c, d, e, f, g)\n  unused = 1\n  a + b + c\nend\n",
        encoding="utf-8",
    )
    return project


def typescript_project(tmp_path: Path) -> Path:
    project = _project(
        tmp_path,
        "typescript-proj",
        'plugins = ["typescript"]\n\n'
        "[sensors.eslint]\n"
        "disabled = true\n\n"
        "[sensors.knip]\n"
        "disabled = true\n",
    )
    (project / "src").mkdir()
    (project / "package.json").write_text(ESM_MANIFEST, encoding="utf-8")
    (project / "node_modules").symlink_to(TYPESCRIPT_PLUGIN / "node_modules")
    (project / TYPESCRIPT_SOURCE).write_text(
        "export function used(): void {\n"
        "  // this comment restates what the code already says clearly\n"
        "}\n",
        encoding="utf-8",
    )
    return project


def python_project(tmp_path: Path) -> Path:
    project = _project(
        tmp_path,
        "python-proj",
        'plugins = ["python"]\n\n[sensors.deptry]\ndisabled = true\n',
    )
    (project / PYTHON_SOURCE).write_text(
        "def total(items):\n    unused = 1\n    return sum(items)\n",
        encoding="utf-8",
    )
    return project
