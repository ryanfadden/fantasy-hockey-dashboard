#!/usr/bin/env python3
"""
Fantasy Hockey Configuration Editor
Interactive tool to adjust analysis parameters and prompts
"""

import json
from analysis_config import (
    VALUE_SCORING,
    RECOMMENDATION_THRESHOLDS,
    SWAP_ANALYSIS,
    OPENAI_PROMPTS,
    ANALYSIS_SETTINGS,
    DASHBOARD_CONFIG,
    update_value_score_weight,
    update_recommendation_threshold,
    update_swap_threshold
)

def display_current_config():
    """Display current configuration"""
    print("=" * 60)
    print("CURRENT FANTASY HOCKEY ANALYSIS CONFIGURATION")
    print("=" * 60)
    
    print("\n📊 VALUE SCORING WEIGHTS:")
    for factor, weight in VALUE_SCORING["weights"].items():
        print(f"  {factor}: {weight}")
    
    print("\n🎯 RECOMMENDATION THRESHOLDS:")
    for threshold, value in RECOMMENDATION_THRESHOLDS.items():
        print(f"  {threshold}: {value}")
    
    print("\n🔄 SWAP ANALYSIS THRESHOLDS:")
    for threshold, value in SWAP_ANALYSIS["thresholds"].items():
        print(f"  {threshold}: {value}")
    
    print("\n⚙️ ANALYSIS SETTINGS:")
    for setting, value in ANALYSIS_SETTINGS.items():
        print(f"  {setting}: {value}")

def edit_value_weights():
    """Edit value scoring weights"""
    print("\n📊 EDIT VALUE SCORING WEIGHTS:")
    print("Current weights:")
    for factor, weight in VALUE_SCORING["weights"].items():
        print(f"  {factor}: {weight}")
    
    print("\nEnter new weights (press Enter to keep current):")
    for factor in VALUE_SCORING["weights"]:
        try:
            new_weight = input(f"{factor} [{VALUE_SCORING['weights'][factor]}]: ")
            if new_weight.strip():
                weight = float(new_weight)
                if update_value_score_weight(factor, weight):
                    print(f"✅ Updated {factor} to {weight}")
                else:
                    print(f"❌ Failed to update {factor}")
        except ValueError:
            print(f"❌ Invalid input for {factor}")

def edit_recommendation_thresholds():
    """Edit recommendation thresholds"""
    print("\n🎯 EDIT RECOMMENDATION THRESHOLDS:")
    print("Current thresholds:")
    for threshold, value in RECOMMENDATION_THRESHOLDS.items():
        print(f"  {threshold}: {value}")
    
    print("\nEnter new values (press Enter to keep current):")
    for threshold in RECOMMENDATION_THRESHOLDS:
        try:
            new_value = input(f"{threshold} [{RECOMMENDATION_THRESHOLDS[threshold]}]: ")
            if new_value.strip():
                value = float(new_value) if threshold != "max_recommendations" else int(new_value)
                if update_recommendation_threshold(threshold, value):
                    print(f"✅ Updated {threshold} to {value}")
                else:
                    print(f"❌ Failed to update {threshold}")
        except ValueError:
            print(f"❌ Invalid input for {threshold}")

def edit_swap_thresholds():
    """Edit swap analysis thresholds"""
    print("\n🔄 EDIT SWAP ANALYSIS THRESHOLDS:")
    print("Current thresholds:")
    for threshold, value in SWAP_ANALYSIS["thresholds"].items():
        print(f"  {threshold}: {value}")
    
    print("\nEnter new values (press Enter to keep current):")
    for threshold in SWAP_ANALYSIS["thresholds"]:
        try:
            new_value = input(f"{threshold} [{SWAP_ANALYSIS['thresholds'][threshold]}]: ")
            if new_value.strip():
                value = float(new_value)
                if update_swap_threshold(threshold, value):
                    print(f"✅ Updated {threshold} to {value}")
                else:
                    print(f"❌ Failed to update {threshold}")
        except ValueError:
            print(f"❌ Invalid input for {threshold}")

def view_prompts():
    """View current OpenAI prompts"""
    print("\n🤖 CURRENT OPENAI PROMPTS:")
    print("=" * 40)
    
    for prompt_type, config in OPENAI_PROMPTS.items():
        print(f"\n📝 {prompt_type.upper()}:")
        print(f"System Message: {config['system_message'][:100]}...")
        
        if 'user_prompt_template' in config:
            print(f"User Template: {config['user_prompt_template'][:100]}...")
        
        if 'scoring_system' in config:
            print(f"Scoring System: {config['scoring_system'][:100]}...")

def save_config():
    """Save current configuration to file"""
    config = {
        "VALUE_SCORING": VALUE_SCORING,
        "RECOMMENDATION_THRESHOLDS": RECOMMENDATION_THRESHOLDS,
        "SWAP_ANALYSIS": SWAP_ANALYSIS,
        "ANALYSIS_SETTINGS": ANALYSIS_SETTINGS,
        "DASHBOARD_CONFIG": DASHBOARD_CONFIG
    }
    
    with open("current_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration saved to current_config.json")

def main():
    """Main configuration editor"""
    while True:
        print("\n" + "=" * 60)
        print("FANTASY HOCKEY CONFIGURATION EDITOR")
        print("=" * 60)
        print("1. View Current Configuration")
        print("2. Edit Value Scoring Weights")
        print("3. Edit Recommendation Thresholds")
        print("4. Edit Swap Analysis Thresholds")
        print("5. View OpenAI Prompts")
        print("6. Save Configuration")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            display_current_config()
        elif choice == "2":
            edit_value_weights()
        elif choice == "3":
            edit_recommendation_thresholds()
        elif choice == "4":
            edit_swap_thresholds()
        elif choice == "5":
            view_prompts()
        elif choice == "6":
            save_config()
        elif choice == "7":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-7.")

if __name__ == "__main__":
    main()
