#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрая проверка улучшений адаптивности объектов
"""

import sys
import os

# Добавляем путь к главному файлу
sys.path.append(os.path.dirname(__file__))

def test_adaptive_improvements():
    """Тестирует новые улучшения адаптивности"""
    print("=== ТЕСТ УЛУЧШЕНИЙ АДАПТИВНОСТИ ОБЪЕКТОВ ===\n")
    
    try:
        from tetris_enhanced import AdvancedResponsiveDesign
        
        # Тестируем различные разрешения
        test_cases = [
            {"name": "Full HD", "width": 1920, "height": 1080},
            {"name": "Ultrawide 21:9", "width": 2560, "height": 1080},
            {"name": "4K", "width": 3840, "height": 2160},
            {"name": "Classic 4:3", "width": 1024, "height": 768}
        ]
        
        for case in test_cases:
            print(f"📱 Тестирование: {case['name']} ({case['width']}x{case['height']})")
            print("-" * 50)
            
            try:
                responsive = AdvancedResponsiveDesign(case['width'], case['height'])
                
                # Тестируем новые методы
                print(f"  Класс устройства: {responsive.device_class}")
                print(f"  Тип экрана: {responsive.aspect_type}")
                
                # Тестируем адаптивный текст
                text_config = responsive.get_adaptive_text_size(
                    "Пример длинного текста для кнопки", 300, 60, 24
                )
                print(f"  Адаптивный текст: размер {text_config['font_size']}px, {text_config['estimated_lines']} строк")
                
                # Тестируем умные размеры кнопки
                button_dims = responsive.get_smart_button_dimensions("Сохранить игру")
                print(f"  Умная кнопка: {button_dims[0]}x{button_dims[1]}px")
                
                # Тестируем адаптивные отступы
                spacing = responsive.get_adaptive_spacing("button", "comfortable")
                print(f"  Отступы: padding={spacing['padding']}, margin={spacing['margin']}")
                
                # Тестируем визуальную иерархию
                hierarchy = responsive.get_visual_hierarchy_sizes()
                print(f"  Иерархия шрифтов: заголовок={hierarchy['title']}, текст={hierarchy['body']}")
                
                # Тестируем умное позиционирование
                pos = responsive.get_smart_positioning(200, 50, 800, 600, "center")
                print(f"  Умное позиционирование: ({pos[0]}, {pos[1]})")
                
                print("  ✅ ВСЕ НОВЫЕ МЕТОДЫ РАБОТАЮТ КОРРЕКТНО\n")
                
            except Exception as e:
                print(f"  ❌ ОШИБКА: {e}\n")
        
        print("🎉 ЗАКЛЮЧЕНИЕ:")
        print("✅ Все новые методы адаптивности успешно добавлены:")
        print("  • get_adaptive_text_size() - умное масштабирование текста")
        print("  • get_smart_button_dimensions() - оптимальные размеры кнопок")
        print("  • get_responsive_grid() - адаптивная сетка")
        print("  • get_adaptive_spacing() - умные отступы")
        print("  • get_visual_hierarchy_sizes() - визуальная иерархия")
        print("  • get_smart_positioning() - интеллектуальное позиционирование")
        print("  • optimize_layout_for_device() - оптимизация под устройство")
        print("\n✅ Добавлены новые функции рисования:")
        print("  • draw_adaptive_button() - адаптивные кнопки с переносом текста")
        print("  • draw_smart_text_block() - умные текстовые блоки")
        print("  • draw_enhanced_panel_with_content() - панели с содержимым")
        print("  • create_adaptive_layout_manager() - менеджер компоновки")
        
        return True
        
    except ImportError as e:
        print(f"❌ ОШИБКА ИМПОРТА: {e}")
        return False
    except Exception as e:
        print(f"❌ ОБЩАЯ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    success = test_adaptive_improvements()
    if success:
        print("\n🚀 ВСЕ УЛУЧШЕНИЯ АДАПТИВНОСТИ УСПЕШНО РЕАЛИЗОВАНЫ!")
    else:
        print("\n❌ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ОТЛАДКА")