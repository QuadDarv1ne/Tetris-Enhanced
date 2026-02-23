#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test framework for Tetris Enhanced

This module provides:
- Unit tests for core game logic
- Integration tests for game systems
- Performance benchmarks
- UI component tests
"""

import sys
import os
import unittest
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestCategory(Enum):
    """Категории тестов"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    UI = "ui"
    CONFIG = "config"


@dataclass
class TestResult:
    """Результат теста"""
    name: str
    category: TestCategory
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None


class TestRunner:
    """Запускатель тестов с расширенной статистикой"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = 0.0
        
    def run_test(self, name: str, category: TestCategory, test_func) -> TestResult:
        """Запускает отдельный тест"""
        if self.verbose:
            print(f"  Running: {name}...", end=" ", flush=True)
        
        self.start_time = time.perf_counter()
        error = None
        passed = False
        
        try:
            test_func()
            passed = True
        except AssertionError as e:
            error = f"Assertion: {e}"
        except Exception as e:
            error = f"Exception: {type(e).__name__}: {e}"
        
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        result = TestResult(
            name=name,
            category=category,
            passed=passed,
            duration_ms=duration_ms,
            error_message=error
        )
        self.results.append(result)
        
        if self.verbose:
            if passed:
                print(f"✅ PASS ({duration_ms:.2f}ms)")
            else:
                print(f"❌ FAIL ({duration_ms:.2f}ms) - {error}")
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку результатов"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        total_duration = sum(r.duration_ms for r in self.results)
        avg_duration = total_duration / total if total > 0 else 0
        
        by_category = {}
        for r in self.results:
            cat = r.category.value
            if cat not in by_category:
                by_category[cat] = {'total': 0, 'passed': 0}
            by_category[cat]['total'] += 1
            if r.passed:
                by_category[cat]['passed'] += 1
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total * 100 if total > 0 else 0,
            'total_duration_ms': total_duration,
            'avg_duration_ms': avg_duration,
            'by_category': by_category
        }
    
    def print_summary(self):
        """Выводит сводку результатов"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        print(f"Всего тестов: {summary['total']}")
        print(f"✅ Пройдено: {summary['passed']}")
        print(f"❌ Провалено: {summary['failed']}")
        print(f"📊 Процент успеха: {summary['pass_rate']:.1f}%")
        print(f"⏱️  Общее время: {summary['total_duration_ms']:.2f}ms")
        print(f"⏱️  Среднее время: {summary['avg_duration_ms']:.2f}ms")
        
        print("\nПо категориям:")
        for cat, stats in summary['by_category'].items():
            rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {cat}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # Вывод проваленных тестов
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            print("\n❌ Проваленные тесты:")
            for result in failed_tests:
                print(f"  • {result.name}: {result.error_message}")
        
        print("=" * 60)


# ==================== ТЕСТЫ КОНФИГУРАЦИИ ====================

class ConfigTests:
    """Тесты для системы конфигурации"""
    
    @staticmethod
    def test_config_load_defaults():
        """Тест загрузки конфигурации по умолчанию"""
        from game_config import GameConfig
        
        config = GameConfig()
        assert config.screen_width == 1366, "Default screen_width mismatch"
        assert config.screen_height == 768, "Default screen_height mismatch"
        assert config.enable_audio is True, "Default enable_audio mismatch"
        assert config.fps_target == 60, "Default fps_target mismatch"
    
    @staticmethod
    def test_config_save_load():
        """Тест сохранения и загрузки конфигурации"""
        from game_config import GameConfig
        import tempfile
        
        config = GameConfig()
        config.screen_width = 1920
        config.screen_height = 1080
        config.fullscreen = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save_to_file(temp_path)
            
            loaded_config = GameConfig.load_from_file(temp_path)
            assert loaded_config.screen_width == 1920, "Loaded screen_width mismatch"
            assert loaded_config.screen_height == 1080, "Loaded screen_height mismatch"
            assert loaded_config.fullscreen is True, "Loaded fullscreen mismatch"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @staticmethod
    def test_config_validation():
        """Тест валидации конфигурации"""
        from game_config import GameConfig
        
        config = GameConfig()
        
        # Проверка наличия всех обязательных полей
        assert hasattr(config, 'screen_width')
        assert hasattr(config, 'screen_height')
        assert hasattr(config, 'enable_audio')
        assert hasattr(config, 'fps_target')
    
    @staticmethod
    def test_config_resolution_filter():
        """Тест фильтрации разрешений"""
        from game_config import GameConfig
        
        config = GameConfig()
        config.screen_width = 1920
        config.screen_height = 1080
        
        resolutions = config.get_filtered_resolutions()
        assert len(resolutions) > 0, "No resolutions found"
        assert (800, 600) in resolutions, "Minimum resolution not found"
    
    @staticmethod
    def test_config_aspect_ratio():
        """Тест расчёта соотношения сторон"""
        from game_config import GameConfig
        
        config = GameConfig()
        config.screen_width = 1920
        config.screen_height = 1080
        
        ratio = config.get_aspect_ratio()
        assert abs(ratio - 16/9) < 0.01, f"Aspect ratio mismatch: {ratio}"


