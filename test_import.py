import sys
import os

# Add the venv site-packages to sys.path explicitly for debugging
venv_path = os.path.join(os.path.dirname(__file__), '.venv', 'Lib', 'site-packages')
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)
    print(f"Manually added to sys.path: {venv_path}")

try:
    import google.generativeai
    print("Successfully imported google.generativeai")
    print(f"Using Python executable: {sys.executable}")
except ImportError as e:
    print(f"Failed to import google.generativeai: {e}")
    print(f"Using Python executable: {sys.executable}")
    print("sys.path:")
    for p in sys.path:
        print(f"- {p}")
