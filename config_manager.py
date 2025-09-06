#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration manager for Tetris Enhanced
"""

import sys
import os
import json
from game_config import game_config

def list_profiles():
    """List all available configuration profiles."""
    print("Available configuration profiles:")
    for profile_name in game_config.get_profile_names():
        print(f"  - {profile_name}")

def apply_profile(profile_name):
    """Apply a configuration profile."""
    if game_config.apply_profile(profile_name):
        print(f"Profile '{profile_name}' applied successfully.")
        # Save the configuration
        game_config.save_to_file()
        print("Configuration saved to config.json")
    else:
        print(f"Failed to apply profile '{profile_name}'")

def validate_config():
    """Validate the current configuration."""
    warnings = game_config.validate_config()
    if warnings:
        print("Configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("Configuration is valid.")

def reset_config():
    """Reset configuration to defaults."""
    game_config.reset_to_defaults()
    game_config.save_to_file()
    print("Configuration reset to defaults and saved to config.json")

def show_config():
    """Show current configuration."""
    print("Current configuration:")
    # Convert to dict and remove profiles for cleaner display
    config_dict = {k: v for k, v in game_config.__dict__.items() if k != "profiles"}
    for key, value in config_dict.items():
        print(f"  {key}: {value}")

def interactive_config():
    """Interactive configuration manager."""
    while True:
        print("\nConfiguration Manager")
        print("1. List profiles")
        print("2. Apply profile")
        print("3. Validate configuration")
        print("4. Reset to defaults")
        print("5. Show current configuration")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == "1":
            list_profiles()
        elif choice == "2":
            profile_name = input("Enter profile name: ").strip()
            apply_profile(profile_name)
        elif choice == "3":
            validate_config()
        elif choice == "4":
            confirm = input("Are you sure you want to reset to defaults? (y/N): ").strip().lower()
            if confirm == "y":
                reset_config()
        elif choice == "5":
            show_config()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        interactive_config()
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_profiles()
    elif command == "apply" and len(sys.argv) > 2:
        apply_profile(sys.argv[2])
    elif command == "validate":
        validate_config()
    elif command == "reset":
        reset_config()
    elif command == "show":
        show_config()
    else:
        print("Usage:")
        print("  python config_manager.py list          - List available profiles")
        print("  python config_manager.py apply <name>  - Apply a profile")
        print("  python config_manager.py validate      - Validate configuration")
        print("  python config_manager.py reset         - Reset to defaults")
        print("  python config_manager.py show          - Show current configuration")
        print("  python config_manager.py               - Interactive mode")

if __name__ == "__main__":
    main()