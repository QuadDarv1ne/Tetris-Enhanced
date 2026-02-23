#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for Tetris Enhanced
Creates a standalone executable using PyInstaller

Usage:
    python build.py [--clean] [--onefile] [--debug]
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path


def get_version() -> str:
    """Получает версию из CHANGELOG.md"""
    changelog_path = Path(__file__).parent / "CHANGELOG.md"
    if changelog_path.exists():
        with open(changelog_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("## ["):
                    # Извлекаем версию из строки ## [2.0.0]
                    version = line.split('[')[1].split(']')[0]
                    return version
    return "2.0.0"


def check_dependencies() -> bool:
    """Проверяет наличие необходимых зависимостей"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller found: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install PyInstaller. Please install manually:")
            print("  pip install pyinstaller")
            return False


def clean_build_dirs():
    """Очищает директории сборки"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✓ Removed {dir_name}")


def build_pyinstaller(onefile: bool = True, debug: bool = False):
    """Собирает исполняемый файл с помощью PyInstaller"""
    version = get_version()
    project_root = Path(__file__).parent
    
    # Основной скрипт
    script_path = project_root / "tetris_enhanced.py"
    
    if not script_path.exists():
        print(f"✗ Main script not found: {script_path}")
        return False
    
    # Формируем команду PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"TetrisEnhanced_v{version}",
        "--add-data", "config.json;.",
        "--add-data", "enhanced_config.json;.",
        "--collect-all", "pygame",
        "--hidden-import", "pygame",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
        "--hidden-import", "psutil",
    ]
    
    # onefile или onedir
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # Отладка
    if debug:
        cmd.append("--debug=all")
    else:
        cmd.append("--noconsole")  # Скрыть консоль для GUI приложения
    
    # Иконка (если есть)
    icon_path = project_root / "tetris.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Путь к скрипту
    cmd.append(str(script_path))
    
    print(f"\n🔨 Building Tetris Enhanced v{version}...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True, cwd=str(project_root))
        print("\n✓ Build completed successfully!")
        
        # Информация о результате
        dist_dir = project_root / "dist"
        if onefile:
            exe_path = dist_dir / f"TetrisEnhanced_v{version}.exe"
        else:
            exe_path = dist_dir / f"TetrisEnhanced_v{version}"
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n📦 Executable: {exe_path}")
            print(f"📊 Size: {size_mb:.2f} MB")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False


def create_readme_dist():
    """Создаёт README для дистрибутива"""
    version = get_version()
    
    readme_content = f"""# Tetris Enhanced v{version}

## Запуск

Просто запустите файл TetrisEnhanced_v{version}.exe

## Управление

- ← / → — перемещение фигуры
- ↓ — мягкое падение
- Space — жёсткое падение
- Z / ↑ — поворот по часовой
- X — поворот против часовой
- C / Shift — удержание (hold)
- P — пауза
- R — перезапуск
- Esc / Q — выход

## Настройка

Для изменения настроек отредактируйте файл config.json

## Системные требования

- Windows 7/8/10/11
- 2 GB RAM
- OpenGL 2.0 compatible video card

## Авторы

Дуплей Максим Игоревич
Email: maksimqwe42@mail.ru
Telegram: @quadd4rv1n7, @dupley_maxim_1999

## Лицензия

MIT License
"""
    
    dist_dir = Path("dist")
    if dist_dir.exists():
        readme_path = dist_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✓ Created distribution README")


def main():
    parser = argparse.ArgumentParser(description="Build Tetris Enhanced executable")
    parser.add_argument('--clean', action='store_true', help='Clean build directories first')
    parser.add_argument('--onedir', action='store_true', help='Build as directory instead of single file')
    parser.add_argument('--debug', action='store_true', help='Build with debug information')
    parser.add_argument('--all', action='store_true', help='Build both onefile and onedir')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("TETRIS ENHANCED - Build Script")
    print("=" * 60)
    
    # Проверка зависимостей
    if not check_dependencies():
        sys.exit(1)
    
    # Очистка
    if args.clean:
        print("\n🧹 Cleaning build directories...")
        clean_build_dirs()
    
    # Сборка
    success = True
    
    if args.all:
        print("\n📦 Building ONEFILE version...")
        success = build_pyinstaller(onefile=True, debug=args.debug)
        
        if success:
            print("\n📦 Building ONEDIR version...")
            success = build_pyinstaller(onefile=False, debug=args.debug)
    else:
        success = build_pyinstaller(
            onefile=not args.onedir,
            debug=args.debug
        )
    
    # Создание README для дистрибутива
    if success:
        create_readme_dist()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ BUILD SUCCESSFUL")
    else:
        print("❌ BUILD FAILED")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
