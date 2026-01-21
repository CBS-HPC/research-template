"""
Streamlit RDA-DMP JSON editor module.

Exports:
- main(): run the Streamlit app
- cli():  run via a small CLI wrapper (streamlit run ...)
"""
from .app import main, cli

__all__ = ["main", "cli"]
