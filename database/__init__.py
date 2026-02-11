"""Database package initialisation.

Expose a single authoritative `DB_PATH` constant. In deployment the path
can be provided via the `DATABASE_PATH` environment variable. If the
environment variable is not set the package falls back to a repository
relative `database/main.db` path.
"""
import os

# Project base directory (one level above this package)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Allow override via environment variable for deployment (Render, etc.)
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'database', 'main.db'))

# Ensure the parent directory exists when package is imported
try:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
except Exception:
    pass
