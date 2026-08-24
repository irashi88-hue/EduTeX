"""
EduTeX Core Error Contract
Component: Core (COMP-CORE-001)
Contract: CC-003 (Error Contract)

Defines the canonical error types used across all EduTeX components.
All fatal errors SHALL be raised as EduTeXError subclasses.
"""

from __future__ import annotations


class EduTeXError(Exception):
    """Base class for all EduTeX framework errors."""


class ConfigurationError(EduTeXError):
    """Raised when configuration validation fails. (CFG-001)"""


class RegistryError(EduTeXError):
    """Raised when a registry operation fails. (REG-001)"""


class ResolverError(EduTeXError):
    """Raised when reference resolution fails. (RES-001)"""


class ActivationError(EduTeXError):
    """Raised when component activation fails. (ACT-001)"""


class KnowledgeError(EduTeXError):
    """Raised when Knowledge Model parsing or validation fails. (KNOW-001)"""


class ThemeError(EduTeXError):
    """Raised when theme processing fails. (THEME-001)"""


class LayoutError(EduTeXError):
    """Raised when layout processing fails. (LAYOUT-001)"""


class BuildError(EduTeXError):
    """Raised when the build stage fails. (BUILD-001)"""


class ExtensionError(EduTeXError):
    """Raised when an extension fails to load or validate. (EXT-001)"""
