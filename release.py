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


def changelog(version: str) -> str:
    """The CHANGELOG.md section for this version, verbatim.

    CHANGELOG.md is the single source of truth (it is also bundled into the
    exe for the in-app About window). We don't derive notes from git tags -
    releases are tagged by `gh release create`, so the tag does not exist
    locally when this runs.
    """
    try:
        text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        return "- See the commit history."

    out: list[str] = []
    capturing = False
    for line in text.splitlines():
        if line.startswith("## "):
            if capturing:
                break
            capturing = line[3:].strip() == version
            continue
        if capturing and (line.strip() or out):
            out.append(line.rstrip())
    body = "\n".join(out).strip()
    return body or f"- Release {version}. See CHANGELOG.md for details."


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
