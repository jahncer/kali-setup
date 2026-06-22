#!/usr/bin/env python3
"""Download the newest GitHub release asset matching a regex.

Usage:
  gh_release_download.py OWNER/REPO REGEX DEST_DIR [--token TOKEN]

Behavior:
  - Queries GitHub's latest release API.
  - Selects the first asset whose name matches REGEX.
  - Downloads the asset into DEST_DIR.
  - Extracts .zip, .tar.gz, .tgz, .gz where appropriate.
  - Leaves the original downloaded asset in DEST_DIR/.downloads.

This uses only the Python standard library so it works on a fresh Kali install.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def request_json(url: str, token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "jahncer-kali-ctf-ansible-role",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url: str, dest: Path, token: str | None) -> None:
    headers = {"User-Agent": "jahncer-kali-ctf-ansible-role"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def chmod_executable(path: Path) -> None:
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


def safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> None:
    dest_resolved = dest.resolve()
    for member in tf.getmembers():
        target = (dest / member.name).resolve()
        if not str(target).startswith(str(dest_resolved)):
            raise RuntimeError(f"Unsafe tar member path: {member.name}")
    tf.extractall(dest)


def extract_asset(asset_path: Path, dest: Path) -> None:
    name = asset_path.name
    lower = name.lower()
    if lower.endswith(".zip"):
        with zipfile.ZipFile(asset_path) as zf:
            zf.extractall(dest)
    elif lower.endswith(".tar.gz") or lower.endswith(".tgz"):
        with tarfile.open(asset_path, "r:gz") as tf:
            safe_extract_tar(tf, dest)
    elif lower.endswith(".tar.xz"):
        with tarfile.open(asset_path, "r:xz") as tf:
            safe_extract_tar(tf, dest)
    elif lower.endswith(".gz"):
        # Single-file gzip, e.g. chisel linux binary.
        out_name = name[:-3]
        out_path = dest / out_name
        with gzip.open(asset_path, "rb") as inp, out_path.open("wb") as out:
            shutil.copyfileobj(inp, out)
        chmod_executable(out_path)
    else:
        copied = dest / name
        if copied != asset_path:
            shutil.copy2(asset_path, copied)
        chmod_executable(copied)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="OWNER/REPO")
    parser.add_argument("regex", help="Regex to match release asset name")
    parser.add_argument("dest", help="Destination directory")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = parser.parse_args()

    if "/" not in args.repo:
        print("repo must be OWNER/REPO", file=sys.stderr)
        return 2

    owner_repo = args.repo.strip()
    pattern = re.compile(args.regex)
    dest = Path(args.dest).expanduser().resolve()
    downloads = dest / ".downloads"
    dest.mkdir(parents=True, exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)

    release_url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
    release = request_json(release_url, args.token)
    assets = release.get("assets", [])
    matches = [a for a in assets if pattern.search(a.get("name", ""))]
    if not matches:
        print(f"No asset in {owner_repo} latest release matched regex: {args.regex}", file=sys.stderr)
        print("Available assets:", file=sys.stderr)
        for asset in assets:
            print(f"  - {asset.get('name')}", file=sys.stderr)
        return 1

    asset = matches[0]
    asset_name = asset["name"]
    asset_url = asset["browser_download_url"]
    asset_path = downloads / asset_name

    if not asset_path.exists() or asset_path.stat().st_size == 0:
        print(f"Downloading {owner_repo} asset {asset_name}")
        download(asset_url, asset_path, args.token)
    else:
        print(f"Already downloaded {asset_path}")

    extract_asset(asset_path, dest)

    # Mark files in dest root executable if they look like binaries/scripts.
    for child in dest.iterdir():
        if child.is_file() and child.name != asset_path.name:
            if not child.suffix or child.suffix in {".sh", ".py", ".pl", ".rb"}:
                chmod_executable(child)

    print(f"Installed {asset_name} into {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
