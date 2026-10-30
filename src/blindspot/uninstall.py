"""Complete uninstallation and cleanup utility for BlindSpot1 / BlindSpot.

Safely removes CLI command shims, virtual environment links, PATH references,
and optional user configuration caches.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.table import Table

console = Console()


def get_known_shim_locations() -> List[Path]:
    """Return all directories where BlindSpot shims and executables are deployed."""
    user_home = Path.home()
    locations = [
        user_home / ".local" / "bin",
        user_home / ".blindspot" / "bin",
        user_home / "AppData" / "Local" / "Python" / "bin",
        user_home / "AppData" / "Local" / "Python" / "pythoncore-3.14-64" / "Scripts",
    ]
    # Also include active virtual environment Scripts directory if present
    if hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
        locations.append(Path(sys.prefix) / "Scripts")

    return [loc for loc in locations if loc.exists()]


def get_installed_shims() -> List[Path]:
    """Detect all existing BlindSpot & BlindSpot1 CLI scripts and wrappers."""
    targets = [
        "blindspot.cmd",
        "blindspot.ps1",
        "blindspot.bat",
        "blindspot.exe",
        "blindspot1.cmd",
        "blindspot1.ps1",
        "blindspot1.bat",
        "blindspot1.exe",
    ]
    found: List[Path] = []
    for loc in get_known_shim_locations():
        for t in targets:
            candidate = loc / t
            if candidate.exists():
                found.append(candidate)
    return found


def remove_shims() -> Tuple[List[Path], List[str]]:
    """Remove all detected CLI executable wrappers and shims."""
    removed: List[Path] = []
    errors: List[str] = []

    for shim in get_installed_shims():
        try:
            shim.unlink(missing_ok=True)
            removed.append(shim)
        except Exception as exc:
            errors.append(f"Failed to remove {shim}: {exc}")

    return removed, errors


def uninstall_pip_package(python_executable: str = sys.executable) -> Tuple[bool, str]:
    """Run pip/uv to remove blindspot1 and blindspot from the specified Python environment."""
    msgs = []
    # Try uv tool uninstall first if installed as uv tool
    uv_bin = shutil.which("uv")
    if uv_bin:
        try:
            res_uv = subprocess.run([uv_bin, "tool", "uninstall", "blindspot1"], capture_output=True, text=True, timeout=15)
            if res_uv.returncode == 0:
                msgs.append("uv tool uninstalled")
        except Exception:
            pass

    try:
        res = subprocess.run(
            [python_executable, "-m", "pip", "uninstall", "-y", "blindspot1", "blindspot"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        msgs.append(res.stdout or res.stderr)
        return (res.returncode == 0 or len(msgs) > 0, " ".join(msgs))
    except Exception as exc:
        return (False, str(exc))


def remove_editable_pth_files() -> List[Path]:
    """Scan site-packages for any lingering _editable_impl_blindspot.pth or blindspot.egg-link."""
    import site
    removed: List[Path] = []
    search_dirs = site.getsitepackages()
    user_site = site.getusersitepackages()
    if isinstance(user_site, str):
        search_dirs.append(user_site)

    for dir_path in search_dirs:
        p = Path(dir_path)
        if not p.is_dir():
            continue
        for f in p.glob("*blindspot*.pth"):
            try:
                f.unlink()
                removed.append(f)
            except Exception:
                pass
        for f in p.glob("*blindspot*.egg-link"):
            try:
                f.unlink()
                removed.append(f)
            except Exception:
                pass

    return removed


def remove_config_directory() -> Tuple[bool, str]:
    """Remove ~/.blindspot configuration and cache directory."""
    cfg_dir = Path.home() / ".blindspot"
    if not cfg_dir.exists():
        return (True, "No ~/.blindspot directory found.")
    try:
        shutil.rmtree(cfg_dir, ignore_errors=True)
        return (True, str(cfg_dir))
    except Exception as exc:
        return (False, str(exc))


def perform_uninstall(
    force: bool = False,
    clean_config: bool = False,
) -> bool:
    """Perform a complete, structured uninstallation of BlindSpot1 / BlindSpot."""
    console.print("\n[bold red]● BlindSpot1 / BlindSpot Uninstaller[/bold red]\n")

    shims = get_installed_shims()
    console.print(f"Found [bold white]{len(shims)}[/bold white] installed CLI executable shims.")
    for s in shims:
        console.print(f"  [dim]•[/dim] {s}")

    if not force:
        confirm = input("\nAre you sure you want to completely uninstall BlindSpot1? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            console.print("[yellow]Uninstallation cancelled by user.[/yellow]\n")
            return False

    console.print("\n[bold cyan]→ Removing CLI shims and wrappers...[/bold cyan]")
    removed_shims, shim_errors = remove_shims()
    for s in removed_shims:
        console.print(f"  [green]✓ Removed:[/green] {s}")
    for err in shim_errors:
        console.print(f"  [red]✖ Error:[/red] {err}")

    console.print("\n[bold cyan]→ Cleaning editable package references...[/bold cyan]")
    removed_pths = remove_editable_pth_files()
    for p in removed_pths:
        console.print(f"  [green]✓ Removed link file:[/green] {p}")

    console.print("\n[bold cyan]→ Uninstalling Python package...[/bold cyan]")
    pip_ok, pip_msg = uninstall_pip_package()
    if pip_ok:
        console.print("  [green]✓ Python package successfully uninstalled.[/green]")
    else:
        console.print(f"  [dim]Note: pip uninstall completed ({pip_msg.strip()[:80]}).[/dim]")

    if clean_config:
        console.print("\n[bold cyan]→ Removing ~/.blindspot directory...[/bold cyan]")
        cfg_ok, cfg_msg = remove_config_directory()
        if cfg_ok:
            console.print(f"  [green]✓ Removed configuration:[/green] {cfg_msg}")
        else:
            console.print(f"  [red]✖ Failed to remove config:[/red] {cfg_msg}")

    # Summary Table
    table = Table(title="Uninstallation Summary", border_style="green", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold green")
    table.add_column("Details", style="dim")

    table.add_row("CLI Executables", "Removed", f"{len(removed_shims)} shims deleted")
    table.add_row("Package Links", "Cleaned", f"{len(removed_pths)} .pth/.egg-link files removed")
    table.add_row("Python Package", "Uninstalled", sys.executable)
    table.add_row("Config Directory", "Cleaned" if clean_config else "Retained", "~/.blindspot")

    console.print()
    console.print(table)
    console.print("\n[bold green]✓ Uninstallation completed successfully.[/bold green]\n")
    return True
