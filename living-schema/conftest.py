"""
Conftest — makes living-schema modules importable.

Since the directory name 'living-schema' has a dash, it can't be a Python package
name. Instead we add this directory to sys.path and import modules directly.
"""
import sys
import os

# Add the living-schema directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
