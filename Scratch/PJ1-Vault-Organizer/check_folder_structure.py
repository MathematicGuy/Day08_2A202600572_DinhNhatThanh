#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
check_folder_structure.py — Minimal script to establish Git Sandbox and print ASCII directory tree.
"""

import os
import sys
import subprocess
from datetime import datetime

# Ensure UTF-8 encoding is used for standard output/error, especially on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def setup_git_sandbox(vault_root: str):
    """Check for dirty tree, stash if needed, and checkout new sandbox branch."""
    print("=== [GIT SANDBOX SETUP] ===")
    
    # Verify git repository
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=vault_root, check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[WARNING] Not inside a git repository. Skipping sandbox branching.")
        return

    # Check for dirty changes
    status_res = subprocess.run(["git", "status", "--porcelain"], cwd=vault_root, capture_output=True, text=True, check=True)
    if status_res.stdout.strip():
        print("[SANDBOX] Workspace is dirty. Stashing changes to protect active drafts...")
        subprocess.run(["git", "stash", "save", "vault-organize: Pre-organize workspace snapshot", "-u"], cwd=vault_root, check=True)
        print("[SANDBOX] Active drafts stashed successfully.")

    # Create timestamped sandbox branch
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"vault-organize/sandbox-{timestamp}"
    print(f"[SANDBOX] Creating and checking out sandbox branch: {branch_name}...")
    subprocess.run(["git", "checkout", "-b", branch_name], cwd=vault_root, check=True)
    print(f"[SANDBOX] Now on branch: {branch_name}")


def print_ascii_tree(path: str, indent: str = ""):
    """Print a clean, minimal ASCII tree of files and folders."""
    if not os.path.exists(path):
        print(f"[ERROR] Path does not exist: {path}")
        return

    items = sorted(os.listdir(path))
    for item in items:
        # Skip hidden files/directories and common cache folders
        if item.startswith('.') or item in ("__pycache__", "node_modules", "venv", ".git"):
            continue
            
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            print(f"{indent}├── 📁 {item}")
            print_ascii_tree(item_path, indent + "│   ")
        else:
            print(f"{indent}├── 📄 {item}")


def main():
    # If a path argument is provided, use it, otherwise use current working directory
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Target Directory: {target_dir}\n")

    # 1. Setup git sandbox
    setup_git_sandbox(target_dir)

    # 2. Print ASCII tree structure
    print("\n=== [DIRECTORY LAYOUT TREE] ===")
    print(f"📁 {os.path.basename(target_dir)}")
    print_ascii_tree(target_dir)
    print("===============================\n")


if __name__ == "__main__":
    main()
