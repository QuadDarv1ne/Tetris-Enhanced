#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Комплексная система тестирования для Tetris Enhanced
====================================================

Объединяет все тесты в один файл:
- Тестирование адаптивного дизайна
- Тестирование динамического изменения разрешения
- Тестирование исправлений системы
- Демонстрационные режимы

Запуск:
    python tetris_tests.py
    
Или с параметрами:
    python tetris_tests.py --test adaptive           # Только адаптивный дизайн
    python tetris_tests.py --test resolution         # Только разрешение
    python tetris_tests.py --test dynamic            # Динамическое изменение
    python tetris_tests.py --demo                    # Демо-режим
"""

import sys
import os
import argparse
import time

# Добавляем путь к главному файлу
sys.path.append(os.path.dirname(__file__))

try:
    import pygame
    from tetris_enhanced import (
        AdvancedResponsiveDesign, 
        apply_resolution_change, 
        game_config
    )
    
    class TetrisTestSuite:
        """Комплексная система тестирования Tetris Enhanced"""
        
        def __init__(self):
            self.results = {}
            print("=== КОМПЛЕКСНАЯ СИСТЕМА ТЕСТИРОВАНИЯ TETRIS ENHANCED ===\n")
        
        def test_adaptive_design(self):
            """Тестирует улучшенную систему адаптивного дизайна"""
            print("🧪 ТЕСТ 1: Улучшенная система адаптивного дизайна")
            print("=" * 60)
            
            test_cases = [
                {"name": "Ультра-высокое разрешение 4K", "width": 3840, "height": 2160, "dpi": 144.0},
                {"name": "Сверхширокий 32:9", "width": 3840, "height": 1080, "dpi": 96.0},
                {"name": "Широкий 21:9", "width": 2560, "height": 1080, "dpi": 96.0},
                {"name": "Стандартный 16:9 FHD", "width": 1920, "height": 1080, "dpi": 96.0},
                {"name": "Классический 4:3", "width": 1024, "height": 768, "dpi": 96.0},
                {"name": "Малый экран", "width": 800, "height": 600, "dpi": 96.0}
            ]
            
            test_results = []
            
            for test_case in test_cases:
                print(f"\n📱 {test_case['name']} ({test_case['width']}x{test_case['height']})")
                print("-" * 50)
                
                try:
                    responsive = AdvancedResponsiveDesign(
                        test_case['width'], 
                        test_case['height'], 
                        test_case['dpi']
                    )
                    
                    # Основная информация
                    print(f"  Класс устройства: {responsive.device_class}")
                    print(f"  Тип экрана: {responsive.aspect_type}")
                    print(f"  Категория DPI: {responsive.dpi_category}")
                    
                    # Масштабирование
                    font_scale = responsive.scale_factors['font']
                    ui_scale = responsive.scale_factors['ui']
                    print(f"  Масштабирование шрифтов: {font_scale:.2f}x")
                    print(f"  Масштабирование UI: {ui_scale:.2f}x")
                    
                    # Практические размеры
                    font_24 = responsive.scale_font(24)
                    button_h = responsive.get_button_height()
                    margin = responsive.get_margin(20)
                    
                    print(f"  Шрифт 24px → {font_24}px")
                    print(f"  Высота кнопки → {button_h}px")
                    print(f"  Отступ 20px → {margin}px")
                    
                    # Игровое поле
                    origin_x, origin_y, field_w, field_h, block_size = responsive.get_grid_position()
                    print(f"  Игровое поле: {field_w}x{field_h}, блок {block_size}px")
                    
                    # Производительность
                    perf = responsive.get_performance_settings()
                    print(f"  Качество рендера: {perf['render_quality']}")
                    print(f"  Целевой FPS: {perf['fps_target']}")
                    
                    test_results.append({"name": test_case['name'], "status": "✅ УСПЕХ", "error": None})
                    
                except Exception as e:
                    print(f"  ❌ ОШИБКА: {e}")
                    test_results.append({"name": test_case['name'], "status": "❌ ОШИБКА", "error": str(e)})
            
            # Итоги
            success_count = sum(1 for r in test_results if "✅" in r['status'])
            print(f"\n📊 ИТОГИ ТЕСТА АДАПТИВНОГО ДИЗАЙНА:")
            print(f"   Успешно: {success_count}/{len(test_results)} тестов")
            
            if success_count == len(test_results):
                print("   🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            
            self.results['adaptive_design'] = test_results
            return success_count == len(test_results)
        
        def test_resolution_system(self):
            """Тестирует систему разрешений"""
            print("\n🖥️  ТЕСТ 2: Система разрешений экрана")
            print("=" * 60)
            
            try:
                # Тестируем фильтрацию разрешений
                filtered_resolutions = game_config.get_filtered_resolutions()
                
                print(f"📊 Статистика разрешений:")
                print(f"   Всего доступно: {len(filtered_resolutions)} разрешений")
                print(f"   Текущее: {game_config.screen_width}x{game_config.screen_height}")
                print(f"   Соотношение сторон: {game_config.get_aspect_ratio():.2f}")
                
                print(f"\n📝 Доступные разрешения:")
                for i, (w, h) in enumerate(filtered_resolutions, 1):
                    ratio = w / h
                    if abs(ratio - 16/9) < 0.1:
                        aspect = "16:9"
                    elif abs(ratio - 21/9) < 0.1:
                        aspect = "21:9"
                    elif abs(ratio - 4/3) < 0.1:
                        aspect = "4:3"
                    elif abs(ratio - 16/10) < 0.1:
                        aspect = "16:10"
                    else:
                        aspect = f"{ratio:.2f}:1"
                    print(f"   {i:2d}. {w}x{h} ({aspect})")
                
                # Проверяем основные функции
                valid_count = 0
                for w, h in filtered_resolutions:
                    if w >= 800 and h >= 600:  # Минимальные требования
                        valid_count += 1
                
                print(f"\n✅ Результаты:")
                print(f"   Валидных разрешений: {valid_count}/{len(filtered_resolutions)}")
                print(f"   Минимальные требования соблюдены: {'✅' if valid_count > 0 else '❌'}")
                
                self.results['resolution_system'] = {
                    'total_resolutions': len(filtered_resolutions),
                    'valid_resolutions': valid_count,
                    'current_resolution': (game_config.screen_width, game_config.screen_height),
                    'status': '✅ УСПЕХ' if valid_count > 0 else '❌ ОШИБКА'
                }
                
                return valid_count > 0
                
            except Exception as e:
                print(f"❌ ОШИБКА при тестировании системы разрешений: {e}")
                self.results['resolution_system'] = {'status': '❌ ОШИБКА', 'error': str(e)}
                return False
        
        def test_dynamic_resolution(self):
            """Интерактивный тест динамического изменения разрешения"""
            print("\n🔄 ТЕСТ 3: Динамическое изменение разрешения")
            print("=" * 60)
            
            try:
                pygame.init()
                pygame.display.set_caption('Тест динамического разрешения - Tetris Enhanced')
                
                # Набор тестовых разрешений
                test_resolutions = [
                    (800, 600, "Минимальное 4:3"),
                    (1024, 768, "Стандартное 4:3"),
                    (1280, 720, "HD 16:9"),
                    (1366, 768, "Популярное 16:9"),
                    (1600, 900, "Высокое 16:9"),
                    (1920, 1080, "Full HD 16:9")
                ]
                
                print("🎮 Интерактивный режим:")
                print("   ПРОБЕЛ - переключить разрешение")
                print("   ESC - завершить тест")
                print("   Наблюдайте за адаптацией элементов интерфейса\n")
                
                current_index = 0
                screen = pygame.display.set_mode(test_resolutions[current_index][:2])
                clock = pygame.time.Clock()
                
                # Создаем шрифты
                font = pygame.font.SysFont('arial,segoeui,helvetica', 24, bold=True)
                small_font = pygame.font.SysFont('arial,segoeui,helvetica', 16)
                
                print(f"🚀 Начальное разрешение: {test_resolutions[current_index][2]}")
                
                test_count = 0
                running = True
                
                while running and test_count < 10:  # Максимум 10 переключений для демо
                    dt = clock.tick(60) / 1000.0
                    
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                running = False
                            elif event.key == pygame.K_SPACE:
                                # Переключение разрешения
                                current_index = (current_index + 1) % len(test_resolutions)
                                new_resolution = test_resolutions[current_index][:2]
                                
                                print(f"🔄 Переключение на: {test_resolutions[current_index][2]} ({new_resolution[0]}x{new_resolution[1]})")
                                
                                # Применяем новое разрешение
                                new_screen = apply_resolution_change(screen, new_resolution)
                                if new_screen:
                                    screen = new_screen
                                    test_count += 1
                                    print(f"   ✅ Успешно применено: {screen.get_size()}")
                                else:
                                    print(f"   ❌ Ошибка при изменении разрешения")
                    
                    # Отрисовка демонстрационного интерфейса
                    screen.fill((25, 30, 40))
                    
                    # Информация о текущем разрешении
                    current_res = screen.get_size()
                    res_text = font.render(f"Разрешение: {current_res[0]}x{current_res[1]}", True, (255, 255, 255))
                    screen.blit(res_text, (20, 20))
                    
                    # Информация об адаптивности
                    if 'responsive' in globals() and globals()['responsive']:
                        responsive = globals()['responsive']
                        y_offset = 60
                        texts = [
                            f"Класс устройства: {responsive.device_class}",
                            f"Тип экрана: {responsive.aspect_type}",
                            f"Категория DPI: {responsive.dpi_category}",
                            f"Масштаб шрифтов: {responsive.scale_factors['font']:.2f}x",
                            f"Масштаб UI: {responsive.scale_factors['ui']:.2f}x"
                        ]
                        
                        for text in texts:
                            text_surface = small_font.render(text, True, (200, 220, 240))
                            screen.blit(text_surface, (20, y_offset))
                            y_offset += 22
                    
                    # Инструкции и статистика
                    instr_text = small_font.render("ПРОБЕЛ - переключить | ESC - выход", True, (150, 170, 200))
                    screen.blit(instr_text, (20, current_res[1] - 60))
                    
                    count_text = small_font.render(f"Тестов: {test_count}/10 | Разрешение {current_index + 1}/{len(test_resolutions)}", True, (100, 150, 200))
                    screen.blit(count_text, (20, current_res[1] - 40))
                    
                    pygame.display.flip()
                
                pygame.quit()
                
                print(f"\n📊 Результаты динамического тестирования:")
                print(f"   Выполнено переключений: {test_count}")
                print(f"   Тест {'✅ УСПЕШЕН' if test_count > 0 else '❌ НЕ ЗАВЕРШЕН'}")
                
                self.results['dynamic_resolution'] = {
                    'switches_performed': test_count,
                    'status': '✅ УСПЕХ' if test_count > 0 else '❌ НЕ ЗАВЕРШЕН'
                }
                
                return test_count > 0
                
            except Exception as e:
                print(f"❌ ОШИБКА в динамическом тесте: {e}")
                self.results['dynamic_resolution'] = {'status': '❌ ОШИБКА', 'error': str(e)}
                return False
        
        def run_demo_mode(self):
            """Демонстрационный режим - показывает все возможности"""
            print("\n🎪 ДЕМОНСТРАЦИОННЫЙ РЕЖИМ")
            print("=" * 60)
            print("Автоматическая демонстрация всех возможностей системы...")
            
            # Автоматическое тестирование различных конфигураций
            demo_configs = [
                {"width": 1920, "height": 1080, "name": "Full HD Gaming"},
                {"width": 2560, "height": 1440, "name": "2K Gaming"},
                {"width": 3440, "height": 1440, "name": "Ultrawide Gaming"},
                {"width": 1024, "height": 768, "name": "Retro 4:3"}
            ]
            
            for i, config in enumerate(demo_configs, 1):
                print(f"\n🎬 Демо {i}/{len(demo_configs)}: {config['name']}")
                print("-" * 40)
                
                try:
                    responsive = AdvancedResponsiveDesign(config['width'], config['height'])
                    
                    print(f"   📱 Устройство: {responsive.device_class}")
                    print(f"   📐 Экран: {responsive.aspect_type}")
                    print(f"   🔍 DPI: {responsive.dpi_category}")
                    print(f"   📏 Масштабы: UI {responsive.scale_factors['ui']:.2f}x, Шрифт {responsive.scale_factors['font']:.2f}x")
                    
                    # Имитация игрового интерфейса
                    font_size = responsive.scale_font(24)
                    button_height = responsive.get_button_height()
                    margin = responsive.get_margin(20)
                    
                    origin_x, origin_y, field_w, field_h, block_size = responsive.get_grid_position()
                    
                    print(f"   🎮 Игровое поле: {field_w}x{field_h} (блок {block_size}px)")
                    print(f"   🔘 Кнопки: высота {button_height}px")
                    print(f"   📝 Шрифт интерфейса: {font_size}px")
                    
                    time.sleep(0.5)  # Небольшая пауза для наглядности
                    
                except Exception as e:
                    print(f"   ❌ Ошибка в демо: {e}")
            
            print(f"\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
        
        def run_all_tests(self):
            """Запускает все тесты"""
            print("🧪 ЗАПУСК ВСЕХ ТЕСТОВ")
            print("=" * 60)
            
            results = []
            
            # Тест 1: Адаптивный дизайн
            results.append(self.test_adaptive_design())
            
            # Тест 2: Система разрешений
            results.append(self.test_resolution_system())
            
            # Итоговый отчет
            print(f"\n📋 ИТОГОВЫЙ ОТЧЕТ")
            print("=" * 60)
            
            success_count = sum(results)
            total_tests = len(results)
            
            print(f"✅ Успешных тестов: {success_count}/{total_tests}")
            print(f"❌ Неудачных тестов: {total_tests - success_count}/{total_tests}")
            
            if success_count == total_tests:
                print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
                print("   Система готова к использованию!")
            else:
                print(f"\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
                print("   Требуется дополнительная отладка")
            
            # Детальные результаты
            print(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
            for test_name, test_result in self.results.items():
                print(f"   {test_name}: {test_result.get('status', 'N/A')}")
            
            return success_count == total_tests

    def main():
        """Главная функция с обработкой аргументов командной строки"""
        parser = argparse.ArgumentParser(description='Система тестирования Tetris Enhanced')
        parser.add_argument('--test', choices=['adaptive', 'resolution', 'dynamic'], 
                          help='Запустить конкретный тест')
        parser.add_argument('--demo', action='store_true', 
                          help='Запустить демонстрационный режим')
        
        args = parser.parse_args()
        
        test_suite = TetrisTestSuite()
        
        if args.demo:
            test_suite.run_demo_mode()
        elif args.test == 'adaptive':
            test_suite.test_adaptive_design()
        elif args.test == 'resolution':
            test_suite.test_resolution_system()
        elif args.test == 'dynamic':
            test_suite.test_dynamic_resolution()
        else:
            # По умолчанию запускаем все тесты (кроме интерактивного)
            test_suite.run_all_tests()
            
            # Предлагаем запустить интерактивный тест
            print(f"\n💡 ДОПОЛНИТЕЛЬНО:")
            print("   Для интерактивного теста динамического разрешения:")
            print("   python tetris_tests.py --test dynamic")

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"ОШИБКА ИМПОРТА: {e}")
    print("Убедитесь, что pygame установлен и tetris_enhanced.py находится в той же папке.")
    print("Установка pygame: pip install pygame")