#!/usr/bin/env python3
"""
File Integrity Checker (FIC)
Uses SHA-256 to detect file changes in a directory.
"""

import os
import hashlib
import json
import argparse
from datetime import datetime

BASELINE_FILE = "baseline.json"
CHUNK_SIZE = 8192  # نقرأ الملف على دفعات لتفادي استهلاك الذاكرة


def calculate_sha256(filepath):
    """حساب بصمة SHA-256 لملف."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, FileNotFoundError) as e:
        return f"ERROR: {e}"


def get_file_info(filepath):
    """يرجّع قاموس يحتوي: hash + size + modified."""
    stat = os.stat(filepath)
    return {
        "sha256": calculate_sha256(filepath),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def scan_directory(directory):
    """يمشي على كل الملفات ويبني قاموس: {relative_path: info}."""
    result = {}
    for root, _, files in os.walk(directory):
        for name in files:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, directory)
            result[rel_path] = get_file_info(full_path)
    return result


def save_baseline(directory, output=BASELINE_FILE):
    """إنشاء بصمة مرجعية (Baseline)."""
    print(f"[*] Scanning: {directory}")
    snapshot = scan_directory(directory)
    data = {
        "directory": os.path.abspath(directory),
        "created": datetime.now().isoformat(timespec="seconds"),
        "files": snapshot,
    }
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[+] Baseline saved to: {output}")
    print(f"[+] Total files hashed: {len(snapshot)}")


def load_baseline(path=BASELINE_FILE):
    """تحميل الـ baseline من ملف JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline '{path}' not found. Run scan first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_integrity(directory, baseline_path=BASELINE_FILE):
    """مقارنة الحالة الحالية بالـ baseline."""
    baseline = load_baseline(baseline_path)
    old_files = baseline["files"]

    print(f"[*] Baseline created: {baseline['created']}")
    print(f"[*] Re-scanning: {directory}\n")

    current = scan_directory(directory)

    modified, added, deleted, unchanged = [], [], [], []

    for path, info in current.items():
        if path not in old_files:
            added.append(path)
        elif info["sha256"] != old_files[path]["sha256"]:
            modified.append(path)
        else:
            unchanged.append(path)

    for path in old_files:
        if path not in current:
            deleted.append(path)

    print("=" * 60)
    print("           FILE INTEGRITY REPORT")
    print("=" * 60)

    if modified:
        print(f"\n[!] MODIFIED ({len(modified)}):")
        for p in modified:
            print(f"    - {p}")

    if added:
        print(f"\n[+] ADDED ({len(added)}):")
        for p in added:
            print(f"    - {p}")

    if deleted:
        print(f"\n[-] DELETED ({len(deleted)}):")
        for p in deleted:
            print(f"    - {p}")

    print(f"\n[=] UNCHANGED: {len(unchanged)}")
    print("=" * 60)

    if not (modified or added or deleted):
        print("\n✅ No changes detected. Files are intact.")
    else:
        print("\n⚠️  Changes detected! Investigate immediately.")


def show_file_details(directory):
    """عرض تفاصيل كل ملف (hash + size + modified)."""
    print(f"{'File':<40} {'Size':>10} {'Modified':<20} SHA-256")
    print("-" * 110)
    for root, _, files in os.walk(directory):
        for name in files:
            full_path = os.path.join(root, name)
            info = get_file_info(full_path)
            rel = os.path.relpath(full_path, directory)
            print(f"{rel:<40} {info['size']:>10} {info['modified']:<20} {info['sha256'][:32]}...")


def main():
    parser = argparse.ArgumentParser(description="File Integrity Checker — SHA-256 based.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Create baseline snapshot")
    p_scan.add_argument("directory", help="Directory to scan")
    p_scan.add_argument("-o", "--output", default=BASELINE_FILE, help="Baseline file")

    p_check = sub.add_parser("check", help="Check integrity against baseline")
    p_check.add_argument("directory", help="Directory to check")
    p_check.add_argument("-b", "--baseline", default=BASELINE_FILE, help="Baseline file")

    p_info = sub.add_parser("info", help="Show file details")
    p_info.add_argument("directory", help="Directory to inspect")

    args = parser.parse_args()

    try:
        if args.command == "scan":
            save_baseline(args.directory, args.output)
        elif args.command == "check":
            check_integrity(args.directory, args.baseline)
        elif args.command == "info":
            show_file_details(args.directory)
    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    main()