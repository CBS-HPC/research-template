"""Compatibility imports.

This module keeps the refactor low-risk by preserving the original dependency
on `..common` (PROJECT_ROOT, read_toml, write_toml, split_multi).

If you move this package somewhere else, adjust these imports accordingly.
"""

from ...common import PROJECT_ROOT, read_toml, write_toml, split_multi  # type: ignore
