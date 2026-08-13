"""Common CLI utilities shared across all command modules."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console

from pyitol.utils.io import safe_read_text


def get_console(ctx: typer.Context) -> Console:
    return ctx.obj["state"].console if ctx.obj else Console()


def _load_config_file(config_path: str) -> dict | list:
    """Load YAML or JSON config file. Returns dict or list."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    if path.stat().st_size > 10 * 1024 * 1024:  # 10 MB limit
        raise ValueError(f"配置文件过大 ({path.stat().st_size} bytes)，超过 10MB 限制")
    content = safe_read_text(path)
    if path.suffix.lower() in (".yaml", ".yml"):
        data = yaml.safe_load(content) or {}
    elif path.suffix.lower() == ".json":
        data = json.loads(content)
    else:
        try:
            data = yaml.safe_load(content) or {}
        except Exception:
            data = json.loads(content)
    if not isinstance(data, (dict, list)):
        raise ValueError(f"配置文件必须是字典或列表格式，得到 {type(data).__name__}")
    return data


# Common parameter name aliases so config files can use the CLI option names
# (e.g. `tree:` / `taxonomy:`) instead of the Python parameter names.
_PARAM_ALIASES: dict[str, list[str]] = {
    "tree_path": ["tree"],
    "taxonomy_path": ["taxonomy"],
    "columns": ["column"],
}


def _resolve_param(ctx: typer.Context, key: str, cli_value, default=None, section: str | None = None):
    """Resolve parameter value with priority: CLI > config file > default.

    If the CLI value equals the declared default, treat it as not explicitly
    provided and fall back to the config file. This allows config files to
    override Typer-declared defaults while still respecting explicit user input.
    """
    if cli_value is not None and cli_value != "" and cli_value != [] and cli_value != default:
        return cli_value

    config_data = ctx.obj.get("config_data", {}) if ctx.obj else {}

    def _lookup(keys: list[str], data: dict):
        for k in keys:
            if k in data:
                val = data[k]
                if val is not None:
                    return val
        return None

    search_keys = [key, *_PARAM_ALIASES.get(key, [])]

    if section and section in config_data:
        section_data = config_data[section]
        if isinstance(section_data, dict):
            val = _lookup(search_keys, section_data)
            if val is not None:
                return val

    val = _lookup(search_keys, config_data)
    if val is not None:
        return val

    for nested in ("task", "api", "template", "taxonomy", "tree", "utils"):
        if nested in config_data and isinstance(config_data[nested], dict):
            val = _lookup(search_keys, config_data[nested])
            if val is not None:
                return val

    return default


def _apply_config_overrides(ctx: typer.Context, **kwargs) -> dict:
    """Apply config file overrides to CLI parameters."""
    result = {}
    for key, (cli_value, default) in kwargs.items():
        result[key] = _resolve_param(ctx, key, cli_value, default)
    return result


def _common_separator_option():
    return typer.Option("TAB", "--separator", "-s", help="数据分隔符: TAB/SPACE/COMMA")


def _common_output_option():
    return typer.Option("config_template.txt", "--output", "-o", help="输出模板文件路径")


