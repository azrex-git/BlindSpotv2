"""File system watcher for hot-reloading Agent Skills during local development.

Monitors SKILL.md files and invalidates or updates registry caches when skills are modified.
"""

from pathlib import Path
import threading
import time
from typing import Callable, Dict, List, Optional

from blindspot.skills.registry import SkillRegistry


class SkillWatcher:
    """Monitors skills directories and updates the SkillRegistry in real time upon file modifications."""

    def __init__(
        self,
        registry: SkillRegistry,
        paths: Optional[List[Path]] = None,
        poll_interval: float = 1.0,
        on_change: Optional[Callable[[Path], None]] = None,
    ) -> None:
        self.registry = registry
        self.paths = paths or registry.search_paths
        self.poll_interval = poll_interval
        self.on_change = on_change
        self._mtimes: Dict[Path, float] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _scan_mtimes(self) -> Dict[Path, float]:
        """Scan all SKILL.md files and record their modification timestamps."""
        mtimes: Dict[Path, float] = {}
        for base in self.paths:
            if not base.is_dir():
                continue
            for p in base.rglob("SKILL.md"):
                if p.is_file():
                    try:
                        mtimes[p.resolve()] = p.stat().st_mtime
                    except OSError:
                        pass
        return mtimes

    def check_once(self) -> List[Path]:
        """Check for changed, added, or deleted SKILL.md files and reload registry if changed."""
        current = self._scan_mtimes()
        changed: List[Path] = []

        # Check modifications and additions
        for p, mtime in current.items():
            if p not in self._mtimes or self._mtimes[p] != mtime:
                changed.append(p)

        # Check deletions
        for p in self._mtimes:
            if p not in current:
                changed.append(p)

        if changed:
            self._mtimes = current
            self.registry.load()
            if self.on_change:
                for p in changed:
                    self.on_change(p)

        return changed

    def start(self) -> None:
        """Start background polling thread."""
        if self._running:
            return
        self._running = True
        self._mtimes = self._scan_mtimes()

        def loop() -> None:
            while self._running:
                try:
                    self.check_once()
                except Exception:
                    pass
                time.sleep(self.poll_interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background polling thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
