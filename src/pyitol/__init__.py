"""PyiTOL - Python CLI tool for iTOL phylogenetic tree visualization automation."""

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    # Fallback when the package is run from source without setuptools_scm.
    __version__ = "1.0.2"

__license__ = "MIT"
__release_date__ = "2026-08-22"


def get_git_hash() -> str:
    """Get the current git commit hash. Returns empty string if unavailable."""
    import subprocess
    from pathlib import Path

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:  # noqa: S110
        pass
    return ""


def get_version_string() -> str:
    """Get full version string with optional git hash."""
    git_hash = get_git_hash()
    if git_hash:
        return f"{__version__} (commit: {git_hash})"
    return __version__


# Known dependency licenses (from PyPI/project metadata)
_DEPENDENCY_LICENSES = {
    "typer": "MIT",
    "rich": "MIT",
    "pandas": "BSD-3-Clause",
    "dendropy": "BSD-3-Clause",
    "numpy": "BSD-3-Clause",
    "requests": "Apache-2.0",
    "PyYAML": "MIT",
    "pydantic": "MIT",
    "scipy": "BSD-3-Clause",
}


def get_dependency_versions() -> dict[str, str]:
    """Get versions of key dependencies."""
    deps = {}
    for name, module in [
        ("typer", "typer"),
        ("rich", "rich"),
        ("pandas", "pandas"),
        ("dendropy", "dendropy"),
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("PyYAML", "yaml"),
        ("pydantic", "pydantic"),
        ("scipy", "scipy"),
    ]:
        try:
            mod = __import__(module)
            ver = getattr(mod, "__version__", "unknown")
            license_ = _DEPENDENCY_LICENSES.get(name, "unknown")
            deps[name] = f"{ver} ({license_})"
        except ImportError:
            deps[name] = "not installed"
    return deps