# ==================== ТЕСТЫ АДАПТИВНОСТИ ====================

class AdaptiveDesignTests:
    """Тесты для системы адаптивного дизайна"""
    
    @staticmethod
    def test_responsive_design_initialization():
        """Тест инициализации адаптивного дизайна"""
        from tetris_enhanced import AdvancedResponsiveDesign
        
        responsive = AdvancedResponsiveDesign(1920, 1080)
        assert responsive.screen_width == 1920
        assert responsive.screen_height == 1080
        assert responsive.scale_factors is not None
    
    @staticmethod
    def test_scale_factors():
        """Тест коэффициентов масштабирования"""
        from tetris_enhanced import AdvancedResponsiveDesign
        
        responsive = AdvancedResponsiveDesign(1920, 1080)
        
        assert responsive.scale_factors['x'] > 0
        assert responsive.scale_factors['y'] > 0
        assert responsive.scale_factors['font'] > 0
        assert responsive.scale_factors['ui'] > 0
    
    @staticmethod
    def test_font_scaling():
        """Тест масштабирования шрифтов"""
        from tetris_enhanced import AdvancedResponsiveDesign
        
        responsive = AdvancedResponsiveDesign(1920, 1080)
        
        scaled = responsive.scale_font(24)
        assert scaled >= 12, "Font too small"
        assert scaled <= 72, "Font too large"
    
    @staticmethod
    def test_margin_scaling():
        """Тест масштабирования отступов"""
        from tetris_enhanced import AdvancedResponsiveDesign
        
        responsive = AdvancedResponsiveDesign(1920, 1080)
        
        margin = responsive.get_margin(20)
        assert margin > 0, "Margin should be positive"
        assert margin <= 100, "Margin too large"
    
    @staticmethod
    def test_device_class_detection():
        """Тест определения класса устройства"""
        from tetris_enhanced import AdvancedResponsiveDesign
        
        test_cases = [
            (3840, 2160, "ultra_high"),
            (1920, 1080, "high"),
            (1024, 768, "medium"),
            (800, 600, "low")
        ]
        
        for width, height, expected_class in test_cases:
            responsive = AdvancedResponsiveDesign(width, height)
            assert responsive.device_class == expected_class, \
                f"Device class mismatch for {width}x{height}"
    
    @staticmethod
    def test_aspect_ratio_detection():
        """Тест определения соотношения сторон"""
        from tetris_enhanced import AdvancedResponsiveDesign
        
        test_cases = [
            (1920, 1080, "16:9"),
            (2560, 1080, "21:9"),
            (1024, 768, "4:3"),
            (1280, 800, "16:10")
        ]
        
        for width, height, expected_aspect in test_cases:
            responsive = AdvancedResponsiveDesign(width, height)
            assert responsive.aspect_type == expected_aspect, \
                f"Aspect type mismatch for {width}x{height}"


# ==================== ТЕСТЫ UI КОМПОНЕНТОВ ====================

class UIComponentTests:
    """Тесты для UI компонентов"""
    
    @staticmethod
    def test_ui_colors():
        """Тест цветов UI"""
        from ui_components import UIColor
        
        assert UIColor.BLACK == (0, 0, 0)
        assert UIColor.WHITE == (255, 255, 255)
        assert len(UIColor.BUTTON_NORMAL) == 3
    
    @staticmethod
    def test_button_initialization():
        """Тест инициализации кнопки"""
        try:
            import pygame
            pygame.init()
            
            from ui_components import Button
            
            font = pygame.font.Font(None, 24)
            button = Button(100, 100, 200, 50, "Test", font)
            
            assert button.rect.width == 200
            assert button.rect.height == 50
            assert button.text == "Test"
            assert button.enabled is True
            
            pygame.quit()
        except ImportError:
            pass  # Пропускаем если pygame не установлен
    
    @staticmethod
    def test_progress_bar():
        """Тест прогресс-бара"""
        try:
            import pygame
            pygame.init()
            
            from ui_components import ProgressBar
            
            bar = ProgressBar(0, 0, 200, 20, 0.0, 1.0, 0.5)
            
            assert bar.get_percentage() == 0.5
            
            bar.set_value(0.75)
            assert bar.get_percentage() == 0.75
            
            bar.set_value(1.5)  # За пределы
            assert bar.get_percentage() == 1.0  # Должно ограничиться
            
            pygame.quit()
        except ImportError:
            pass


# ==================== ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ====================

