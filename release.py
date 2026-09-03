"""Build dist/InvoiceM8.exe and (optionally) publish it as a GitHub release.

One system, three ways in - ``build.bat`` and ``release.bat`` are just thin
wrappers around this:

    python release.py                # test -> build -> publish release v<APP_VERSION>
    python release.py --build-only    # test -> build, then stop (no gh CLI needed)
    python release.py --skip-build    # test -> publish an exe that is already built
    python release.py --yes           # skip the "Publish? [y/N]" confirmation

The permanent download URL - also what installed builds poll for updates - is:

    https://github.com/<owner>/<repo>/releases/latest/download/InvoiceM8.exe

Bump version.py, run release.bat, done. Publishing requires the GitHub CLI:
    winget install GitHub.cli  &&  gh auth login
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from core.updater import GITHUB_REPO
from version import APP_VERSION

EXE = Path("dist/InvoiceM8.exe")
SPEC = "InvoiceM8.spec"


def gh(*args: str) -> subprocess.CompletedProcess:
    """Run a gh subcommand, capturing output."""
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def build() -> bool:
    """Clean previous output and build the one-file exe with PyInstaller.

    Invoked as ``python -m PyInstaller`` (not the bare ``pyinstaller`` shim):
    this machine has more than one Python on PATH and the shim can resolve to
    the wrong interpreter, silently building against the wrong site-packages.
    Build from a venv with the full requirements.txt installed to bake in the
    AI / Graph / attachment features (the spec skips any that are missing).
    """
    print("  Building dist/InvoiceM8.exe ...")
    for stale in ("build", "dist"):
        shutil.rmtree(stale, ignore_errors=True)
    if subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                       "--upgrade", "pyinstaller"]).returncode != 0:
        print("  Could not install PyInstaller.")
        return False
    if subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm",
                       "--clean", SPEC]).returncode != 0:
        print("  BUILD FAILED.")
        return False
    print(f"  Built {EXE}")
    return True


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


def run_tests() -> bool:
    """Run the unit suite; a failing build must never be published."""
    print("  Running tests...")
    result = subprocess.run([sys.executable, "-m", "unittest", "discover",
                             "-s", "tests"], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:] or result.stderr[-2000:])
        return False
    print("  Tests passed.")
    return True


def main() -> int:
    """Test, build, then publish - subject to the CLI flags. Returns an exit code.

    ``--build-only`` stops after a successful build; ``--skip-build`` publishes
    the exe already in ``dist/``. Tests always run first either way. The publish
    step prints what is about to ship and waits for a Y unless ``--yes`` is set.
    """
    args = set(sys.argv[1:])
    unknown = args - {"--build-only", "--skip-build", "--yes"}
    if unknown:
        # Fail loudly rather than let a typo'd flag fall through to a publish.
        print(f"  Unknown option(s): {' '.join(sorted(unknown))}")
        print("  Usage: release.py [--build-only | --skip-build] [--yes]")
        return 2
    build_only = "--build-only" in args
    skip_build = "--skip-build" in args
    assume_yes = "--yes" in args

    if not run_tests():
        print("  TESTS FAILED - stopping.")
        return 1

    if not skip_build and not build():
        return 1
    if not EXE.exists():
        print(f"  {EXE} not found"
              + (" - drop --skip-build to build it." if skip_build else "."))
        return 1
    if build_only:
        print(f"\n  Done. {EXE} is ready to run.\n"
              f"  (settings + database live in %LOCALAPPDATA%\\InvoiceM8)\n")
        return 0

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
    exists = gh("release", "view", tag).returncode == 0

    # Publishing is outward-facing and marks this build "Latest" - every
    # installed client updates to it. Confirm what is about to ship first.
    stat = EXE.stat()
    print(f"\n  {'UPDATE' if exists else 'PUBLISH'} release {tag} on {slug} "
          f"(GitHub marks it 'Latest').")
    print(f"    asset : {EXE}  ({stat.st_size / 1_048_576:.1f} MB, built "
          f"{datetime.fromtimestamp(stat.st_mtime):%Y-%m-%d %H:%M})")
    print(f"    notes : first line - {changelog(APP_VERSION).splitlines()[0][:70]}")
    if not assume_yes and input("  Proceed? [y/N] ").strip().lower() not in ("y", "yes"):
        print("  Aborted - nothing published.")
        return 1

    notes = (
        f"## What's new\n\n{changelog(APP_VERSION)}\n\n"
        "---\n\n"
        "Download `InvoiceM8.exe` and run it - no install, no admin. It is "
        "unsigned, so Windows SmartScreen shows \"Windows protected your PC\": "
        "click **More info** then **Run anyway**. Existing installs update "
        "themselves from this release."
    )

    if exists:
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
