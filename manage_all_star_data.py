#!/usr/bin/env python3
"""
All-Star Data Management Script
Handles updating All-Star Game appearances data
"""

import json
import os
from datetime import datetime

def load_all_star_data():
    """Load current All-Star data"""
    file_path = "data/all_star_appearances.json"
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {"all_star_appearances": {}, "last_updated": "2025-01-17", "season": "2024-2025"}

def save_all_star_data(data):
    """Save All-Star data"""
    file_path = "data/all_star_appearances.json"
    os.makedirs("data", exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"All-Star data saved to {file_path}")

def add_player(name, appearances):
    """Add or update a player's All-Star appearances"""
    data = load_all_star_data()
    data["all_star_appearances"][name] = appearances
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    save_all_star_data(data)
    print(f"Added {name}: {appearances} All-Star appearances")

def remove_player(name):
    """Remove a player from the list"""
    data = load_all_star_data()
    if name in data["all_star_appearances"]:
        del data["all_star_appearances"][name]
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        save_all_star_data(data)
        print(f"Removed {name}")
    else:
        print(f"Player {name} not found")

def list_players():
    """List all players with their All-Star appearances"""
    data = load_all_star_data()
    players = data["all_star_appearances"]
    
    print(f"All-Star Game Appearances (Updated: {data['last_updated']})")
    print("=" * 60)
    
    # Sort by appearances (descending)
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    
    for name, appearances in sorted_players:
        tier = "Elite" if appearances >= 5 else "High" if appearances >= 3 else "Medium" if appearances >= 2 else "Low" if appearances >= 1 else "None"
        print(f"{name}: {appearances} appearances ({tier} tier)")

def update_season(season):
    """Update the season field"""
    data = load_all_star_data()
    data["season"] = season
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    save_all_star_data(data)
    print(f"Updated season to {season}")

def main():
    """Interactive management interface"""
    print("All-Star Data Management")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. List all players")
        print("2. Add/update player")
        print("3. Remove player")
        print("4. Update season")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            list_players()
        elif choice == "2":
            name = input("Player name: ").strip()
            try:
                appearances = int(input("All-Star appearances: ").strip())
                add_player(name, appearances)
            except ValueError:
                print("Invalid number")
        elif choice == "3":
            name = input("Player name to remove: ").strip()
            remove_player(name)
        elif choice == "4":
            season = input("Season (e.g., 2025-2026): ").strip()
            update_season(season)
        elif choice == "5":
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()


