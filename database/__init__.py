"""Database package initialisation.

Expose a single authoritative `DB_PATH` constant so other modules
can import the absolute path to the SQLite database file.
"""
import os

# Absolute path to the project's database file (Windows path provided by user)
DB_PATH = r"C:\Users\yshel\Downloads\kumbh_smart_seva_OG\kumbh_smart_seva_v2\database\main.db"

# Ensure directory exists when package is imported
try:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
except Exception:
    pass
