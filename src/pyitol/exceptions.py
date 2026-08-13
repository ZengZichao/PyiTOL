"""PyiTOL custom exception hierarchy.

Provides structured exceptions for better error handling and bilingual error messages.
"""

from __future__ import annotations


class PyiTOLBaseError(Exception):
    """Base exception for all PyiTOL errors."""

    pass


# ---------------------------------------------------------------------------
# Tree / Topology
# ---------------------------------------------------------------------------


class TopologyError(PyiTOLBaseError):
    """Raised for tree topology errors (invalid tree structure, missing nodes)."""

    pass


class TreeParseError(TopologyError):
    """Raised when a tree file cannot be parsed."""

    pass


# ---------------------------------------------------------------------------
# Taxonomy / Metadata
# ---------------------------------------------------------------------------


class TaxonomyError(PyiTOLBaseError):
    """Raised for taxonomy data errors (invalid rank, missing taxa, inconsistent mapping)."""

    pass


class MetadataParseError(TaxonomyError):
    """Raised when a metadata/taxonomy file cannot be parsed."""

    pass


class TaxaNotFoundError(TaxonomyError):
    """Raised when taxa in metadata are not found in the tree."""

    pass


class NodeIDMismatchError(TaxonomyError):
    """Raised when node IDs in metadata do not match tree node names."""

    pass


# ---------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------


class TemplateError(PyiTOLBaseError):
    """Raised for template generation or validation errors."""

    pass


class TemplateValidationError(TemplateError):
    """Raised when template input validation fails."""

    pass


class SchemaValidationError(TemplateError):
    """Raised when a template schema fails structural validation."""

    pass


class TemplateTypeError(TemplateError):
    """Raised when an unsupported or unknown template type is requested."""

    pass


class InvalidColumnError(TemplateError):
    """Raised when a specified column does not exist in the data."""

    pass


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


class FileError(PyiTOLBaseError):
    """Base for file-related errors."""

    pass


class FileFormatError(FileError):
    """Raised when a file's format is not recognized or not supported."""

    pass


class FileTooLargeError(FileError):
    """Raised when a file exceeds the size limit."""

    pass


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


class DataError(PyiTOLBaseError):
    """Base for data-content errors."""

    pass


class MissingColumnError(DataError):
    """Raised when a required column is absent from the input data."""

    pass


class DataFormatError(DataError):
    """Raised when data content does not match the expected format."""

    pass


class UnsupportedFormatError(DataError):
    """Raised when the requested output format is not supported."""

    pass


class SpecialCharacterError(DataError):
    """Raised when node IDs or labels contain unsupported special characters."""

    pass


class SeparatorConflictError(DataError):
    """Raised when data content conflicts with the chosen separator."""

    pass


# ---------------------------------------------------------------------------
# iTOL API
# ---------------------------------------------------------------------------


class APIError(PyiTOLBaseError):
    """Raised for iTOL API communication errors."""

    pass


class APITransportError(APIError):
    """Raised for network/HTTP transport errors (connection, timeout, SSL)."""

    pass


class APIServiceError(APIError):
    """Raised for iTOL service-side errors (invalid response, rate limiting, maintenance)."""

    pass


class APIKeyError(APIServiceError):
    """Raised when API key is missing or invalid."""

    pass


class UploadError(APIServiceError):
    """Raised when tree upload to iTOL fails."""

    pass


class ExportError(APIServiceError):
    """Raised when tree export from iTOL fails."""

    pass


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


class ColorCodeError(PyiTOLBaseError):
    """Raised when an invalid color code is provided."""

    pass


class SessionError(PyiTOLBaseError):
    """Raised for session snapshot load/save errors."""

    pass


class ReplayError(SessionError):
    """Raised when session replay fails."""

    pass
