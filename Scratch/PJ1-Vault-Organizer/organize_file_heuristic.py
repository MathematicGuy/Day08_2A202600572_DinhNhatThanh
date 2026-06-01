#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
organize_file_heuristic.py — Simple keyword heuristic script to organize notes into the PARA taxonomy.
"""

import os
import sys
import shutil

# Ensure UTF-8 encoding is used for standard output/error, especially on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Keyword rules mapping to PARA directories
PARA_KEYWORDS = {
    "1_PROJECTS": ["deadline", "goal", "milestone", "active project", "lab assignment", "deliverable"],
    "2_ACTIONS": ["todo", "task", "gym", "cv", "resume", "driving test", "driving license", "buy", "actions"],
    "3_RESOURCES": ["nlp", "rag", "llm", "ai", "machine learning", "deep learning", "calculus", "vector", "aws", "cloud"],
    "4_ARCHIVES": ["final exam", "aio2024", "archive", "old", "3rd year", "zalo_ai", "midterm"]
}

def match_para_folder(filename: str, content: str) -> str:
    """Check filename and content against keywords. Returns categorized PARA folder name."""
    norm_text = f"{filename.lower()} {content.lower()}"
    
    for folder, keywords in PARA_KEYWORDS.items():
        for keyword in keywords:
            if keyword in norm_text:
                return folder
    return "3_RESOURCES" # Default fallback folder


def run_heuristic_organizer(target_dir: str):
    print("=== [HEURISTIC NOTE CLASSIFIER] ===")
    if not os.path.exists(target_dir):
        print(f"[ERROR] Directory {target_dir} does not exist!")
        return

    moved_count = 0

    # Scan target directory for unorganized loose markdown notes
    for item in sorted(os.listdir(target_dir)):
        item_path = os.path.join(target_dir, item)
        if os.path.isdir(item_path) or not item.lower().endswith(".md"):
            continue

        # Skip readme
        if item.lower() == "readme.md":
            continue

        # Read content preview to check keyword matching
        content = ""
        try:
            with open(item_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(1500)
        except Exception as e:
            print(f"[WARNING] Could not read {item}: {e}")

        # Classify note
        para_folder = match_para_folder(item, content)
        dest_folder = os.path.join(target_dir, para_folder)
        os.makedirs(dest_folder, exist_ok=True)

        # Move the note
        dst = os.path.join(dest_folder, item)
        if not os.path.exists(dst):
            shutil.move(item_path, dst)
            print(f"  [MOVED] {item} -> {para_folder}/{item}")
            moved_count += 1
        else:
            print(f"  [COLLISION] Note {item} already exists in {para_folder}/. Skipped.")

    print(f"[HEURISTIC] Note organization completed. Total notes moved: {moved_count}\n")


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_heuristic_organizer(target_dir)


if __name__ == "__main__":
    main()
