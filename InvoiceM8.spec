# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for InvoiceM8.

Produces a single windowed executable: dist/InvoiceM8.exe

Notes:
* CustomTkinter ships theme JSON + fonts as package data - collected below.
* pywin32 / Outlook COM needs its submodules named explicitly (they are
  imported lazily inside integrations/email_outlook.py so the analyser
  cannot see them).
* AI providers are called over plain REST (requests) - no vendor SDKs to bundle.
* The Graph / attachment libraries are OPTIONAL - only bundled if installed in
  the environment you build from. Install the full requirements.txt first for a
  build that supports every feature.
"""
import os

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []


def _bundle(pkg: str, optional: bool = False) -> None:
    """Add a package's data/binaries/submodules, skipping missing optionals."""
    if optional:
        try:
            __import__(pkg)
        except Exception:
            print(f"[InvoiceM8.spec] optional package not installed, skipping: {pkg}")
            return
    d, b, h = collect_all(pkg)
    datas.extend(d)
    binaries.extend(b)
    hiddenimports.extend(h)


# Required.
_bundle("customtkinter")

# Ship the changelog so the in-app About window can show it offline.
if os.path.exists("CHANGELOG.md"):
    datas.append(("CHANGELOG.md", "."))

# Outlook COM (pywin32) - lazily imported, so name the submodules.
hiddenimports += [
    "win32com", "win32com.client", "win32com.server",
    "pythoncom", "pywintypes", "win32timezone",
]

# Optional feature libraries - bundled only if present at build time.
for _pkg in ("msal", "pdfminer", "docx", "keyring.backends.Windows"):
    _bundle(_pkg, optional=True)

_icon = "assets/icon.ico" if os.path.exists("assets/icon.ico") else None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter.test", "test", "unittest", "pydoc_data"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Single-file build: pass binaries + datas straight into EXE, no COLLECT.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="InvoiceM8",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # windowed - no console pops up
    disable_windowed_traceback=False,
    icon=_icon,
)
