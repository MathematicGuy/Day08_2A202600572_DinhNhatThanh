#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
move_image.py — Simple script to scan a folder and move image files into an 'images/' folder.
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

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}

def migrate_images(target_dir: str):
    print("=== [IMAGE MIGRATION SERVICE] ===")
    if not os.path.exists(target_dir):
        print(f"[ERROR] Directory {target_dir} does not exist!")
        return

    images_folder = os.path.join(target_dir, "images")
    moved_count = 0

    # Scan directory for image files
    for item in sorted(os.listdir(target_dir)):
        item_path = os.path.join(target_dir, item)
        # Skip directories
        if os.path.isdir(item_path):
            continue

        # Check file extension
        _, ext = os.path.splitext(item)
        if ext.lower() in IMAGE_EXTENSIONS:
            # Lazy create images folder
            if not os.path.exists(images_folder):
                os.makedirs(images_folder, exist_ok=True)
                print(f"[IMAGE] Created images directory: {images_folder}")
            
            dst = os.path.join(images_folder, item)
            shutil.move(item_path, dst)
            print(f"  [MOVED] {item} -> images/{item}")
            moved_count += 1

    print(f"[IMAGE] Completed image migration. Total files moved: {moved_count}\n")


def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    migrate_images(target_dir)


if __name__ == "__main__":
    main()
