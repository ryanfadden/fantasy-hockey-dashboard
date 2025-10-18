#!/usr/bin/env python3
"""
Data Directory Cleanup Script
Keeps only the latest files and essential data
"""

import os
import glob
from datetime import datetime


def cleanup_directory(directory, patterns, essential_files=None):
    """Clean up old files in a directory, keeping only the latest"""

    if essential_files is None:
        essential_files = []

    print(f"\n{directory.upper()} Directory Cleanup")
    print("=" * 40)

    deleted_count = 0
    kept_count = 0

    # Process each pattern
    for pattern in patterns:
        files = glob.glob(f"{directory}/{pattern}")
        if files:
            # Sort by modification time (newest first)
            files.sort(key=os.path.getmtime, reverse=True)

            # Keep the latest file, delete the rest
            latest_file = files[0]
            old_files = files[1:]

            pattern_name = pattern.replace("*.json", "").replace("*.md", "")
            print(f"{pattern_name} files:")
            print(f"  Keeping: {os.path.basename(latest_file)}")

            for old_file in old_files:
                try:
                    os.remove(old_file)
                    deleted_count += 1
                except Exception as e:
                    print(f"  Error deleting {os.path.basename(old_file)}: {e}")

    # Check essential files
    if essential_files:
        print(f"\nEssential files:")
        for essential in essential_files:
            file_path = f"{directory}/{essential}"
            if os.path.exists(file_path):
                print(f"  {essential}")
                kept_count += 1
            else:
                print(f"  Missing: {essential}")

    print(f"\n{directory.upper()} Summary:")
    print(f"  Files deleted: {deleted_count}")
    print(f"  Files kept: {kept_count}")

    return deleted_count, kept_count


def cleanup_all_directories():
    """Clean up all directories"""

    print("COMPLETE DIRECTORY CLEANUP")
    print("=" * 50)

    total_deleted = 0
    total_kept = 0

    # Data directory
    data_patterns = [
        "team_data_*.json",
        "free_agents_*.json",
        "standings_*.json",
        "matchup_data_*.json",
        "all_teams_data_*.json",
        "combined_data_*.json",
    ]
    data_essential = ["all_star_appearances.json"]
    deleted, kept = cleanup_directory("data", data_patterns, data_essential)
    total_deleted += deleted
    total_kept += kept

    # Output directory
    output_patterns = [
        "recommendations_*.json",
        "summary_*.json",
    ]
    deleted, kept = cleanup_directory("output", output_patterns)
    total_deleted += deleted
    total_kept += kept

    # Reports directory
    reports_patterns = [
        "analysis_report_*.md",
    ]
    deleted, kept = cleanup_directory("reports", reports_patterns)
    total_deleted += deleted
    total_kept += kept

    print(f"\nOVERALL CLEANUP SUMMARY:")
    print(f"  Total files deleted: {total_deleted}")
    print(f"  Total files kept: {total_kept}")
    print(f"  Estimated space saved: ~{total_deleted * 0.5:.1f} MB")


def show_current_files():
    """Show what files remain after cleanup"""
    print(f"\nCurrent data directory contents:")
    print("=" * 40)

    data_files = glob.glob("data/*.json")
    data_files.sort()

    for file in data_files:
        filename = os.path.basename(file)
        size = os.path.getsize(file) / 1024  # Size in KB
        modified = datetime.fromtimestamp(os.path.getmtime(file))
        print(f"  {filename} ({size:.1f} KB, {modified.strftime('%Y-%m-%d %H:%M')})")


if __name__ == "__main__":
    cleanup_all_directories()
    show_current_files()
