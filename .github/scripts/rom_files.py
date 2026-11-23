#!/usr/bin/env python3
"""Print rom/files.json: every file in rom/ (at a git ref) with its size, from `git ls-tree`.
Usage: rom_files.py [ref]   (default HEAD)"""
import json, subprocess, sys
ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
out = subprocess.run(["git", "ls-tree", "-r", "-l", ref, "rom/"], capture_output=True, text=True, check=True).stdout
files = []
for line in out.splitlines():
    meta, path = line.split("\t", 1)
    parts = meta.split()
    if parts[1] == "blob" and path != "rom/files.json":
        files.append({"path": path, "size": int(parts[3])})
print(json.dumps({"files": files}, indent=1, ensure_ascii=False))
