#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v ludus >/dev/null 2>&1; then
  echo "[-] ludus CLI not found. Run this on the Ludus server as the Ludus user that owns the range." >&2
  exit 1
fi

if command -v ansible-galaxy >/dev/null 2>&1; then
  ansible-galaxy collection install -r requirements.yml
else
  echo "[!] ansible-galaxy not found; skipping collection install." >&2
fi

ludus ansible role add ./roles/jahncer.kali_ctf
ludus ansible roles list

echo "[+] Role added. Add roles: [jahncer.kali_ctf] to your Kali VM and run:"
echo "    ludus range deploy -t user-defined-roles --limit '*-kali' --only-roles jahncer.kali_ctf"