class PerformanceTests:
    """Тесты производительности"""
    
    @staticmethod
    def test_cache_performance():
        """Тест производительности кэша"""
        from utils.performance import LRUCache
        
        cache = LRUCache(max_size=100)
        
        # Заполняем кэш
        start = time.perf_counter()
        for i in range(200):
            cache.put(i, f"value_{i}")
        put_time = (time.perf_counter() - start) * 1000
        
        # Читаем из кэша
        start = time.perf_counter()
        for i in range(200):
            cache.get(i)
        get_time = (time.perf_counter() - start) * 1000
        
        stats = cache.get_stats()
        
        assert stats['size'] <= 100, "Cache size exceeded max"
        assert stats['hit_rate_percent'] > 0, "Hit rate should be positive"
        assert put_time < 100, f"Put operations too slow: {put_time:.2f}ms"
        assert get_time < 100, f"Get operations too slow: {get_time:.2f}ms"
    
    @staticmethod
    def test_performance_monitor():
        """Тест монитора производительности"""
        from utils.performance import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        monitor.start_frame()
        time.sleep(0.016)  # ~60 FPS
        monitor.end_frame()
        
        metrics = monitor.metrics
        assert metrics.fps >= 0
        assert metrics.frame_time_ms >= 0
    
    @staticmethod
    def test_responsive_design_caching():
        """Тест кэширования в адаптивном дизайне"""
        from tetris_enhanced import AdvancedResponsiveDesign
        
        responsive = AdvancedResponsiveDesign(1920, 1080)
        
        # Многократный вызов должен использовать кэш
        start = time.perf_counter()
        for _ in range(100):
            responsive.scale_font(24)
        cached_time = (time.perf_counter() - start) * 1000
        
        # Кэш должен ускорить выполнение
        assert cached_time < 50, f"Cached operations too slow: {cached_time:.2f}ms"


# ==================== ТЕСТЫ ИГРОВОЙ ЛОГИКИ ====================

class GameLogicTests:
    """Тесты игровой логики"""
    
    @staticmethod
    def test_tetromino_colors():
        """Тест цветов тетромино"""
        from ui_components import UIColor
        
        colors = UIColor.TETROMINO_COLORS
        assert 'I' in colors
        assert 'O' in colors
        assert 'T' in colors
        assert 'S' in colors
        assert 'Z' in colors
        assert 'J' in colors
        assert 'L' in colors
        
        # Все цвета должны быть RGB кортежами
        for name, color in colors.items():
            assert len(color) == 3, f"{name} color should be RGB"
            assert all(0 <= c <= 255 for c in color), f"{name} color values out of range"
    
    @staticmethod
    def test_game_modes():
        """Тест игровых режимов"""
        from tetris_enhanced import GameMode, GAME_MODE_CONFIGS
        
        # Проверка наличия всех режимов
        assert GameMode.CAMPAIGN in GAME_MODE_CONFIGS
        assert GameMode.ENDLESS_IMMERSIVE in GAME_MODE_CONFIGS
        assert GameMode.ENDLESS_RELAXED in GAME_MODE_CONFIGS
        
        # Проверка конфигурации каждого режима
        for mode, config in GAME_MODE_CONFIGS.items():
            assert config.name is not None
            assert config.description is not None
            assert config.gravity_multiplier > 0
            assert config.scoring_multiplier > 0
    
    @staticmethod
    def test_campaign_levels():
        """Тест уровней кампании"""
        from tetris_enhanced import CAMPAIGN_LEVELS
        
        assert len(CAMPAIGN_LEVELS) > 0, "No campaign levels defined"
        
        for level in CAMPAIGN_LEVELS:
            assert level.level_num > 0
            assert level.name is not None
            assert level.description is not None
            assert len(level.objectives) > 0
            
            for obj in level.objectives:
                assert obj.type in ["lines", "score", "time", "survive"]
                assert obj.target > 0
                assert obj.description is not None


# ==================== ЗАПУСК ВСЕХ ТЕСТОВ ====================

def run_all_tests(categories: Optional[List[TestCategory]] = None) -> bool:
    """
    Запускает все тесты
    
    Args:
        categories: Фильтр по категориям (None = все категории)
    
    Returns:
        True если все тесты пройдены
    """
    runner = TestRunner(verbose=True)
    
    all_test_classes = [
        (TestCategory.CONFIG, ConfigTests),
        (TestCategory.UNIT, AdaptiveDesignTests),
        (TestCategory.UI, UIComponentTests),
        (TestCategory.PERFORMANCE, PerformanceTests),
        (TestCategory.UNIT, GameLogicTests),
    ]
    
    for category, test_class in all_test_classes:
        if categories and category not in categories:
            continue
        
        print(f"\n{'=' * 60}")
        print(f"КАТЕГОРИЯ: {category.value.upper()}")
        print('=' * 60)
        
        for test_name in dir(test_class):
            if test_name.startswith('test_'):
                test_func = getattr(test_class, test_name)
                if callable(test_func):
                    runner.run_test(f"{test_class.__name__}.{test_name}", category, test_func)
    
    runner.print_summary()
    
    summary = runner.get_summary()
    return summary['failed'] == 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tetris Enhanced Test Framework")
    parser.add_argument(
        '--category', '-c',
        choices=['unit', 'integration', 'performance', 'ui', 'config'],
        action='append',
        help='Run only tests from specified category'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress detailed output'
    )
    
    args = parser.parse_args()
    
    categories = None
    if args.category:
        categories = [TestCategory(c) for c in args.category]
    
    success = run_all_tests(categories)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
