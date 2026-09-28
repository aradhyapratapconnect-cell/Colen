"""Colen - A beautiful Jarvis-like CLI assistant."""

__version__ = "0.1.0"
__author__ = "Colen Team"
__description__ = "A beautiful Jarvis-like CLI assistant"

# Load the .env file before any submodule is imported: colen.assistant and
# colen.speech read their configuration from environment variables at import
# time.  Real environment variables always take precedence over .env values.
from colen.env import load_env

load_env()

from colen.cli import main

__all__ = ["main"]