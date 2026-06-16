#!/usr/bin/env python3
"""
dspng 打包脚本

用法:
  uv run scripts/build.py          # 默认打包 Qt 版本
  uv run scripts/build.py qt       # 同上
  uv run scripts/build.py clean    # 清理构建产物
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DSPNG = PROJECT_ROOT / "src" / "dspng"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "tmp" / "build"


def run(cmd: list[str]) -> int:
    exe = shutil.which(cmd[0])
    if exe:
        cmd = [exe] + cmd[1:]
    env = dict(os.environ)
    return subprocess.run(cmd, cwd=PROJECT_ROOT, env=env).returncode


def ensure_deps():
    """Ensure PyInstaller is available."""
    try:
        subprocess.run(
            ["uv", "run", "pyinstaller", "--version"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError, FileNotFoundError:
        print("> Installing pyinstaller ...")
        run(["uv", "add", "--dev", "pyinstaller"])


def build_qt() -> int:
    """Build Qt version into a standalone exe/binary."""
    ensure_deps()

    print("\n=== Building dspng (PyInstaller) ===\n")

    icon = PROJECT_ROOT / "icon.ico"
    sep = ";" if sys.platform == "win32" else ":"
    suffix = ".exe" if sys.platform == "win32" else ""

    cmd = [
        "uv",
        "run",
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name",
        "dspng",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--clean",
        f"--add-data={icon}{sep}.",
        f"--add-data={PROJECT_ROOT / 'locales'}{sep}locales",
        f"--add-data={PROJECT_ROOT / 'icons'}{sep}icons",
        str(SRC_DSPNG / "main.py"),
    ]
    if icon.exists():
        cmd.insert(-1, f"--icon={icon}")

    rc = run(cmd)

    if rc == 0:
        exe = DIST_DIR / f"dspng{suffix}"
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"\n[OK] Built: {exe}  ({size_mb:.1f} MB)")
    else:
        print("\n[FAIL] Build failed.")

    return rc


def clean() -> int:
    """Remove build artifacts."""
    for d in [DIST_DIR, BUILD_DIR, PROJECT_ROOT / "dspng.spec"]:
        if d.is_dir():
            print(f"  Removing {d.relative_to(PROJECT_ROOT)}")
            shutil.rmtree(d, ignore_errors=True)
        elif d.is_file():
            print(f"  Removing {d.relative_to(PROJECT_ROOT)}")
            d.unlink(missing_ok=True)
    return 0


TARGETS = {
    "qt": build_qt,
    "clean": clean,
}


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "qt"
    fn = TARGETS.get(target)
    if fn is None:
        print(f"Unknown target: {target}")
        print(f"Available: {', '.join(TARGETS)}")
        return 1
    return fn()


if __name__ == "__main__":
    sys.exit(main())
