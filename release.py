"""Publish dist/InvoiceM8.exe as a GitHub release (tag = v<APP_VERSION>).

The permanent download URL - also what installed builds poll for updates - is:

    https://github.com/<owner>/<repo>/releases/latest/download/InvoiceM8.exe

Bump version.py, run release.bat, done. Requires the GitHub CLI:
    winget install GitHub.cli  &&  gh auth login
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.updater import GITHUB_REPO
from version import APP_VERSION

EXE = Path("dist/InvoiceM8.exe")


def gh(*args: str) -> subprocess.CompletedProcess:
    """Run a gh subcommand, capturing output."""
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def changelog(tag: str) -> str:
    """Commit subjects since the previous tag, as markdown bullets."""
    prev = subprocess.run(["git", "describe", "--tags", "--abbrev=0", f"{tag}^"],
                          capture_output=True, text=True)
    if prev.returncode != 0 or not prev.stdout.strip():
        return "- First release."
    span = f"{prev.stdout.strip()}..{tag}"
    log = subprocess.run(["git", "log", span, "--no-merges", "--pretty=%s"],
                         capture_output=True, text=True)
    lines = [l.strip() for l in log.stdout.splitlines() if l.strip()]
    return "\n".join("- " + l for l in lines[:20]) or "- Maintenance release."


def main() -> int:
    if not EXE.exists():
        print(f"  {EXE} not found - build first (build.bat / PyInstaller).")
        return 1
    if gh("--version").returncode != 0:
        print("  GitHub CLI not found:  winget install GitHub.cli")
        return 1
    if gh("auth", "status").returncode != 0:
        print("  Not logged in:  gh auth login")
        return 1

    slug = gh("repo", "view", "--json", "nameWithOwner",
              "-q", ".nameWithOwner").stdout.strip()
    if slug.lower() != GITHUB_REPO.lower():
        print(f"  Remote is {slug} but core/updater.py checks {GITHUB_REPO}.\n"
              f"  Fix GITHUB_REPO before releasing or clients go stale.")
        return 1

    tag = f"v{APP_VERSION}"
    notes = (
        f"## What's new\n\n{changelog(tag)}\n\n"
        "---\n\n"
        "Download `InvoiceM8.exe` and run it - no install, no admin. It is "
        "unsigned, so Windows SmartScreen shows \"Windows protected your PC\": "
        "click **More info** then **Run anyway**. Existing installs update "
        "themselves from this release."
    )

    if gh("release", "view", tag).returncode == 0:
        print(f"  Release {tag} exists - updating asset + notes")
        r1 = gh("release", "upload", tag, str(EXE), "--clobber")
        r2 = gh("release", "edit", tag, "--notes", notes)
        ok = r1.returncode == 0 and r2.returncode == 0
        if not ok:
            print("  " + (r1.stderr.strip() or r2.stderr.strip()))
    else:
        r = gh("release", "create", tag, str(EXE),
               "--title", f"InvoiceM8 {tag}", "--notes", notes)
        ok = r.returncode == 0
        print("  " + (f"Created release {tag}" if ok else r.stderr.strip()))

    if ok:
        print(f"\n  Permanent link:\n"
              f"  https://github.com/{slug}/releases/latest/download/InvoiceM8.exe\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
