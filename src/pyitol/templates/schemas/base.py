"""Base template schema definitions for all iTOL v7 visualization types."""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Callable

from pyitol.exceptions import TemplateTypeError

SEPARATOR_MAP = {
    "TAB": "\t",
    "SPACE": " ",
    "COMMA": ",",
}

SEPARATOR_REVERSE = {v: k for k, v in SEPARATOR_MAP.items()}

# ---------------------------------------------------------------------------
# Template registration system (Plugin architecture for 10.1)
# ---------------------------------------------------------------------------
# New template types can be registered via @register_template decorator.
# This eliminates the need to manually update SCHEMA_MAP, TEMPLATE_TYPE_HEADER,
# REQUIRED_COLUMNS, and NO_LABEL_COLOR_TYPES in multiple files.
# ---------------------------------------------------------------------------


class TemplateRegistry:
    """Central registry for template schema types."""

    def __init__(self) -> None:
        self._registry: dict[str, dict] = {}
        self._schema_map: dict[str, type] = {}
        self._type_header: dict[str, str] = {}
        self._required_columns: dict[str, list[str]] = {}
        self._no_label_color_types: set[str] = set()

    def register(
        self,
        type_name: str,
        cls: type,
        header: str,
        required_columns: list[str] | None = None,
        no_label_color: bool = False,
        aliases: list[str] | None = None,
    ) -> None:
        """Register a template type."""
        if type_name in self._registry:
            warnings.warn(
                f"Template type '{type_name}' is being re-registered. "
                f"Previous class: {self._registry[type_name]['class'].__name__}, "
                f"New class: {cls.__name__}",
                UserWarning,
                stacklevel=3,
            )
        self._registry[type_name] = {
            "class": cls,
            "header": header,
            "required_columns": required_columns or [],
            "no_label_color": no_label_color,
        }
        all_names = [type_name] + (aliases or [])
        for name in all_names:
            self._schema_map[name] = cls
            self._type_header[name] = header
            if required_columns:
                self._required_columns[name] = required_columns
            if no_label_color:
                self._no_label_color_types.add(name)

    def unregister(self, type_name: str) -> None:
        """Unregister a template type and its aliases."""
        entry = self._registry.pop(type_name, None)
        if entry is None:
            return
        aliases_to_remove = []
        for alias, cls in list(self._schema_map.items()):
            if cls is entry["class"]:
                aliases_to_remove.append(alias)
        for alias in aliases_to_remove:
            self._schema_map.pop(alias, None)
            self._type_header.pop(alias, None)
            self._required_columns.pop(alias, None)
            self._no_label_color_types.discard(alias)

    def get(self, type_name: str) -> type | None:
        """Return schema class by type name."""
        return self._schema_map.get(type_name)

    def get_header(self, type_name: str) -> str | None:
        """Return header string by type name."""
        return self._type_header.get(type_name)

    def get_required_columns(self, type_name: str) -> list[str]:
        """Return required columns list by type name."""
        return self._required_columns.get(type_name, [])

    def is_no_label_color(self, type_name: str) -> bool:
        """Return whether type uses no label/color."""
        return type_name in self._no_label_color_types

    def list_types(self) -> list[str]:
        """Return all registered type names."""
        return list(self._registry.keys())

    @property
    def schema_map(self) -> dict[str, type]:
        """Read-only view of schema map."""
        return dict(self._schema_map)

    @property
    def type_header(self) -> dict[str, str]:
        """Read-only view of type header map."""
        return dict(self._type_header)

    @property
    def required_columns(self) -> dict[str, list[str]]:
        """Read-only view of required columns map."""
        return dict(self._required_columns)

    @property
    def no_label_color_types(self) -> set[str]:
        """Read-only view of no-label-color types."""
        return set(self._no_label_color_types)


default_registry = TemplateRegistry()


