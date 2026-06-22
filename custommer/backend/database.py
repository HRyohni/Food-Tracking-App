import os
import sys

# Make the project root importable so `Ashared` resolves when running
# `uvicorn main:app` from inside this folder.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Re-export the shared engine / Base / session so all backends use ONE database.
from Ashared.database import Base, SessionLocal, engine, get_db  # noqa: E402,F401
