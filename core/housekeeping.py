"""Retention for the on-disk attachment cache.

Every processed email leaves a folder of attachment bytes under
``ATTACHMENT_CACHE``. Nothing consumed those files after routing finished, so
without a sweep the cache grows for the lifetime of the install.

Two things are never deleted regardless of age: files referenced by an
unresolved error (the Error tab can still retry them) and files belonging to an
invoice still queued for a new-customer decision.
"""
from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from config import ATTACHMENT_CACHE

log = logging.getLogger(__name__)


def prune_attachment_cache(keep_days: int, protected: set[str] | None = None,
                           root: Path | None = None) -> int:
    """Delete cached attachment folders older than ``keep_days``.

    ``protected`` is a set of absolute file paths that must survive whatever
    their age. Returns the number of folders removed. Never raises: a cache
    sweep failing must not stop the watcher from polling.
    """
    root = root or ATTACHMENT_CACHE
    if keep_days <= 0 or not root.exists():
        return 0

    cutoff = time.time() - keep_days * 86400
    keep = {str(Path(p).resolve()) for p in (protected or set())}
    removed = 0

    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        try:
            if folder.stat().st_mtime >= cutoff:
                continue
            # A single protected file pins its whole message folder.
            if any(str(f.resolve()) in keep for f in folder.rglob("*") if f.is_file()):
                continue
            shutil.rmtree(folder)
            removed += 1
        except OSError as exc:
            log.warning("Could not prune cache folder %s: %s", folder, exc)
    if removed:
        log.info("Pruned %d cached attachment folder(s) older than %d days.",
                 removed, keep_days)
    return removed
