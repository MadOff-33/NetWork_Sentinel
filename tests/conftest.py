# Fichier : tests/conftest.py
# Rend la racine du depot importable (src/, server/) quel que soit
# le repertoire depuis lequel pytest est lance.
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