def check_output_path(output_path: str | Path, force: bool = False, no_clobber: bool = False) -> Path | None:
    """Check output path and handle overwrite protection.

    Args:
        output_path: Output file path
        force: If True, allow overwriting existing files
        no_clobber: If True, skip if file exists

    Returns:
        Path object to write to (may differ from input if file exists)

    Raises:
        SystemExit(1) if file exists and neither force nor no_clobber is set
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Skip check for /dev/null and similar special files
    if str(path) in ("/dev/null", "/dev/zero", "NUL", "nul"):
        return path

    if path.exists():
        if no_clobber:
            sys.stdout.write(f"INFO Skipping existing file: {path}\n")
            sys.stdout.flush()
            return None  # Caller should check for None
        elif not force:
            sys.stdout.write(f"ERROR Output file already exists: {path}\n")
            sys.stdout.write("      Use --force to overwrite or --no-clobber to skip.\n")
            sys.stdout.flush()
            raise SystemExit(1)

    return path


def resolve_output(
    output_path: str | Path,
    force: bool = False,
    no_clobber: bool = False,
) -> Path | None:
    """Canonical output-path resolver used by template sub-commands.

    Thin wrapper around :func:`check_output_path` so callers (including the
    unified ``template create`` entry point) can thread ``--force`` /
    ``--no-clobber`` down to the dedicated sub-commands without re-implementing
    the overwrite-protection logic.

    Args:
        output_path: Output file path.
        force: If True, allow overwriting existing files.
        no_clobber: If True, skip if file exists.

    Returns:
        Path object to write to, or ``None`` when ``no_clobber`` skips.
    """
    return check_output_path(output_path, force=force, no_clobber=no_clobber)


def resolve_output_path(
    ctx: typer.Context,
    output: str | Path,
    force: bool,
    no_clobber: bool,
) -> Path | None:
    """Resolve an output path, honoring per-command and global force flags.

    Consolidates the ~34-line force/no-clobber boilerplate that was duplicated
    across every ``template create-*`` sub-command. Both the per-command
    ``--force`` / ``--no-clobber`` options and the global flags threaded
    through ``ctx.obj`` (by the unified ``template create`` entry point) are
    OR-combined, so ``--force`` from either source enables overwriting.

    When a sub-command is dispatched from ``template create`` it may receive the
    raw ``typer.Option`` default (``False`` as declared) instead of the caller's
    actual boolean; in that case the global flag from ``ctx.obj`` is used.

    Returns:
        The resolved :class:`~pathlib.Path` to write to, or ``None`` when
        ``--no-clobber`` skips an existing file (caller should ``return``).
    """
    cli_force = bool(ctx.obj.get("_cli_force", False)) if ctx.obj else False
    cli_no_clobber = bool(ctx.obj.get("_cli_no_clobber", False)) if ctx.obj else False

    # If the per-command flag is not a real bool (dispatched default), fall
    # back to the global flag; otherwise OR the two so either source wins.
    use_force = (cli_force or force) if isinstance(force, bool) else cli_force
    use_no_clobber = (cli_no_clobber or no_clobber) if isinstance(no_clobber, bool) else cli_no_clobber

    return check_output_path(output, force=use_force, no_clobber=use_no_clobber)


def load_tree_tips(tree_path: str | Path) -> set[str]:
    """Return the set of leaf (tip) taxon labels for a tree file.

    Used by callers that only need the tip set (e.g. to filter a taxonomy
    table) without re-parsing the tree repeatedly.
    """
    import dendropy

    from pyitol.core.parser import detect_tree_schema

    tree_schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=tree_schema, preserve_underscores=True)
    return {t.taxon.label for t in tree.leaf_nodes() if t.taxon}


def load_filtered_taxonomy(
    tree_path: str | Path,
    taxonomy_path: str | Path,
    id_column: str = "id",
) -> tuple:
    """Load a tree + taxonomy and return tip-filtered taxonomy data.

    Replaces the ~6-line "read tree, collect tips, read taxonomy, rename id
    column, filter by tips" snippet that was duplicated 20+ times across the
    CLI modules. Behavior is preserved exactly:

    - The tree is parsed with ``detect_tree_schema`` and ``preserve_underscores``.
    - The taxonomy is read with ``sep=None, engine='python', dtype=str``.
    - If ``id_column`` is present it is renamed to ``id``.
    - Rows whose ``id`` is not a tree tip are dropped.

    Returns:
        ``(tree, df, tip_set, tip_order_map)`` where ``tip_order_map`` maps each
        tip label to its zero-based leaf order in the tree.
    """
    import dendropy
    import pandas as pd

    from pyitol.core.parser import detect_tree_schema

    tree_schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=tree_schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    tip_order_map = {t.taxon.label: i for i, t in enumerate(tree.leaf_nodes()) if t.taxon}
    df = pd.read_csv(str(taxonomy_path), sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    df = df[df["id"].isin(tip_set)]
    return tree, df, tip_set, tip_order_map


def validate_input_paths(*paths: str | Path | None, ctx: typer.Context | None = None) -> None:
    """Validate that all input file paths exist.

    P1-12: CLI commands should check file existence before passing to
    core functions, which throw cryptic dendropy/pandas errors.

    Args:
        *paths: File paths to check. None values are silently skipped.
        ctx: Optional typer context for console output.

    Raises:
        typer.Exit(1) if any path does not exist.
    """
    missing = []
    for p in paths:
        if p is not None and not Path(p).exists():
            missing.append(str(p))
    if missing:
        msg = f"✗ 输入文件不存在: {', '.join(missing)}"
        if ctx:
            get_console(ctx).print(f"[bold red]{msg}[/]")
        raise typer.Exit(1)


def _common_tree_option():
    return typer.Option(..., "--tree", "-r", help="Newick格式系统发育树文件路径")


def _common_taxonomy_option():
    return typer.Option(..., "--taxonomy", "-t", help="分类信息表格文件路径")


def _common_label_option(default: str = "dataset"):
    return typer.Option(default, "--label", "-l", help="数据集标签")


def _common_id_column_option():
    return typer.Option("id", "--id-column", help="ID列名")


def _common_multi_tree_option():
    return typer.Option(
        "ask",
        "--multi-tree-mode",
        "-m",
        help="多棵树处理策略: ask(默认,提示用户)/first(第一棵)/last(最后一棵)/random(随机)/split(全部分别处理)",
    )


# Re-export the canonical _assign_colors from color_tools to avoid duplication
from pyitol.utils.color_tools import _assign_colors  # noqa: F401, E402


def _parse_log_detail(detail: str) -> dict:
    """Parse detail string like 'rank=phylum, groups=5' into dict.

    Handles values that contain commas (e.g., 'columns=a,b,c') by splitting
    on comma (with optional whitespace) when followed by a key= pattern,
    rather than on every comma.
    """
    params: dict[str, str] = {}
    if not detail:
        return params
    # Split on comma (with optional whitespace) when followed by a word-char and '='
    parts = re.split(r",\s*(?=\w+=)", detail)
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip()] = value.strip()
    return params


def _parse_colors(colors: str | None) -> dict | None:
    """Parse a colors string into a dict.

    Supports both JSON and simplified 'key:value,key:value' formats.
    Examples:
        '{"A": "#ff0000", "B": "#00ff00"}'
        'A:#ff0000,B:#00ff00'
    """
    if not colors:
        return None
    colors = colors.strip()
    if colors.startswith("{") and colors.endswith("}"):
        import json

        return json.loads(colors)
    # Simplified format: key:value,key:value
    result = {}
    for part in colors.split(","):
        part = part.strip()
        if ":" in part:
            key, value = part.split(":", 1)
            result[key.strip()] = value.strip()
    return result if result else None