class _SchemaMapProxy(dict):
    """Dict proxy reading from default_registry.schema_map."""

    def __getitem__(self, key: str) -> object:
        try:
            return super().__getitem__(key)
        except KeyError:
            return default_registry.schema_map[key]

    def __contains__(self, key: object) -> bool:
        return super().__contains__(key) or key in default_registry.schema_map

    def get(self, key: str, default: object | None = None) -> object | None:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> set[str]:  # type: ignore[override]
        return set(super().keys()) | set(default_registry.schema_map.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def items(self) -> Iterator[tuple[str, object]]:  # type: ignore[override]
        for k in self.keys():
            yield k, self[k]

    def values(self) -> Iterator[object]:  # type: ignore[override]
        for k in self.keys():
            yield self[k]

    def __len__(self) -> int:
        return len(self.keys())


class _TypeHeaderProxy(dict):
    """Dict proxy reading from default_registry.type_header."""

    def __getitem__(self, key: str) -> object:
        try:
            return super().__getitem__(key)
        except KeyError:
            return default_registry.type_header[key]

    def __contains__(self, key: object) -> bool:
        return super().__contains__(key) or key in default_registry.type_header

    def get(self, key: str, default: object | None = None) -> object | None:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> set[str]:  # type: ignore[override]
        return set(super().keys()) | set(default_registry.type_header.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def items(self) -> Iterator[tuple[str, object]]:  # type: ignore[override]
        for k in self.keys():
            yield k, self[k]

    def values(self) -> Iterator[object]:  # type: ignore[override]
        for k in self.keys():
            yield self[k]

    def __len__(self) -> int:
        return len(self.keys())


class _RequiredColumnsProxy(dict):
    """Dict proxy reading from default_registry.required_columns."""

    def __getitem__(self, key: str) -> object:
        try:
            return super().__getitem__(key)
        except KeyError:
            return default_registry.required_columns[key]

    def __contains__(self, key: object) -> bool:
        return super().__contains__(key) or key in default_registry.required_columns

    def get(self, key: str, default: object | None = None) -> object | None:
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> set[str]:  # type: ignore[override]
        return set(super().keys()) | set(default_registry.required_columns.keys())

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def items(self) -> Iterator[tuple[str, object]]:  # type: ignore[override]
        for k in self.keys():
            yield k, self[k]

    def values(self) -> Iterator[object]:  # type: ignore[override]
        for k in self.keys():
            yield self[k]

    def __len__(self) -> int:
        return len(self.keys())


class _NoLabelColorProxy:
    """Set-like proxy reading from default_registry.no_label_color_types."""

    def __init__(self) -> None:
        self._data: set[str] = set()

    def __contains__(self, key: object) -> bool:
        return key in self._data or key in default_registry.no_label_color_types

    def add(self, item: str) -> None:
        self._data.add(item)

    def discard(self, item: str) -> None:
        self._data.discard(item)

    def remove(self, item: str) -> None:
        self._data.remove(item)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data | default_registry.no_label_color_types)

    def __len__(self) -> int:
        return len(self._data | default_registry.no_label_color_types)

    def __bool__(self) -> bool:
        return bool(self._data) or bool(default_registry.no_label_color_types)


# Auto-populated lookup tables (replaces hard-coded mappings)
# These are backward-compatible proxies that read from default_registry
TEMPLATE_TYPE_HEADER: dict[str, str] = _TypeHeaderProxy()
NO_LABEL_COLOR_TYPES = _NoLabelColorProxy()
REQUIRED_COLUMNS: dict[str, list[str]] = _RequiredColumnsProxy()
SCHEMA_MAP: dict[str, type] = _SchemaMapProxy()


def register_template(
    type_name: str,
    header: str,
    required_columns: list[str] | None = None,
    no_label_color: bool = False,
    aliases: list[str] | None = None,
) -> Callable[[type], type]:
    """Register a template type with the global registry.

    Usage:
        @register_template(
            type_name='my_dataset',
            header='DATASET_MYDATASET',
            required_columns=['id', 'value'],
            aliases=['mydata'],
        )
        class MyDatasetSchema(TemplateSchema):
            ...

    This automatically populates:
        - SCHEMA_MAP[type_name] = cls
        - TEMPLATE_TYPE_HEADER[type_name] = header
        - REQUIRED_COLUMNS[type_name] = required_columns
        - NO_LABEL_COLOR_TYPES (if no_label_color=True)
        - All aliases are also registered.
    """

    def decorator(cls: type) -> type:
        default_registry.register(
            type_name=type_name,
            cls=cls,
            header=header,
            required_columns=required_columns,
            no_label_color=no_label_color,
            aliases=aliases,
        )
        # Also populate the legacy lookup tables for backward compatibility
        all_names = [type_name] + (aliases or [])
        for name in all_names:
            SCHEMA_MAP[name] = cls
            TEMPLATE_TYPE_HEADER[name] = header
            if required_columns:
                REQUIRED_COLUMNS[name] = required_columns
            if no_label_color:
                NO_LABEL_COLOR_TYPES.add(name)
        return cls

    return decorator


def get_registered_types() -> dict[str, dict]:
    """Return a read-only view of the template registry."""
    return dict(default_registry._registry)


@dataclass
class LegendConfig:
    """iTOL v7 LEGEND section configuration."""

    title: str | None = None
    position_x: str | None = None
    position_y: str | None = None
    horizontal: str | None = None
    shapes: list[str] | None = None
    colors: list[str] | None = None
    labels: list[str] | None = None
    shape_scales: list[str] | None = None

    def is_empty(self) -> bool:
        return all(
            v is None or v == "" or v == []
            for v in [
                self.title,
                self.position_x,
                self.position_y,
                self.horizontal,
                self.shapes,
                self.colors,
                self.labels,
                self.shape_scales,
            ]
        )

    def get_lines(self, sep: str = "\t") -> list[str]:
        """Generate LEGEND section lines."""
        lines = []
        if self.title is not None:
            lines.append(f"LEGEND_TITLE{sep}{self.title}")
        if self.position_x is not None:
            lines.append(f"LEGEND_POSITION_X{sep}{self.position_x}")
        if self.position_y is not None:
            lines.append(f"LEGEND_POSITION_Y{sep}{self.position_y}")
        if self.horizontal is not None:
            lines.append(f"LEGEND_HORIZONTAL{sep}{self.horizontal}")
        if self.shapes:
            lines.append(f"LEGEND_SHAPES{sep}{sep.join(str(s) for s in self.shapes)}")
        if self.colors:
            lines.append(f"LEGEND_COLORS{sep}{sep.join(str(c) for c in self.colors)}")
        if self.labels:
            lines.append(f"LEGEND_LABELS{sep}{sep.join(str(label) for label in self.labels)}")
        if self.shape_scales:
            lines.append(f"LEGEND_SHAPE_SCALES{sep}{sep.join(str(s) for s in self.shape_scales)}")
        return lines

    @staticmethod
    def auto_position(n_items: int = 5, position: str = "bottom-right") -> tuple[str, str]:
        """Calculate legend position to avoid tree overlap.

        Args:
            n_items: Number of legend items (affects height estimation)
            position: Preferred position - 'bottom-right', 'top-right', 'bottom-left', 'top-left'

        Returns:
            (x, y) tuple of position percentages
        """
        # iTOL coordinates: 0,0 = bottom-left, 100,100 = top-right
        # Tree is typically centered, so corners are safe
        positions = {
            "bottom-right": ("85", str(max(5, 15 - n_items))),
            "top-right": ("85", "90"),
            "bottom-left": ("5", str(max(5, 15 - n_items))),
            "top-left": ("5", "90"),
        }
        return positions.get(position, positions["bottom-right"])


@dataclass
class TemplateSchema:
    """Base class for template schemas."""

    dataset_type: str = ""
    label: str = ""
    color: str = "#ff0000"
    separator: str = "TAB"  # TAB, SPACE, or COMMA
    columns: list[str] = field(default_factory=list)
    data_rows: list[dict] = field(default_factory=list)
    parameters: dict = field(default_factory=dict)
    legend: LegendConfig = field(default_factory=LegendConfig)

    def __post_init__(self) -> None:
        if self.separator not in SEPARATOR_MAP:
            self.separator = "TAB"

    def get_header_line(self) -> str:
        header = TEMPLATE_TYPE_HEADER.get(self.dataset_type, self.dataset_type.upper())
        return header

    def get_separator_char(self) -> str:
        return SEPARATOR_MAP.get(self.separator, "\t")

    def uses_label_color(self) -> bool:
        return self.dataset_type not in NO_LABEL_COLOR_TYPES

    def validate(self) -> list[str]:
        """Validate data against schema. Returns list of error messages."""
        errors = []
        req_cols = REQUIRED_COLUMNS.get(self.dataset_type, [])
        if self.columns:
            for rc in req_cols:
                if rc not in self.columns:
                    errors.append(f"Missing required column: {rc}")
        for i, row in enumerate(self.data_rows):
            for rc in req_cols:
                # Handle None explicitly (treated as missing, same as '').
                if rc not in row or row[rc] == "" or row[rc] is None:
                    errors.append(f"Row {i + 1}: missing required field '{rc}'")
        return errors

    def get_parameter_lines(self) -> list[str]:
        """Generate parameter lines in iTOL v7 format."""
        sep = self.get_separator_char()
        lines = []

        # Always output DATASET_LABEL and COLOR for dataset types that use them
        if self.uses_label_color():
            if self.label:
                lines.append(f"DATASET_LABEL{sep}{self.label}")
            if self.color:
                lines.append(f"COLOR{sep}{self.color}")

        # Output other parameters
        for key, value in self.parameters.items():
            if key.upper() in {"DATASET_LABEL", "COLOR", "SEPARATOR"}:
                continue
            lines.append(f"{key}{sep}{value}")

        return lines


def create_schema(type_name: str, **kwargs: object) -> TemplateSchema:
    """Create a schema instance by type name."""
    schema_cls = SCHEMA_MAP.get(type_name)
    if schema_cls is None:
        raise TemplateTypeError(
            f"Unknown template type: {type_name}. Available types: {sorted(set(SCHEMA_MAP.keys()))}"
        )
    return schema_cls(**kwargs)


# ---------------------------------------------------------------------------
# Import schema classes from categorized submodules.
# These imports trigger @register_template decorators, auto-populating the
# global lookup tables (SCHEMA_MAP, TEMPLATE_TYPE_HEADER, etc.).
#
# P1-xx: Previously this registration relied solely on `templates.presets`
# being imported as a side effect, which made SCHEMA_MAP empty whenever
# `generator.py` (or tests) imported this module in isolation. Importing the
# schema submodules directly here decouples registration from import order.
# ---------------------------------------------------------------------------
from . import (  # noqa: E402, I001
    annotations as _schema_annotations,  # noqa: F401
    datasets_advanced,  # noqa: F401
    datasets_simple,  # noqa: F401
    tree_structure,  # noqa: F401
)
