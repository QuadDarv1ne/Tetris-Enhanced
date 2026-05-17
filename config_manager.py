#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration manager for Tetris Enhanced
"""

import sys
import os
import json
from game_config import GameConfig, game_config


def list_profiles():
    """List all available configuration profiles (resolution presets)."""
    print("Available resolution profiles:")
    for i, (w, h) in enumerate(game_config.available_resolutions, 1):
        aspect = "16:9" if abs(w / h - 16 / 9) < 0.05 else "16:10" if abs(w / h - 16 / 10) < 0.05 else "4:3"
        current = " <-- current" if (w, h) == (game_config.screen_width, game_config.screen_height) else ""
        print(f"  {i}. {w}x{h} ({aspect}){current}")


def apply_profile(profile_name):
    """Apply a resolution profile by name (e.g. '1920x1080') or index."""
    # Try parsing as index
    try:
        idx = int(profile_name) - 1
        if 0 <= idx < len(game_config.available_resolutions):
            w, h = game_config.available_resolutions[idx]
            game_config.screen_width = w
            game_config.screen_height = h
            game_config.save_to_file()
            print(f"Resolution set to {w}x{h}. Configuration saved.")
            return
    except ValueError:
        pass

    # Try matching by name like "1920x1080"
    target = profile_name.lower().replace(" ", "")
    for w, h in game_config.available_resolutions:
        if f"{w}x{h}" == target:
            game_config.screen_width = w
            game_config.screen_height = h
            game_config.save_to_file()
            print(f"Resolution set to {w}x{h}. Configuration saved.")
            return

    print(f"Profile '{profile_name}' not found. Use 'list' to see available profiles.")


def validate_config():
    """Validate the current configuration."""
    warnings = []

    if not (320 <= game_config.screen_width <= 7680):
        warnings.append(f"Unusual screen width: {game_config.screen_width}")
    if not (200 <= game_config.screen_height <= 4320):
        warnings.append(f"Unusual screen height: {game_config.screen_height}")
    if not (0.0 <= game_config.music_volume <= 1.0):
        warnings.append(f"Music volume out of range: {game_config.music_volume}")
    if not (0.0 <= game_config.sound_volume <= 1.0):
        warnings.append(f"Sound volume out of range: {game_config.sound_volume}")
    if game_config.fps_target not in (30, 60, 120, 144, 240):
        warnings.append(f"Non-standard FPS target: {game_config.fps_target}")
    if game_config.render_quality not in ("low", "medium", "high"):
        warnings.append(f"Unknown render quality: {game_config.render_quality}")
    if game_config.ui_theme not in ("dark", "light"):
        warnings.append(f"Unknown UI theme: {game_config.ui_theme}")

    current_res = (game_config.screen_width, game_config.screen_height)
    if current_res not in game_config.available_resolutions:
        warnings.append(f"Current resolution {current_res} is not in available resolutions list")

    return warnings


def reset_config():
    """Reset configuration to defaults."""
    defaults = GameConfig()
    for field_name in defaults.__dataclass_fields__:
        setattr(game_config, field_name, getattr(defaults, field_name))
    game_config.save_to_file()
    print("Configuration reset to defaults and saved.")


def show_config():
    """Show current configuration."""
    print("Current configuration:")
    print(f"  screen: {game_config.screen_width}x{game_config.screen_height}")
    print(f"  fullscreen: {game_config.fullscreen}")
    print(f"  vsync: {game_config.vsync}")
    print(f"  fps_target: {game_config.fps_target}")
    print(f"  enable_adaptive_design: {game_config.enable_adaptive_design}")
    print(f"  ui_scale_factor: {game_config.ui_scale_factor}")
    print(f"  font_scale_multiplier: {game_config.font_scale_multiplier}")
    print(f"  button_scale_multiplier: {game_config.button_scale_multiplier}")
    print(f"  margin_scale_multiplier: {game_config.margin_scale_multiplier}")
    print(f"  game_field: {game_config.game_field_cols}x{game_config.game_field_rows}")
    print(f"  block_size_base: {game_config.block_size_base}")
    print(f"  music_volume: {game_config.music_volume}")
    print(f"  sound_volume: {game_config.sound_volume}")
    print(f"  enable_animations: {game_config.enable_animations}")
    print(f"  enable_shadows: {game_config.enable_shadows}")
    print(f"  render_quality: {game_config.render_quality}")
    print(f"  cache_size_multiplier: {game_config.cache_size_multiplier}")
    print(f"  auto_save_enabled: {game_config.auto_save_enabled}")
    print(f"  auto_save_interval: {game_config.auto_save_interval}s")
    print(f"  show_debug_info: {game_config.show_debug_info}")
    print(f"  ui_theme: {game_config.ui_theme}")
    print(f"  enable_high_contrast: {game_config.enable_high_contrast}")
    print(f"  text_size_multiplier: {game_config.text_size_multiplier}")
    print(f"  enable_text_shadows: {game_config.enable_text_shadows}")
    print(f"  enable_motion_effects: {game_config.enable_motion_effects}")


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
            profile_name = input("Enter profile name (e.g. '1920x1080' or index number): ").strip()
            apply_profile(profile_name)
        elif choice == "3":
            ws = validate_config()
            if ws:
                print("Configuration warnings:")
                for w in ws:
                    print(f"  - {w}")
            else:
                print("Configuration is valid.")
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
        ws = validate_config()
        if ws:
            print("Configuration warnings:")
            for w in ws:
                print(f"  - {w}")
        else:
            print("Configuration is valid.")
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
