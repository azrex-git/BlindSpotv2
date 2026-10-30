#!/usr/bin/env python3
"""Standalone uninstallation script for BlindSpot1 / BlindSpot."""

import os
import sys
from pathlib import Path

# Add src to sys.path so it works even if not installed
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from blindspot.uninstall import perform_uninstall
except ImportError:
    # Fallback minimal cleaner
    print("Direct import failed, using basic cleanup...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "blindspot"])
    sys.exit(0)

if __name__ == "__main__":
    force = "-y" in sys.argv or "--force" in sys.argv
    clean_config = "--clean-config" in sys.argv
    perform_uninstall(force=force, clean_config=clean_config)
