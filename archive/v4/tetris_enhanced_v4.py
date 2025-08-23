"""
TETRIS ENHANCED — итоговый файл проекта (на русском)
Описание:
    Улучшенная одностраничная реализация игры Tetris на Python c использованием pygame.
    Включает:
      - проигрывание фоновой музыки из папки music/ (mp3/ogg/wav);
      - звуковые эффекты из папки sounds/ (rotate.wav, drop.wav, line.wav);
      - стартовое меню выбора уровня и трека;
      - меню паузы c кнопками Продолжить / Сохранить / Загрузить / Следующая / Предыдущая / Выйти;
      - сохранение и загрузка состояния в JSON-файл (saves/tetris_save.json);
      - механика Hold, ghost-piece, комбо и back-to-back, базовая обработка T-Spin;
      - настраиваемые контролы: стрелки, Z/X/A/S, Space, C/Shift, P, R, Esc/Q.

Установка и запуск:
    1) Убедитесь, что установлен Python 3.7+.
    2) Установите pygame:
         pip install pygame
    3) Создайте папки рядом со скриптом:
         music/   - поместите mp3/ogg/wav треки
         sounds/  - поместите wav-файлы эффектов: rotate.wav, drop.wav, line.wav
         saves/   - будет создана автоматически для сохранений
    4) Запустите:
         python tetris_enhanced.py

Формат сохранения:
    Состояние игры сохраняется в JSON в папке saves/ и содержит простые типы (grid, next_queue, bag, current, hold, score, level и т.д.).
    Это позволяет при необходимости вручную редактировать или переносить файл.

Авторство и лицензия:
    Дуплей Максим Игоревич (17.07.1999)
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Tetris (single-file) — pygame

Улучшения по запросу пользователя:
 - Фоновая музыка (сканируется папка music/ для mp3/ogg/wav)
 - Простые звуковые эффекты (если есть файлы в ./sounds/)
 - Сохранение/загрузка игры в JSON (saves/tetris_save.json)
 - Стартовое меню выбора уровня и музыкального трека
 - Меню паузы с кнопками: Продолжить, Сохранить, Загрузить, Следующая музыка, Предыдущая, Выйти
 - Меню выбора разрешения экрана

Положите свои mp3 (перечисленные вами) в папку ./music/
и wav-эффекты в ./sounds/ (rotate.wav, drop.wav, line.wav)

Запуск:
    pip install pygame
    python tetris_enhanced.py
"""
import os
import sys
import json
import random
import time
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

try:
    import pygame
except Exception:
    print("This script requires pygame. Install with: pip install pygame")
    raise

# -------------------- Централизованная конфигурация игры --------------------
@dataclass
class GameConfig:
    """
    Централизованная система конфигурации для управления всеми настраиваемыми параметрами игры.
    Обеспечивает легкое изменение, настройку и лучшую модификацию поведения игры.
    """
    
    # Настройки экрана и разрешения
    screen_width: int = 1366
    screen_height: int = 768
    fullscreen: bool = False
    vsync: bool = True
    fps_target: int = 60
    
    # Доступные разрешения
    available_resolutions: List[Tuple[int, int]] = field(default_factory=lambda: [
        (800, 600),    # 4:3 Минимальное
        (1024, 768),   # 4:3 Стандарт
        (1280, 720),   # 16:9 HD
        (1280, 800),   # 16:10
        (1366, 768),   # 16:9 Популярное
        (1440, 900),   # 16:10
        (1600, 900),   # 16:9
        (1680, 1050),  # 16:10
        (1920, 1080),  # 16:9 Full HD
        (2560, 1440),  # 16:9 2K
        (3840, 2160),  # 16:9 4K
    ])
    
    # Настройки адаптивного дизайна
    enable_adaptive_design: bool = True
    ui_scale_factor: float = 1.0
    font_scale_multiplier: float = 1.0
    button_scale_multiplier: float = 1.0
    margin_scale_multiplier: float = 1.0
    
    # Настройки игрового поля
    game_field_cols: int = 10
    game_field_rows: int = 20
    block_size_base: int = 32
    
    # Настройки аудио
    enable_audio: bool = True
    music_volume: float = 0.7
    sound_volume: float = 0.8
    
    # Настройки производительности
    enable_animations: bool = True
    enable_shadows: bool = True
    render_quality: str = "high"  # "low", "medium", "high"
    cache_size_multiplier: float = 1.0
    
    # Настройки игрового процесса
    auto_save_enabled: bool = True
    auto_save_interval: int = 300  # секунд
    show_debug_info: bool = False
    
    @classmethod
    def load_from_file(cls, filename: str = "config.json") -> "GameConfig":
        """Загружает конфигурацию из файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**data)
        except Exception as e:
            print(f"[Конфиг] Ошибка загрузки конфигурации: {e}")
        return cls()  # Возвращаем стандартную конфигурацию
    
    def save_to_file(self, filename: str = "config.json") -> None:
        """Сохраняет конфигурацию в файл"""
        try:
            # Преобразуем dataclass в словарь для JSON
            config_dict = {
                'screen_width': self.screen_width,
                'screen_height': self.screen_height,
                'fullscreen': self.fullscreen,
                'vsync': self.vsync,
                'fps_target': self.fps_target,
                'enable_adaptive_design': self.enable_adaptive_design,
                'ui_scale_factor': self.ui_scale_factor,
                'font_scale_multiplier': self.font_scale_multiplier,
                'button_scale_multiplier': self.button_scale_multiplier,
                'margin_scale_multiplier': self.margin_scale_multiplier,
                'enable_audio': self.enable_audio,
                'music_volume': self.music_volume,
                'sound_volume': self.sound_volume,
                'enable_animations': self.enable_animations,
                'enable_shadows': self.enable_shadows,
                'render_quality': self.render_quality,
                'auto_save_enabled': self.auto_save_enabled,
                'auto_save_interval': self.auto_save_interval,
                'show_debug_info': self.show_debug_info
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            print(f"[Конфиг] Конфигурация сохранена в {filename}")
        except Exception as e:
            print(f"[Конфиг] Ошибка сохранения: {e}")
    
    def get_aspect_ratio(self) -> float:
        """Возвращает соотношение сторон экрана"""
        return self.screen_width / self.screen_height
    
    def get_filtered_resolutions(self, min_width: int = 800, min_height: int = 600) -> List[Tuple[int, int]]:
        """Возвращает широкий список подходящих разрешений"""
        try:
            pygame.init()
            display_info = pygame.display.Info()
            max_width = display_info.current_w
            max_height = display_info.current_h
            
            # Очень щедрая фильтрация - показываем все разрешения до 1920x1080, а выше - только если экран позволяет
            filtered = []
            for w, h in self.available_resolutions:
                fits_min = w >= min_width and h >= min_height
                # Коммон резолушнс до 1920x1080 всегда доступны
                if w <= 1920 and h <= 1080:
                    fits_max = True  # Обычные разрешения всегда доступны
                else:
                    # Только высокие разрешения ограничиваем по размеру экрана
                    fits_max = w <= int(max_width * 1.1) and h <= int(max_height * 1.1)
                
                if fits_min and fits_max:
                    filtered.append((w, h))
            
            # Если получилось мало разрешений, добавляем безопасные варианты
            if len(filtered) < 3:
                safe_resolutions = [
                    (800, 600), (1024, 768), (1280, 720), (1280, 800),
                    (1366, 768), (1440, 900), (1600, 900)
                ]
                for w, h in safe_resolutions:
                    if (w, h) not in filtered and w <= max_width and h <= max_height:
                        filtered.append((w, h))
            
            return sorted(filtered, key=lambda x: x[0] * x[1])  # Сортируем по площади
            
        except Exception as e:
            # Фалбэк: возвращаем стандартный набор разрешений
            fallback = [
                (800, 600), (1024, 768), (1280, 720), (1280, 800),
                (1366, 768), (1440, 900), (1600, 900), (1920, 1080)
            ]
            return fallback

# Глобальная конфигурация
game_config = GameConfig.load_from_file()  # Загружаем сохраненную конфигурацию

# -------------------- Game Modes --------------------
class GameMode(Enum):
    """Перечисление игровых режимов"""
    CAMPAIGN = "campaign"      # Кампания - прохождение уровней с целями
    ENDLESS_IMMERSIVE = "endless_immersive"  # Бесконечный иммерсивный режим
    ENDLESS_RELAXED = "endless_relaxed"      # Бесконечный релакс режим

@dataclass
class LevelObjective:
    """Цель уровня в кампании"""
    type: str  # "lines", "score", "time", "survive"
    target: int  # Целевое значение
    description: str  # Описание цели

@dataclass
class CampaignLevel:
    """Уровень кампании"""
    level_num: int
    name: str
    description: str
    objectives: List[LevelObjective]
    starting_level: int  # Начальный уровень скорости
    max_level: int  # Максимальный уровень для этого этапа
    unlocked: bool = False
    completed: bool = False
    best_score: int = 0
    best_time: float = 0.0

@dataclass
class GameModeConfig:
    """Конфигурация игрового режима"""
    mode: GameMode
    name: str
    description: str
    gravity_multiplier: float = 1.0  # Множитель скорости падения
    scoring_multiplier: float = 1.0  # Множитель очков
    level_progression: bool = True   # Автоматическое повышение уровня
    max_level: Optional[int] = None  # Максимальный уровень (None = без лимита)

# Конфигурации режимов игры
GAME_MODE_CONFIGS = {
    GameMode.CAMPAIGN: GameModeConfig(
        mode=GameMode.CAMPAIGN,
        name="Кампания",
        description="Пройдите уровни с различными целями",
        gravity_multiplier=1.0,
        scoring_multiplier=1.2,
        level_progression=False  # Управляется целями уровня
    ),
    GameMode.ENDLESS_IMMERSIVE: GameModeConfig(
        mode=GameMode.ENDLESS_IMMERSIVE,
        name="Бесконечный (Иммерсивный)",
        description="Вызов для опытных игроков",
        gravity_multiplier=1.3,
        scoring_multiplier=1.5,
        level_progression=True
    ),
    GameMode.ENDLESS_RELAXED: GameModeConfig(
        mode=GameMode.ENDLESS_RELAXED,
        name="Бесконечный (Релакс)",
        description="Спокойная игра без спешки",
        gravity_multiplier=0.7,
        scoring_multiplier=1.0,
        level_progression=False,
        max_level=10  # Ограничиваем максимальную скорость
    )
}

# Кампания - определение уровней
CAMPAIGN_LEVELS = [
    CampaignLevel(
        level_num=1,
        name="Первые шаги",
        description="Освойте основы игры",
        objectives=[
            LevelObjective("lines", 5, "Очистите 5 линий")
        ],
        starting_level=1,
        max_level=3,
        unlocked=True
    ),
    CampaignLevel(
        level_num=2,
        name="Набираем обороты",
        description="Покажите своё мастерство",
        objectives=[
            LevelObjective("lines", 10, "Очистите 10 линий"),
            LevelObjective("score", 5000, "Наберите 5000 очков")
        ],
        starting_level=2,
        max_level=5,
        unlocked=False
    ),
    CampaignLevel(
        level_num=3,
        name="Под давлением",
        description="Выживание на высокой скорости",
        objectives=[
            LevelObjective("time", 180, "Продержитесь 3 минуты"),
            LevelObjective("lines", 15, "Очистите 15 линий")
        ],
        starting_level=5,
        max_level=8,
        unlocked=False
    ),
    CampaignLevel(
        level_num=4,
        name="Мастер Тетриса",
        description="Финальное испытание",
        objectives=[
            LevelObjective("score", 25000, "Наберите 25000 очков"),
            LevelObjective("lines", 25, "Очистите 25 линий")
        ],
        starting_level=8,
        max_level=15,
        unlocked=False
    )
]
# -------------------- Улучшенная адаптивная дизайн система --------------------
class AdvancedResponsiveDesign:
    """
    Кардинально улучшенная система адаптивного дизайна с интеллектуальным
    определением устройств, DPI-масштабированием и оптимизированным кэшированием.
    """
    
    def __init__(self, screen_width: int, screen_height: int, dpi: float = 96.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.dpi = dpi
        self.total_pixels = screen_width * screen_height
        
        # Интеллектуальное определение класса устройства
        self.device_class = self._detect_device_class()
        
        # Улучшенное определение соотношения сторон
        self.aspect_ratio = screen_width / screen_height
        self.aspect_type = self._detect_aspect_type_enhanced()
        
        # Определение категории DPI
        self.dpi_category = self._detect_dpi_category()
        
        # Вычисление интеллектуальных базовых размеров
        self.base_width, self.base_height = self._calculate_base_dimensions()
        
        # Умные коэффициенты масштабирования
        self.scale_factors = self._calculate_intelligent_scaling()
        
        # Централизованная система кэширования
        self._unified_cache = {
            'fonts': {},
            'surfaces': {},
            'margins': {},
            'layouts': {},
            'adaptive_fonts': {}
        }
        
        # Настройки производительности на основе устройства
        self.performance_profile = self._get_performance_profile()
        
        print(f"[AdvancedResponsiveDesign] Initialized for {screen_width}x{screen_height}")
        print(f"[AdvancedResponsiveDesign] Device: {self.device_class}, Aspect: {self.aspect_type}, DPI: {self.dpi_category}")
        print(f"[AdvancedResponsiveDesign] Scale factors: {self.scale_factors}")
    
    def _detect_device_class(self) -> str:
        """Интеллектуальное определение класса устройства"""
        # Определяем по общему количеству пикселей и соотношению сторон
        if self.total_pixels >= 8294400:  # 4K+ (3840x2160)
            return "ultra_high"
        elif self.total_pixels >= 2073600:  # 1920x1080+
            return "high"
        elif self.total_pixels >= 1048576:  # 1024x1024+
            return "medium"
        else:
            return "low"
    
    def _detect_aspect_type_enhanced(self) -> str:
        """Улучшенное определение соотношения сторон с поддержкой современных форматов"""
        ratio = self.aspect_ratio
        
        # Расширенная поддержка соотношений сторон
        aspect_ratios = {
            32/9: "32:9",     # Супер-ультраширокие
            21/9: "21:9",     # Ультраширокие
            16/9: "16:9",     # Широкие
            16/10: "16:10",   # Широкие 16:10
            3/2: "3:2",       # Классические
            4/3: "4:3",       # Квадратные
            5/4: "5:4"        # Почти квадратные
        }
        
        # Находим ближайшее соотношение с допуском
        tolerance = 0.1
        for target_ratio, aspect_name in aspect_ratios.items():
            if abs(ratio - target_ratio) < tolerance:
                return aspect_name
        
        return "custom"
    
    def _detect_dpi_category(self) -> str:
        """Определение категории DPI для правильного масштабирования"""
        if self.dpi >= 144:
            return "high_dpi"     # Retina/4K дисплеи
        elif self.dpi >= 120:
            return "medium_dpi"   # Промежуточные дисплеи
        else:
            return "low_dpi"      # Стандартные дисплеи
    
    def _calculate_base_dimensions(self) -> tuple:
        """Вычисление интеллектуальных базовых размеров"""
        # Базовые размеры зависят от класса устройства и соотношения сторон
        base_configs = {
            "ultra_high": {"16:9": (1920, 1080), "21:9": (2560, 1080), "4:3": (1600, 1200)},
            "high": {"16:9": (1600, 900), "21:9": (1720, 720), "4:3": (1280, 960)},
            "medium": {"16:9": (1280, 720), "21:9": (1440, 600), "4:3": (1024, 768)},
            "low": {"16:9": (1024, 576), "21:9": (1200, 500), "4:3": (800, 600)}
        }
        
        config = base_configs.get(self.device_class, base_configs["medium"])
        return config.get(self.aspect_type, config.get("16:9", (1280, 720)))
    
    def _calculate_intelligent_scaling(self) -> dict:
        """Вычисление умных коэффициентов масштабирования"""
        # Базовые коэффициенты
        scale_x = self.screen_width / self.base_width
        scale_y = self.screen_height / self.base_height
        scale_avg = (scale_x + scale_y) / 2
        scale_uniform = min(scale_x, scale_y)
        
        # Интеллектуальные ограничения на основе класса устройства
        limits = {
            "ultra_high": {"min": 0.8, "max": 3.0},
            "high": {"min": 0.7, "max": 2.5},
            "medium": {"min": 0.6, "max": 2.0},
            "low": {"min": 0.5, "max": 1.8}
        }
        
        device_limits = limits.get(self.device_class, limits["medium"])
        
        # DPI корректировка
        dpi_multiplier = {
            "high_dpi": 1.4,
            "medium_dpi": 1.2,
            "low_dpi": 1.0
        }.get(self.dpi_category, 1.0)
        
        # Применяем ограничения и DPI коррекцию
        font_scale = max(device_limits["min"], min(device_limits["max"], scale_avg * dpi_multiplier * 1.4))
        ui_scale = max(device_limits["min"], min(device_limits["max"], scale_uniform * 1.3))
        
        return {
            'x': scale_x,
            'y': scale_y,
            'avg': scale_avg,
            'uniform': scale_uniform,
            'font': font_scale,
            'ui': ui_scale
        }
    
    def _get_performance_profile(self) -> dict:
        """Получение профиля производительности"""
        profiles = {
            "ultra_high": {"fps_target": 120, "max_cache_items": 200},
            "high": {"fps_target": 60, "max_cache_items": 150},
            "medium": {"fps_target": 60, "max_cache_items": 100},
            "low": {"fps_target": 45, "max_cache_items": 50}
        }
        return profiles[self.device_class]
    
    def _manage_cache_size(self):
        """Управление размером кэша"""
        max_items = self.performance_profile["max_cache_items"]
        for cache_type, cache in self._unified_cache.items():
            if len(cache) > max_items:
                items_to_remove = len(cache) - max_items + 10
                for _ in range(items_to_remove):
                    if cache:
                        cache.pop(next(iter(cache)))
    
    # ================ Методы компоновки и позиционирования ================
    
    def scale_size_uniform(self, base_size: int) -> int:
        """Масштабирует размер равномерно, сохраняя пропорции"""
        return int(base_size * self.scale_factors['uniform'])
    
    def scale_width(self, base_width: int) -> int:
        """Масштабирует ширину"""
        return int(base_width * self.scale_factors['x'])
    
    def scale_height(self, base_height: int) -> int:
        """Масштабирует высоту"""
        return int(base_height * self.scale_factors['y'])
    
    def scale_size(self, base_size: int) -> int:
        """Масштабирует размер средним коэффициентом"""
        return int(base_size * self.scale_factors['avg'])
    
    def get_margin(self, base_margin: int) -> int:
        """Масштабирует отступы"""
        if base_margin in self._unified_cache['margins']:
            return self._unified_cache['margins'][base_margin]
        
        margin = max(5, int(base_margin * self.scale_factors['ui']))
        if self.aspect_type in ["21:9", "32:9"]: 
            margin = int(margin * 1.2)
        elif self.aspect_type in ["4:3", "5:4"]: 
            margin = int(margin * 0.8)
        
        self._unified_cache['margins'][base_margin] = margin
        self._manage_cache_size()
        return margin
    
    def get_button_height(self, base_height: int = 70) -> int:
        """Возвращает оптимальную высоту кнопки"""
        scaled_height = max(40, int(base_height * self.scale_factors['ui']))
        if self.aspect_type in ["16:9", "21:9", "32:9"]: 
            scaled_height = int(scaled_height * 1.15)
        return scaled_height
    
    def get_panel_width(self, base_width: int) -> int:
        """Возвращает ширину панели"""
        scaled = self.scale_width(base_width)
        max_width_ratio = 0.85 if self.aspect_type == "4:3" else 0.9
        return min(scaled, int(self.screen_width * max_width_ratio))
    
    def get_optimal_layout(self) -> dict:
        """Возвращает оптимальную компоновку"""
        layouts = {
            "21:9": {"layout_type": "centered_wide", "side_margins": self.get_margin(120), "content_width_ratio": 0.6, "safe_area": {}},
            "32:9": {"layout_type": "centered_wide", "side_margins": self.get_margin(150), "content_width_ratio": 0.5, "safe_area": {}},
            "16:9": {"layout_type": "standard_wide", "side_margins": self.get_margin(60), "content_width_ratio": 0.8, "safe_area": {}},
            "4:3": {"layout_type": "compact", "side_margins": self.get_margin(30), "content_width_ratio": 0.95, "safe_area": {}}
        }
        default_layout = {"layout_type": "standard", "side_margins": self.get_margin(50), "content_width_ratio": 0.85, "safe_area": {}}
        
        layout = layouts.get(self.aspect_type, default_layout)
        
        # Добавляем безопасную область
        layout["safe_area"] = {
            'x': layout["side_margins"],
            'y': self.get_margin(20),
            'width': self.screen_width - 2 * layout["side_margins"],
            'height': self.screen_height - 2 * self.get_margin(20)
        }
        
        return layout
    
    def get_rect(self, x: int, y: int, width: int, height: int):
        """Создаёт pygame.Rect с масштабированными координатами"""
        import pygame
        return pygame.Rect(x, y, width, height)
    def scale_font(self, base_font_size: int) -> int:
        """Интеллектуальное масштабирование шрифтов с кэшированием"""
        if base_font_size in self._unified_cache['fonts']:
            return self._unified_cache['fonts'][base_font_size]
        
        # Применяем интеллектуальный множитель
        scaled = int(base_font_size * self.scale_factors['font'])
        
        # Ограничения на основе класса устройства
        limits = {
            "ultra_high": {"min": 24, "max": 200},
            "high": {"min": 20, "max": 150},
            "medium": {"min": 16, "max": 120},
            "low": {"min": 12, "max": 80}
        }[self.device_class]
        
        scaled = max(limits["min"], min(limits["max"], scaled))
        
        # Кэшируем результат
        self._unified_cache['fonts'][base_font_size] = scaled
        self._manage_cache_size()
        
        return scaled
    
    def get_grid_position(self):
        """Возвращает оптимальную позицию и размеры игрового поля"""
        # Базовые параметры
        cols, rows = 10, 20
        base_block_size = 32 if self.aspect_type == "16:9" else 30
        
        # Масштабирование размера блока
        block_size = max(15, self.scale_size_uniform(base_block_size))
        
        # Оптимизация для разных экранов
        if self.aspect_type == "4:3":
            # На квадратных экранах уменьшаем блоки
            block_size = max(12, int(block_size * 0.85))
        elif self.aspect_type == "21:9":
            # На ультрашироких экранах можно увеличить
            block_size = int(block_size * 1.1)
        
        # Размеры поля
        field_width = cols * block_size
        field_height = rows * block_size
        
        # Получаем оптимальную компоновку
        layout = self.get_optimal_layout()
        margin = self.get_margin(25)
        
        # Позиционирование в зависимости от типа экрана
        if layout["layout_type"] == "centered_wide":
            # Центрированное расположение для широких экранов
            available_width = self.screen_width - 2 * layout["side_margins"]
            origin_x = (self.screen_width - field_width) // 2
        else:
            # Обычное расположение слева
            origin_x = layout["side_margins"]
        
        # Вертикальное центрирование
        origin_y = max(margin, (self.screen_height - field_height) // 2)
        
        return origin_x, origin_y, field_width, field_height, block_size
    
    def get_performance_settings(self):
        """Возвращает оптимальные настройки производительности"""
        total_pixels = self.screen_width * self.screen_height
        
        # Определяем класс производительности
        if total_pixels >= 2073600:  # 1920x1080+
            performance_class = "high"
        elif total_pixels >= 1048576:  # 1024x1024+
            performance_class = "medium"
        else:
            performance_class = "low"
        
        settings = {
            "high": {
                "fps_target": 60,
                "enable_shadows": True,
                "enable_animations": True,
                "cache_size_multiplier": 1.5,
                "render_quality": "high"
            },
            "medium": {
                "fps_target": 60,
                "enable_shadows": True,
                "enable_animations": True,
                "cache_size_multiplier": 1.0,
                "render_quality": "medium"
            },
            "low": {
                "fps_target": 45,
                "enable_shadows": False,
                "enable_animations": False,
                "cache_size_multiplier": 0.7,
                "render_quality": "low"
            }
        }
        
        return settings[performance_class]
    
    def clear_caches(self):
        """Очищает все кэши"""
        for cache in self._unified_cache.values():
            cache.clear()
    
    def get_panel_position(self, field_x: int, field_width: int):
        """Возвращает оптимальную позицию и размеры боковой панели"""
        margin = self.get_margin(25)
        layout = self.get_optimal_layout()
        
        if layout["layout_type"] == "centered_wide":
            # Для широких экранов размещаем панель справа, но не слишком широко
            panel_x = field_x + field_width + margin * 2
            available_width = self.screen_width - panel_x - layout["side_margins"]
            panel_width = min(available_width, self.scale_width(350))
        else:
            # Обычное расположение
            panel_x = field_x + field_width + margin
            panel_width = self.screen_width - panel_x - margin
        
        # Минимальная и максимальная ширина панели
        min_panel_width = self.scale_width(180)
        max_panel_width = self.scale_width(400)
        panel_width = max(min_panel_width, min(max_panel_width, panel_width))
        
        return panel_x, margin, panel_width
    
    # ================ Улучшенные методы адаптивности объектов ================
    
    def get_adaptive_text_size(self, text: str, container_width: int, container_height: int, base_font_size: int = 24) -> dict:
        """Возвращает оптимальные параметры текста для контейнера"""
        cache_key = f"text_size_{hash(text)}_{container_width}_{container_height}_{base_font_size}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Базовый размер с учетом устройства
        scaled_base = self.scale_font(base_font_size)
        
        # Оценка оптимального размера
        char_width_ratio = 0.6  # Приблизительное отношение ширины символа к размеру шрифта
        estimated_char_width = scaled_base * char_width_ratio
        max_chars_per_line = max(1, int(container_width / estimated_char_width))
        
        # Адаптация под длину текста
        if len(text) > max_chars_per_line:
            # Текст не помещается в одну строку
            lines_needed = (len(text) + max_chars_per_line - 1) // max_chars_per_line
            available_height_per_line = container_height / lines_needed
            font_size = min(scaled_base, int(available_height_per_line * 0.8))
        else:
            # Текст помещается в одну строку
            font_size = scaled_base
        
        # Ограничения по устройству
        limits = {
            "ultra_high": {"min": 16, "max": 72},
            "high": {"min": 14, "max": 56},
            "medium": {"min": 12, "max": 42},
            "low": {"min": 10, "max": 36}
        }[self.device_class]
        
        font_size = max(limits["min"], min(limits["max"], font_size))
        
        result = {
            'font_size': font_size,
            'max_chars_per_line': max_chars_per_line,
            'estimated_lines': (len(text) + max_chars_per_line - 1) // max_chars_per_line,
            'line_height': int(font_size * 1.2)
        }
        
        self._unified_cache['layouts'][cache_key] = result
        return result
    
    def get_smart_button_dimensions(self, text: str, min_width: int = 120, min_height: int = 40) -> tuple:
        """Возвращает оптимальные размеры кнопки для текста"""
        cache_key = f"button_dims_{hash(text)}_{min_width}_{min_height}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Базовые размеры с учетом устройства
        base_height = self.get_button_height()
        padding_h = self.get_margin(20)
        padding_v = self.get_margin(10)
        
        # Оценка ширины текста
        estimated_font_size = self.scale_font(24)
        char_width = estimated_font_size * 0.6
        estimated_text_width = len(text) * char_width
        
        # Вычисление оптимальной ширины
        button_width = max(min_width, estimated_text_width + padding_h * 2)
        button_height = max(min_height, base_height + padding_v)
        
        # Адаптация под тип экрана
        if self.aspect_type in ["21:9", "32:9"]:
            button_width = int(button_width * 1.1)  # Немного шире для ультраширокий экранов
        elif self.aspect_type in ["4:3", "5:4"]:
            button_width = int(button_width * 0.9)  # Немного уже для квадратных экранов
        
        result = (button_width, button_height)
        self._unified_cache['layouts'][cache_key] = result
        return result
    
    def get_optimal_layout(self) -> dict:
        """Возвращает оптимальную компоновку для текущего экрана"""
        cache_key = f"layout_{self.screen_width}_{self.screen_height}_{self.aspect_type}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Анализ типа экрана и определение оптимальной компоновки
        if self.aspect_type in ["21:9", "32:9"]:
            # Ультраширокие экраны - центрированная компоновка
            layout_type = "centered_wide"
            side_margins = self.scale_width(150)  # Большие боковые отступы
            content_ratio = 0.7  # 70% экрана для контента
        elif self.aspect_type == "16:9" and self.device_class in ["high", "ultra_high"]:
            # Широкие экраны с высоким разрешением
            layout_type = "wide_optimized"
            side_margins = self.scale_width(80)
            content_ratio = 0.85
        elif self.aspect_type in ["4:3", "5:4"]:
            # Квадратные экраны - компактная компоновка
            layout_type = "compact"
            side_margins = self.scale_width(30)
            content_ratio = 0.95
        else:
            # Стандартная компоновка
            layout_type = "standard"
            side_margins = self.scale_width(50)
            content_ratio = 0.9
        
        # Вертикальные отступы
        top_margin = self.scale_height(40)
        bottom_margin = self.scale_height(30)
        
        layout = {
            'layout_type': layout_type,
            'side_margins': side_margins,
            'top_margin': top_margin,
            'bottom_margin': bottom_margin,
            'content_ratio': content_ratio,
            'safe_area': {
                'x': side_margins,
                'y': top_margin,
                'width': self.screen_width - 2 * side_margins,
                'height': self.screen_height - top_margin - bottom_margin
            }
        }
        
        self._unified_cache['layouts'][cache_key] = layout
        return layout
    
    def get_responsive_grid(self, total_items: int, container_width: int, container_height: int,
                           item_min_width: int = 120, item_min_height: int = 80,
                           max_columns: int = None) -> dict:
        """Возвращает оптимальную сетку для размещения элементов"""
        cache_key = f"grid_{total_items}_{container_width}_{container_height}_{item_min_width}_{item_min_height}_{max_columns}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Масштабирование минимальных размеров
        scaled_min_width = self.scale_width(item_min_width)
        scaled_min_height = self.scale_height(item_min_height)
        
        # Отступы между элементами
        gap_x = self.get_margin(15)
        gap_y = self.get_margin(10)
        
        # Определяем оптимальное количество колонок
        max_cols_by_width = (container_width + gap_x) // (scaled_min_width + gap_x)
        max_cols_by_aspect = {
            "21:9": 6, "32:9": 8, "16:9": 4, "16:10": 4, "4:3": 3, "5:4": 3
        }.get(self.aspect_type, 4)
        
        if max_columns:
            cols = min(max_columns, max_cols_by_width, max_cols_by_aspect)
        else:
            cols = min(max_cols_by_width, max_cols_by_aspect)
        
        cols = max(1, min(cols, total_items))  # Не больше чем элементов
        rows = (total_items + cols - 1) // cols
        
        # Вычисляем фактические размеры элементов
        available_width = container_width - (cols - 1) * gap_x
        available_height = container_height - (rows - 1) * gap_y
        
        item_width = max(scaled_min_width, available_width // cols)
        item_height = max(scaled_min_height, available_height // rows)
        
        # Оптимизация для малого количества элементов
        if total_items <= 3 and self.aspect_type in ["21:9", "32:9"]:
            # На ультрашироких экранах размещаем в одну строку
            cols = total_items
            rows = 1
            item_width = min(self.scale_width(250), available_width // cols)
        
        result = {
            'columns': cols,
            'rows': rows,
            'item_width': item_width,
            'item_height': item_height,
            'gap_x': gap_x,
            'gap_y': gap_y,
            'total_width': cols * item_width + (cols - 1) * gap_x,
            'total_height': rows * item_height + (rows - 1) * gap_y
        }
        
        self._unified_cache['layouts'][cache_key] = result
        return result
    
    def get_adaptive_spacing(self, context: str = "default") -> dict:
        """Возвращает адаптивные отступы для разных типов элементов"""
        cache_key = f"spacing_{context}_{self.device_class}_{self.aspect_type}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Базовые отступы для разных контекстов
        base_spacings = {
            "menu": {"padding": 20, "margin": 15, "spacing": 12},
            "button": {"padding": 15, "margin": 10, "spacing": 8},
            "panel": {"padding": 25, "margin": 20, "spacing": 15},
            "text": {"padding": 10, "margin": 8, "spacing": 6},
            "game": {"padding": 15, "margin": 12, "spacing": 10},
            "default": {"padding": 15, "margin": 12, "spacing": 10}
        }
        
        base = base_spacings.get(context, base_spacings["default"])
        
        # Масштабирование на основе устройства
        multipliers = {
            "ultra_high": 1.4,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }
        
        multiplier = multipliers.get(self.device_class, 1.0)
        
        # Коррекция для разных соотношений сторон
        if self.aspect_type in ["21:9", "32:9"]:
            multiplier *= 1.2  # Больше отступов на широких экранах
        elif self.aspect_type in ["4:3", "5:4"]:
            multiplier *= 0.9  # Меньше отступов на квадратных
        
        result = {
            'padding': max(8, int(base["padding"] * multiplier)),
            'margin': max(6, int(base["margin"] * multiplier)),
            'spacing': max(4, int(base["spacing"] * multiplier))
        }
        
        self._unified_cache['layouts'][cache_key] = result
        return result
    
    def get_visual_hierarchy_sizes(self) -> dict:
        """Возвращает размеры шрифтов для визуальной иерархии"""
        cache_key = f"hierarchy_{self.device_class}_{self.dpi_category}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Базовые размеры (модульная шкала 1.25)
        base_sizes = {
            "h1": 48,      # Основной заголовок
            "h2": 38,      # Вторичные заголовки
            "h3": 30,      # Подзаголовки
            "heading": 26, # Обычные заголовки
            "body": 20,    # Основной текст
            "caption": 16, # Подписи
            "small": 14    # Маленький текст
        }
        
        # Масштабирование с учетом агрессивного масштабирования
        result = {}
        for key, size in base_sizes.items():
            scaled_size = self.scale_font(size)
            
            # Минимальные размеры для читаемости (согласно memory)
            min_sizes = {
                "h1": 32, "h2": 26, "h3": 22, "heading": 20,
                "body": 18, "caption": 16, "small": 14
            }
            
            scaled_size = max(min_sizes.get(key, 14), scaled_size)
            result[key] = scaled_size
        
        self._unified_cache['layouts'][cache_key] = result
        return result
        self._unified_cache['layouts'][cache_key] = result
        return result
    
    def get_responsive_grid(self, items_count: int, container_width: int, container_height: int, 
                           item_min_width: int = 100, item_min_height: int = 60) -> dict:
        """Возвращает оптимальную сетку для размещения элементов"""
        cache_key = f"grid_{items_count}_{container_width}_{container_height}_{item_min_width}_{item_min_height}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Адаптивные отступы
        margin = self.get_margin(10)
        spacing = self.get_margin(8)
        
        # Вычисление оптимального количества колонок
        max_cols = max(1, (container_width + spacing) // (item_min_width + spacing))
        
        # Подбор оптимального количества колонок
        best_cols = 1
        best_score = float('inf')
        
        for cols in range(1, max_cols + 1):
            rows = (items_count + cols - 1) // cols
            
            # Вычисляем размеры элементов
            available_width = container_width - margin * 2 - spacing * (cols - 1)
            available_height = container_height - margin * 2 - spacing * (rows - 1)
            
            item_width = available_width // cols
            item_height = available_height // rows
            
            # Проверяем минимальные требования
            if item_width >= item_min_width and item_height >= item_min_height:
                # Оценка качества компоновки (предпочитаем квадратные элементы)
                aspect_ratio = item_width / item_height
                ideal_ratio = 1.6  # Золотое сечение
                ratio_score = abs(aspect_ratio - ideal_ratio)
                
                # Штраф за пустые ячейки
                empty_cells = cols * rows - items_count
                empty_penalty = empty_cells * 0.5
                
                total_score = ratio_score + empty_penalty
                
                if total_score < best_score:
                    best_score = total_score
                    best_cols = cols
        
        # Финальные вычисления
        final_rows = (items_count + best_cols - 1) // best_cols
        available_width = container_width - margin * 2 - spacing * (best_cols - 1)
        available_height = container_height - margin * 2 - spacing * (final_rows - 1)
        
        item_width = available_width // best_cols
        item_height = available_height // final_rows
        
        result = {
            'cols': best_cols,
            'rows': final_rows,
            'item_width': item_width,
            'item_height': item_height,
            'margin': margin,
            'spacing': spacing,
            'total_width': best_cols * item_width + spacing * (best_cols - 1),
            'total_height': final_rows * item_height + spacing * (final_rows - 1)
        }
        
        self._unified_cache['layouts'][cache_key] = result
        return result
    
    def get_adaptive_spacing(self, element_type: str, context: str = "default") -> dict:
        """Возвращает адаптивные отступы для различных типов элементов"""
        cache_key = f"spacing_{element_type}_{context}"
        
        if cache_key in self._unified_cache['layouts']:
            return self._unified_cache['layouts'][cache_key]
        
        # Базовые конфигурации отступов
        base_configs = {
            "button": {"padding": 15, "margin": 10, "spacing": 8},
            "panel": {"padding": 20, "margin": 15, "spacing": 12},
            "text": {"padding": 8, "margin": 6, "spacing": 4},
            "list_item": {"padding": 12, "margin": 8, "spacing": 6},
            "menu_item": {"padding": 16, "margin": 12, "spacing": 10}
        }
        
        base_config = base_configs.get(element_type, base_configs["button"])
        
        # Масштабирование с учетом устройства
        ui_scale = self.scale_factors['ui']
        
        # Адаптация под контекст
        context_multipliers = {
            "compact": 0.7,
            "comfortable": 1.3,
            "spacious": 1.6,
            "default": 1.0
        }
        
        context_mult = context_multipliers.get(context, 1.0)
        
        # Адаптация под тип экрана
        aspect_multipliers = {
            "32:9": 1.2,  # Больше места на ультраширокий экранах
            "21:9": 1.15,
            "16:9": 1.1,
            "16:10": 1.05,
            "4:3": 0.9,   # Меньше места на квадратных экранах
            "5:4": 0.95
        }
        
        aspect_mult = aspect_multipliers.get(self.aspect_type, 1.0)
        
        # Финальные вычисления
        final_multiplier = ui_scale * context_mult * aspect_mult
        
        result = {
            'padding': max(4, int(base_config["padding"] * final_multiplier)),
            'margin': max(3, int(base_config["margin"] * final_multiplier)),
            'spacing': max(2, int(base_config["spacing"] * final_multiplier))
        }
        
        self._unified_cache['layouts'][cache_key] = result
        return result
    
    def get_visual_hierarchy_sizes(self, base_size: int = 24) -> dict:
        """Возвращает размеры для создания визуальной иерархии"""
        cache_key = f"hierarchy_{base_size}"
        
        if cache_key in self._unified_cache['fonts']:
            return self._unified_cache['fonts'][cache_key]
        
        # Базовый размер с учетом устройства
        scaled_base = self.scale_font(base_size)
        
        # Иерархия размеров (на основе модульной шкалы)
        hierarchy = {
            'title': int(scaled_base * 2.0),      # Главный заголовок
            'subtitle': int(scaled_base * 1.5),   # Подзаголовок
            'heading': int(scaled_base * 1.25),   # Заголовок секции
            'body': scaled_base,                  # Основной текст
            'caption': int(scaled_base * 0.875),  # Подпись
            'small': int(scaled_base * 0.75)      # Мелкий текст
        }
        
        # Ограничения по устройству
        device_limits = {
            "ultra_high": {"min": 14, "max": 96},
            "high": {"min": 12, "max": 72},
            "medium": {"min": 10, "max": 56},
            "low": {"min": 8, "max": 42}
        }[self.device_class]
        
        # Применяем ограничения
        for key in hierarchy:
            hierarchy[key] = max(device_limits["min"], min(device_limits["max"], hierarchy[key]))
        
        self._unified_cache['fonts'][cache_key] = hierarchy
        return hierarchy
    
    def get_enhanced_positioning_system(self, elements: list, container_rect: tuple,
                                      positioning_strategy: str = "auto") -> list:
        """Продвинутая система позиционирования с предотвращением коллизий"""
        container_x, container_y, container_w, container_h = container_rect
        positioned_elements = []
        
        # Определяем стратегию позиционирования
        if positioning_strategy == "auto":
            if len(elements) <= 2:
                positioning_strategy = "centered_horizontal"
            elif len(elements) <= 6:
                positioning_strategy = "adaptive_grid"
            elif self.aspect_type in ["21:9", "32:9"]:
                positioning_strategy = "wide_flow"
            else:
                positioning_strategy = "optimal_grid"
        
        spacing = self.get_adaptive_spacing("menu", "comfortable")
        
        if positioning_strategy == "centered_horizontal":
            # Центрированное горизонтальное размещение
            total_width = sum(elem.get('width', 0) for elem in elements) + spacing['spacing'] * (len(elements) - 1)
            start_x = container_x + max(0, (container_w - total_width) // 2)
            current_x = start_x
            
            for elem in elements:
                elem_width = elem.get('width', 120)
                elem_height = elem.get('height', 40)
                y_pos = container_y + (container_h - elem_height) // 2
                
                positioned_elements.append({
                    **elem,
                    'x': current_x,
                    'y': y_pos,
                    'width': elem_width,
                    'height': elem_height
                })
                current_x += elem_width + spacing['spacing']
        
        elif positioning_strategy == "adaptive_grid":
            # Адаптивная сетка
            grid = self.get_responsive_grid(
                len(elements), container_w, container_h,
                item_min_width=120, item_min_height=40,
                max_columns=4 if self.aspect_type != "32:9" else 6
            )
            
            grid_start_x = container_x + (container_w - grid['total_width']) // 2
            grid_start_y = container_y + (container_h - grid['total_height']) // 2
            
            for i, elem in enumerate(elements):
                row = i // grid['columns']
                col = i % grid['columns']
                
                x_pos = grid_start_x + col * (grid['item_width'] + grid['gap_x'])
                y_pos = grid_start_y + row * (grid['item_height'] + grid['gap_y'])
                
                positioned_elements.append({
                    **elem,
                    'x': x_pos,
                    'y': y_pos,
                    'width': grid['item_width'],
                    'height': grid['item_height']
                })
        
        elif positioning_strategy == "wide_flow":
            # Потоковое размещение для широких экранов
            cols = min(len(elements), 8 if self.aspect_type == "32:9" else 6)
            rows = (len(elements) + cols - 1) // cols
            
            item_width = (container_w - spacing['spacing'] * (cols - 1)) // cols
            item_height = (container_h - spacing['spacing'] * (rows - 1)) // rows
            
            for i, elem in enumerate(elements):
                row = i // cols
                col = i % cols
                
                x_pos = container_x + col * (item_width + spacing['spacing'])
                y_pos = container_y + row * (item_height + spacing['spacing'])
                
                positioned_elements.append({
                    **elem,
                    'x': x_pos,
                    'y': y_pos,
                    'width': item_width,
                    'height': item_height
                })
        
        else:  # optimal_grid
            # Оптимальная сетка с минимизацией пустого места
            best_layout = self._calculate_optimal_grid_layout(elements, container_w, container_h)
            
            grid_start_x = container_x + (container_w - best_layout['total_width']) // 2
            grid_start_y = container_y + (container_h - best_layout['total_height']) // 2
            
            for i, elem in enumerate(elements):
                row = i // best_layout['cols']
                col = i % best_layout['cols']
                
                x_pos = grid_start_x + col * (best_layout['item_width'] + best_layout['spacing'])
                y_pos = grid_start_y + row * (best_layout['item_height'] + best_layout['spacing'])
                
                positioned_elements.append({
                    **elem,
                    'x': x_pos,
                    'y': y_pos,
                    'width': best_layout['item_width'],
                    'height': best_layout['item_height']
                })
        
        return positioned_elements
    
    def _calculate_optimal_grid_layout(self, elements: list, container_w: int, container_h: int) -> dict:
        """Вычисляет оптимальную компоновку сетки"""
        num_elements = len(elements)
        spacing = self.get_adaptive_spacing("menu")["spacing"]
        
        best_score = float('inf')
        best_layout = None
        
        # Проверяем все возможные компоновки
        for cols in range(1, min(num_elements + 1, 8)):
            rows = (num_elements + cols - 1) // cols
            
            # Вычисляем размеры элементов
            available_width = container_w - spacing * (cols - 1)
            available_height = container_h - spacing * (rows - 1)
            
            item_width = available_width // cols
            item_height = available_height // rows
            
            # Проверяем минимальные размеры
            if item_width >= 80 and item_height >= 30:
                # Оцениваем качество компоновки
                aspect_ratio = item_width / item_height
                ideal_ratio = 2.5  # Предпочитаемый коэффициент для кнопок
                ratio_penalty = abs(aspect_ratio - ideal_ratio)
                
                # Штраф за пустые ячейки
                empty_cells = cols * rows - num_elements
                empty_penalty = empty_cells * 1.5
                
                # Бонус за оптимальное количество колонок
                optimal_cols = 3 if self.aspect_type in ["4:3", "5:4"] else 4
                cols_penalty = abs(cols - optimal_cols) * 0.5
                
                total_score = ratio_penalty + empty_penalty + cols_penalty
                
                if total_score < best_score:
                    best_score = total_score
                    best_layout = {
                        'cols': cols,
                        'rows': rows,
                        'item_width': item_width,
                        'item_height': item_height,
                        'spacing': spacing,
                        'total_width': cols * item_width + spacing * (cols - 1),
                        'total_height': rows * item_height + spacing * (rows - 1)
                    }
        
        # Если не нашли оптимальную компоновку, используем простую
        if best_layout is None:
            cols = min(num_elements, 3)
            rows = (num_elements + cols - 1) // cols
            best_layout = {
                'cols': cols,
                'rows': rows,
                'item_width': container_w // cols,
                'item_height': container_h // rows,
                'spacing': spacing,
                'total_width': container_w,
                'total_height': container_h
            }
        
        return best_layout
    
    def get_smart_positioning(self, element_width: int, element_height: int, 
                            container_width: int, container_height: int, 
                            position_type: str = "center") -> tuple:
        """Возвращает умное позиционирование элемента в контейнере"""
        # Позиционирование с учетом безопасных зон
        safe_margin_x = self.get_margin(20)
        safe_margin_y = self.get_margin(15)
        
        if position_type == "center":
            x = (container_width - element_width) // 2
            y = (container_height - element_height) // 2
        elif position_type == "top_center":
            x = (container_width - element_width) // 2
            y = safe_margin_y
        elif position_type == "bottom_center":
            x = (container_width - element_width) // 2
            y = container_height - element_height - safe_margin_y
        elif position_type == "left_center":
            x = safe_margin_x
            y = (container_height - element_height) // 2
        elif position_type == "right_center":
            x = container_width - element_width - safe_margin_x
            y = (container_height - element_height) // 2
        elif position_type == "top_left":
            x = safe_margin_x
            y = safe_margin_y
        elif position_type == "top_right":
            x = container_width - element_width - safe_margin_x
            y = safe_margin_y
        elif position_type == "bottom_left":
            x = safe_margin_x
            y = container_height - element_height - safe_margin_y
        elif position_type == "bottom_right":
            x = container_width - element_width - safe_margin_x
            y = container_height - element_height - safe_margin_y
        else:
            # По умолчанию центрируем
            x = (container_width - element_width) // 2
            y = (container_height - element_height) // 2
        
        # Проверяем границы и корректируем при необходимости
        x = max(safe_margin_x, min(x, container_width - element_width - safe_margin_x))
        y = max(safe_margin_y, min(y, container_height - element_height - safe_margin_y))
        
        return x, y
    
    def optimize_layout_for_device(self, elements: list, container_width: int, container_height: int) -> dict:
        """Оптимизирует компоновку множества элементов для текущего устройства"""
        layout_info = {
            'device_class': self.device_class,
            'aspect_type': self.aspect_type,
            'recommended_columns': 1,
            'element_spacing': self.get_margin(10),
            'container_padding': self.get_margin(20)
        }
        
        # Рекомендации по количеству колонок на основе устройства
        if self.device_class == "ultra_high":
            if self.aspect_type in ["32:9", "21:9"]:
                layout_info['recommended_columns'] = min(4, len(elements))
            else:
                layout_info['recommended_columns'] = min(3, len(elements))
        elif self.device_class == "high":
            if self.aspect_type in ["32:9", "21:9"]:
                layout_info['recommended_columns'] = min(3, len(elements))
            else:
                layout_info['recommended_columns'] = min(2, len(elements))
        else:
            # medium и low
            if self.aspect_type in ["21:9", "32:9"]:
                layout_info['recommended_columns'] = min(2, len(elements))
            else:
                layout_info['recommended_columns'] = 1
        
        # Оптимальная сетка
        grid_config = self.get_responsive_grid(
            len(elements), container_width, container_height
        )
        
        layout_info.update(grid_config)
        
        return layout_info

# Кэширование для оптимизации производительности
_font_cache = {}
_surface_cache = {}
_adaptive_font_cache = {}

# Глобальная переменная для адаптивного дизайна
responsive = None

def get_cached_font(font_name: str, size: int, bold: bool = False) -> pygame.font.Font:
    """Получает шрифт из кэша с агрессивным масштабированием для лучшей читаемости"""
    global responsive
    
    # Применяем агрессивное масштабирование согласно memory
    if responsive:
        # Минимальный размер 18px
        min_size = 18
        
        # Масштабирование на основе разрешения
        total_pixels = responsive.screen_width * responsive.screen_height
        resolution_bonus = 1.0
        
        if total_pixels >= 8294400:  # 4K+
            resolution_bonus = 1.8
        elif total_pixels >= 2073600:  # 1920x1080+
            resolution_bonus = 1.6
        elif total_pixels >= 1440000:  # 1600x900+
            resolution_bonus = 1.4
        elif total_pixels >= 1049088:  # 1366x768+
            resolution_bonus = 1.3
        elif total_pixels >= 921600:   # 1280x720+
            resolution_bonus = 1.2
        
        # Начинаем с высокого базового размера (90% от оригинала)
        base_scaling = max(0.9, responsive.scale_factors['font']) if hasattr(responsive, 'scale_factors') else 1.0
        
        # Применяем бонусы и ограничения
        scaled_size = max(min_size, int(size * base_scaling * resolution_bonus))
        
        # Никогда не уменьшаем ниже 100% от базы
        scaled_size = max(size, scaled_size)
    else:
        scaled_size = max(18, size)
    
    cache_key = f"{font_name}_{scaled_size}_{bold}"
    
    if cache_key not in _font_cache:
        try:
            # Приоритетные шрифты с хорошей поддержкой кириллицы
            cyrillic_fonts = 'arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace'
            _font_cache[cache_key] = pygame.font.SysFont(cyrillic_fonts, scaled_size, bold=bold)
        except Exception:
            try:
                # Проверяем наличие системных шрифтов с поддержкой кириллицы
                _font_cache[cache_key] = pygame.font.SysFont(font_name, scaled_size, bold=bold)
            except Exception:
                # Фолбэк на стандартный шрифт
                _font_cache[cache_key] = pygame.font.Font(None, scaled_size)
        
        # Ограничиваем размер кэша
        if len(_font_cache) > 50:
            # Удаляем старые шрифты
            oldest_keys = list(_font_cache.keys())[:10]
            for old_key in oldest_keys:
                del _font_cache[old_key]
    
    return _font_cache[cache_key]

def get_cached_text_surface(text: str, font: pygame.font.Font, color: tuple) -> pygame.Surface:
    """Получает отрисованный текст из кэша"""
    cache_key = f"{text}_{font.get_height()}_{color[0]}_{color[1]}_{color[2]}"
    if cache_key not in _surface_cache:
        _surface_cache[cache_key] = font.render(text, True, color)
        
        # Ограничиваем размер кэша
        if len(_surface_cache) > 100:
            oldest_keys = list(_surface_cache.keys())[:20]
            for old_key in oldest_keys:
                del _surface_cache[old_key]
    
    return _surface_cache[cache_key]

def clear_performance_caches():
    """Очищает кэши для освобождения памяти"""
    global _font_cache, _surface_cache, _adaptive_font_cache
    _font_cache.clear()
    _surface_cache.clear()
    _adaptive_font_cache.clear()

WIDTH, HEIGHT = 1200, 800 # Увеличиваем размер экрана для лучшего размещения
PLAY_COLS, PLAY_ROWS = 10, 20 
BLOCK = 30 # Немного уменьшаем размер блока для лучшей компоновки
PLAY_W, PLAY_H = PLAY_COLS * BLOCK, PLAY_ROWS * BLOCK
MARGIN = 25 # Увеличиваем отступы
PANEL_W = WIDTH - PLAY_W - MARGIN * 3
FPS = 60

# Origin of playfield (centered vertically)
ORIGIN_X = MARGIN
ORIGIN_Y = max(MARGIN, MARGIN + (HEIGHT - 2*MARGIN - PLAY_H) // 2)

# Music directory scanning
MUSIC_DIR = "music"
MUSIC_FILES = []

def scan_music_files(directory):
    """Рекурсивно сканирует директорию в поисках музыкальных файлов и разделяет их на категории."""
    menu_music = []
    pause_music = []
    game_music = []
    
    if os.path.isdir(directory):
        for root, dirs, files in os.walk(directory):
            for fname in sorted(files):
                if fname.lower().endswith(('.mp3', '.ogg', '.wav')):
                    full_path = os.path.join(root, fname)
                    # Определяем категорию музыки по пути или имени файла
                    if (
                        'pause' in root.lower() or 
                        'pause' in fname.lower()
                    ):
                        pause_music.append(full_path)
                    elif (
                        'menu' in root.lower() or 
                        'menu' in fname.lower() or 
                        '18-competition-menu' in fname.lower()
                    ):
                        menu_music.append(full_path)
                    else:
                        game_music.append(full_path)
    
    return menu_music, pause_music, game_music

MENU_MUSIC_FILES, PAUSE_MUSIC_FILES, GAME_MUSIC_FILES = scan_music_files(MUSIC_DIR)
# Для обратной совместимости - объединённый список
MUSIC_FILES = MENU_MUSIC_FILES + PAUSE_MUSIC_FILES + GAME_MUSIC_FILES
if not MUSIC_FILES:
    # fallback to explicit list (kept for compatibility)
    MUSIC_FILES = [
        "Tetris - Коробейники(FamilyJules7X).mp3",
        "Маридат47 - Музыка из тетриса (коробейники).mp3",
        "Коробейники - Тетрис Техно Ремикс.mp3",
        "Тетрис - Коробейники.mp3",
        "Владимир Зеленцов - Коробейники (Tetris Theme).mp3",
        "chocolate-chip-by-uncle-morris.mp3",
        "kevin-macleod-pixelland.mp3",
        "kubbi-digestive-biscuit.mp3",
        "laxity-crosswords-by-seraphic-music.mp3"
    ]

# Sound effects (optional). Put wav files into ./sounds/ named: rotate.wav, drop.wav, line.wav
SOUNDS_DIR = "sounds"

# Colors - Современная улучшенная цветовая схема
BLACK = (12, 12, 15)
BG = (18, 18, 22)  # Более глубокий темный фон
BG_GRADIENT_TOP = (22, 25, 30)
BG_GRADIENT_BOTTOM = (12, 15, 18)
GRID = (40, 45, 55)
WHITE = (248, 250, 252)
DIM = (165, 175, 185)
GHOST = (95, 105, 115)

# UI Элементы - Обновленная палитра
BUTTON_BG = (32, 37, 45)
BUTTON_BG_HOVER = (42, 50, 65)
BUTTON_BG_ACTIVE = (52, 65, 85)
BUTTON_BORDER = (75, 85, 105)
BUTTON_BORDER_HOVER = (115, 135, 165)
BUTTON_TEXT = (220, 230, 240)
BUTTON_TEXT_HOVER = (255, 255, 255)

# Современные акцентные цвета
ACCENT_PRIMARY = (58, 150, 255)    # Яркий синий
ACCENT_SECONDARY = (128, 90, 213)  # Элегантный фиолетовый
ACCENT_SUCCESS = (52, 211, 153)    # Свежий зеленый
ACCENT_WARNING = (251, 191, 36)    # Теплый желтый
ACCENT_DANGER = (239, 68, 68)      # Современный красный
ACCENT_INFO = (59, 130, 246)       # Информационный синий

# Панели и контейнеры - Улучшенные градиенты
PANEL_BG = (25, 30, 38)
PANEL_BORDER = (55, 65, 78)
PANEL_SHADOW = (5, 8, 10)

# Игровое поле - Более контрастные цвета
PLAYFIELD_BG = (20, 24, 32)
PLAYFIELD_BORDER = (50, 60, 75)
PLAYFIELD_GRID = (30, 37, 47)

# Tetromino colors - Улучшенные яркие цвета с лучшим контрастом (I, O, T, S, Z, J, L)
COLORS = {
    'I': (0, 184, 255),      # Яркий голубой - классика Tetris
    'O': (255, 215, 0),      # Золотой желтый
    'T': (160, 32, 240),     # Яркий фиолетовый
    'S': (0, 230, 64),       # Насыщенный зеленый
    'Z': (255, 48, 48),      # Яркий красный
    'J': (0, 121, 255),      # Глубокий синий
    'L': (255, 163, 0),      # Яркий оранжевый
}

# Тёмные варианты для теней и границ - более контрастные
COLORS_DARK = {
    'I': (0, 130, 180),      # Глубокий голубой
    'O': (200, 150, 0),      # Темно-золотой
    'T': (100, 15, 150),     # Темно-фиолетовый
    'S': (0, 160, 45),       # Темно-зеленый
    'Z': (180, 25, 25),      # Темно-красный
    'J': (0, 85, 180),       # Темно-синий
    'L': (180, 115, 0),      # Темно-оранжевый
}

# Светлые варианты для бликов - ярче и насыщеннее
COLORS_LIGHT = {
    'I': (100, 220, 255),    # Светло-голубой
    'O': (255, 245, 120),    # Светло-желтый
    'T': (200, 120, 255),    # Светло-фиолетовый
    'S': (120, 255, 160),    # Светло-зеленый
    'Z': (255, 120, 120),    # Светло-красный
    'J': (120, 180, 255),    # Светло-синий
    'L': (255, 200, 120),    # Светло-оранжевый
}

# Дополнительные цвета для создания красивых градиентов
COLORS_GRADIENT_TOP = {
    'I': (80, 245, 255),     # Светло-голубой верх
    'O': (255, 240, 80),     # Светло-золотой верх
    'T': (190, 130, 220),    # Светло-фиолетовый верх
    'S': (80, 230, 140),     # Светло-зеленый верх
    'Z': (255, 120, 100),    # Светло-красный верх
    'J': (90, 180, 245),     # Светло-синий верх
    'L': (255, 170, 80),     # Светло-оранжевый верх
}

COLORS_GRADIENT_BOTTOM = {
    'I': (0, 180, 220),      # Темно-голубой низ
    'O': (220, 180, 0),      # Темно-золотой низ
    'T': (120, 60, 150),     # Темно-фиолетовый низ
    'S': (30, 160, 90),      # Темно-зеленый низ
    'Z': (190, 40, 30),      # Темно-красный низ
    'J': (30, 120, 180),     # Темно-синий низ
    'L': (210, 100, 20),     # Темно-оранжевый низ
}

# Shapes are 4x4 matrices
SHAPES = {
    'I': [
        ["....",
         "IIII",
         "....",
         "...."],
    ],
    'O': [
        ["....",
         ".OO.",
         ".OO.",
         "...."],
    ],
    'T': [
        ["....",
         ".TTT",
         "..T.",
         "...."],
    ],
    'S': [
        ["....",
         "..SS",
         ".SS.",
         "...."],
    ],
    'Z': [
        ["....",
         ".ZZ.",
         "..ZZ",
         "...."],
    ],
    'J': [
        ["....",
         ".JJJ",
         ".J..",
         "...."],
    ],
    'L': [
        ["....",
         ".LLL",
         ".L..",
         "...."],
    ],
}

ROTATIONS = {'I': 2, 'O': 1, 'T': 4, 'S': 2, 'Z': 2, 'J': 4, 'L': 4}

# Kicks (simplified SRS-ish)
KICKS = {
    'JLTSZ': {
        (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, +2), (-1, +2)],
        (1, 0): [(0, 0), (+1, 0), (+1, +1), (0, -2), (+1, -2)],
        (1, 2): [(0, 0), (+1, 0), (+1, -1), (0, +2), (+1, +2)],
        (2, 1): [(0, 0), (-1, 0), (-1, +1), (0, -2), (-1, -2)],
        (2, 3): [(0, 0), (+1, 0), (+1, +1), (0, -2), (+1, -2)],
        (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, +2), (-1, +2)],
        (3, 0): [(0, 0), (-1, 0), (-1, +1), (0, -2), (-1, -2)],
        (0, 3): [(0, 0), (+1, 0), (+1, -1), (0, +2), (+1, +2)],
    },
    'I': {
        (0, 1): [(0, 0), (-2, 0), (+1, 0), (-2, -1), (+1, +2)],
        (1, 0): [(0, 0), (+2, 0), (-1, 0), (+2, +1), (-1, -2)],
        (1, 2): [(0, 0), (-1, 0), (+2, 0), (-1, +2), (+2, -1)],
        (2, 1): [(0, 0), (+1, 0), (-2, 0), (+1, -2), (-2, +1)],
        (2, 3): [(0, 0), (+2, 0), (-1, 0), (+2, +1), (-1, -2)],
        (3, 2): [(0, 0), (-2, 0), (+1, 0), (-2, -1), (+1, +2)],
        (3, 0): [(0, 0), (+1, 0), (-2, 0), (+1, -2), (-2, +1)],
        (0, 3): [(0, 0), (-1, 0), (+2, 0), (-1, +2), (+2, -1)],
    }
}

# -------------------- Utility --------------------
def rotate_shape(grid: List[str]) -> List[str]:
    """
    Поворачивает матрицу 4x4 на 90 градусов по часовой стрелке.
    
    Args:
        grid: Список строк, представляющий матрицу 4x4
        
    Returns:
        Повернутая матрица 4x4 как список строк
    """
    return [''.join([grid[3 - c][r] for c in range(4)]) for r in range(4)]

def build_rotations(kind: str) -> List[List[str]]:
    """
    Создает все уникальные состояния поворота для указанного типа тетромино.
    
    Args:
        kind: Тип тетромино ('I', 'O', 'T', 'S', 'Z', 'J', 'L')
        
    Returns:
        Список всех уникальных состояний поворота для данного типа
    """
    base = SHAPES[kind][0]
    rots = [base]
    for _ in range(3):
        rots.append(rotate_shape(rots[-1]))
    unique = []
    seen = set()
    for r in rots:
        key = tuple(r)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    count = ROTATIONS[kind]
    return unique[:count]

ROTATED = {k: build_rotations(k) for k in SHAPES.keys()}

@dataclass
class InputState:
    """
    Класс для управления состояниями ввода и анимации.
    Централизует все временные состояния, связанные с пользовательским вводом.
    """
    # Состояния клавиш
    left: bool = False
    right: bool = False
    down: bool = False
    down_activated_for_current_piece: bool = False  # Активирована ли кнопка вниз для текущей фигуры
    
    # Таймеры автоповтора
    das_timer: float = 0.0  # Delay Auto Shift
    arr_timer: float = 0.0  # Auto Repeat Rate
    last_direction: Optional[str] = None  # 'L' или 'R'
    
    # Состояния анимации падения
    smooth_fall_active: bool = False
    smooth_fall_speed: float = 1.0
    smooth_fall_timer: float = 0.0
    smooth_fall_double_press: bool = False
    smooth_fall_start_time: float = 0.0
    
    # Обнаружение двойных нажатий
    last_down_press: float = 0.0
    last_space_press: float = 0.0
    double_press_window: float = 0.18  # 180мс окно для двойного нажатия (более отзывчиво)
    
    # Отслеживание длительности нажатий для предотвращения случайных нажатий
    key_press_start_times: dict = field(default_factory=dict)
    short_press_threshold: float = 0.06  # 60мс для короткого нажатия (ещё быстрее)
    long_press_threshold: float = 0.15   # 150мс для долгого нажатия (быстрее активация)
    
    # Улучшенная система контроля нажатий
    key_hold_states: dict = field(default_factory=dict)  # Состояния удержания клавиш
    last_action_time: dict = field(default_factory=dict)  # Время последнего действия для каждой клавиши
    action_cooldown: float = 0.05  # 50мс кулдаун между действиями для предотвращения спама
    
    # Состояние обычной гравитации
    gravity_timer: float = 0.0
    
    def reset_all(self):
        """Полный сброс всех состояний."""
        self.left = False
        self.right = False
        self.down = False
        self.down_activated_for_current_piece = False
        self.das_timer = 0.0
        self.arr_timer = 0.0
        self.last_direction = None
        self.reset_falling_animation()
        self.gravity_timer = 0.0
        # Очищаем информацию о длительности нажатий
        self.key_press_start_times.clear()
        self.key_hold_states.clear()
        self.last_action_time.clear()
    
    def reset_falling_animation(self):
        """Сброс только состояний анимации падения."""
        self.smooth_fall_active = False
        self.smooth_fall_speed = 1.0
        self.smooth_fall_timer = 0.0
        self.smooth_fall_double_press = False
        self.smooth_fall_start_time = 0.0
    
    def reset_movement_keys(self):
        """Сброс только клавиш движения."""
        self.left = False
        self.right = False
        self.down = False
        self.down_activated_for_current_piece = False
        self.das_timer = 0.0
        self.arr_timer = 0.0
        self.last_direction = None
    
    def start_smooth_fall(self, speed: float, is_double_press: bool = False):
        """Запуск плавного падения с указанными параметрами."""
        current_time = pygame.time.get_ticks() / 1000.0
        self.smooth_fall_active = True
        self.smooth_fall_speed = speed
        self.smooth_fall_timer = 0.0
        self.smooth_fall_double_press = is_double_press
        self.smooth_fall_start_time = current_time
    
    def is_double_press(self, key_type: str) -> bool:
        """Проверка на двойное нажатие для указанного типа клавиши."""
        current_time = pygame.time.get_ticks() / 1000.0
        if key_type == 'down':
            if current_time - self.last_down_press < self.double_press_window:
                self.last_down_press = current_time
                return True
            self.last_down_press = current_time
            return False
        elif key_type == 'space':
            if current_time - self.last_space_press < self.double_press_window:
                self.last_space_press = current_time
                return True
            self.last_space_press = current_time
            return False
        return False
    
    def start_key_press(self, key_name: str):
        """Запуск отслеживания длительности нажатия клавиши."""
        current_time = pygame.time.get_ticks() / 1000.0
        self.key_press_start_times[key_name] = current_time
    
    def end_key_press(self, key_name: str) -> str:
        """
        Окончание нажатия клавиши и определение типа нажатия.
        
        Returns:
            'short' для короткого нажатия, 'long' для долгого, 'medium' для среднего
        """
        current_time = pygame.time.get_ticks() / 1000.0
        start_time = self.key_press_start_times.get(key_name, current_time)
        duration = current_time - start_time
        
        # Удаляем запись о начале нажатия
        if key_name in self.key_press_start_times:
            del self.key_press_start_times[key_name]
        
        if duration < self.short_press_threshold:
            return 'short'
        elif duration > self.long_press_threshold:
            return 'long'
        else:
            return 'medium'
    
    def get_key_press_duration(self, key_name: str) -> float:
        """Получает текущую длительность нажатия клавиши."""
        current_time = pygame.time.get_ticks() / 1000.0
        start_time = self.key_press_start_times.get(key_name, current_time)
        return current_time - start_time
    
    def is_long_press_active(self, key_name: str) -> bool:
        """Проверяет, является ли текущее нажатие долгим."""
        return self.get_key_press_duration(key_name) > self.long_press_threshold
    
    def can_perform_action(self, key_name: str) -> bool:
        """Проверяет, можно ли выполнить действие для данной клавиши."""
        current_time = pygame.time.get_ticks() / 1000.0
        last_action = self.last_action_time.get(key_name, 0.0)
        return current_time - last_action >= self.action_cooldown
    
    def mark_action_performed(self, key_name: str):
        """Отмечает, что действие для клавиши было выполнено."""
        current_time = pygame.time.get_ticks() / 1000.0
        self.last_action_time[key_name] = current_time
    
    def get_press_intent(self, key_name: str) -> str:
        """
        Определяет намерение нажатия клавиши на основе длительности.
        
        Returns:
            'tap' - короткое нажатие (лёгкое касание)
            'press' - среднее нажатие (осознанное действие)
            'hold' - долгое нажатие (удержание)
        """
        duration = self.get_key_press_duration(key_name)
        if duration < self.short_press_threshold:
            return 'tap'
        elif duration < self.long_press_threshold:
            return 'press' 
        else:
            return 'hold'
    
    def start_enhanced_smooth_fall(self, base_speed: float, intent: str, is_double: bool = False):
        """
        Запускает улучшенное плавное падение с адаптивной скоростью.
        
        Args:
            base_speed: Базовая скорость
            intent: Намерение нажатия ('tap', 'press', 'hold')
            is_double: Является ли двойным нажатием
        """
        # Модификаторы скорости на основе намерения
        intent_multipliers = {
            'tap': 1.0,     # Минимальная скорость для лёгкого касания
            'press': 1.5,   # Средняя скорость для осознанного нажатия
            'hold': 2.0     # Максимальная скорость для удержания
        }
        
        final_speed = base_speed * intent_multipliers.get(intent, 1.0)
        if is_double:
            final_speed *= 1.8  # Дополнительный буст для двойного нажатия
        
        current_time = pygame.time.get_ticks() / 1000.0
        self.smooth_fall_active = True
        self.smooth_fall_speed = final_speed
        self.smooth_fall_timer = 0.0
        self.smooth_fall_double_press = is_double
        self.smooth_fall_start_time = current_time

@dataclass
class Piece:
    """
    Класс, представляющий тетромино (фигуру) на игровом поле.
    
    Attributes:
        kind: Тип тетромино ('I', 'O', 'T', 'S', 'Z', 'J', 'L')
        x: Позиция по оси X (столбец)
        y: Позиция по оси Y (строка)
        r: Состояние поворота (0-3)
    """
    kind: str
    x: int
    y: int
    r: int = 0

    @property
    def grid(self) -> List[str]:
        """
        Возвращает матрицу 4x4 для текущего состояния поворота.
        
        Returns:
            Матрица 4x4 как список строк
        """
        return ROTATED[self.kind][self.r % len(ROTATED[self.kind])]

    def cells(self) -> List[Tuple[int, int]]:
        """
        Возвращает список координат всех занятых клеток тетромино.
        
        Returns:
            Список кортежей (x, y) для каждой занятой клетки
        """
        cells = []
        g = self.grid
        for j in range(4):
            for i in range(4):
                if g[j][i] != '.':
                    cells.append((self.x + i, self.y + j))
        return cells

@dataclass
class GameState:
    """
    Класс, представляющий полное состояние игры Тетрис.
    
    Содержит всю информацию о текущем состоянии игры:
    стакан с заполненными клетками, текущую фигуру, очки, уровень, статистику и т.д.
    
    Attributes:
        grid: Игровой стакан 20x10 клеток
        bag: Мешок с типами тетромино для генерации
        next_queue: Очередь следующих фигур
        hold: Тип зафиксированной фигуры (Hold)
        can_hold: Можно ли использовать Hold
        current: Текущая падающая фигура
        score: Очки игрока
        lines: Количество убранных линий
        level: Текущий уровень
        combo: Количество последовательных очисток линий
        back_to_back: Флаг Back-to-Back бонуса
        game_over: Закончена ли игра
        paused: Поставлена ли игра на паузу
        fall_interval: Интервал между падениями фигур (гравитация)
        hard_drop_anim: Флаг анимации быстрого падения
        hard_drop_start_y: Начальная Y-позиция для анимации быстрого падения
        hard_drop_target_y: Конечная Y-позиция для анимации быстрого падения
        hard_drop_duration: Продолжительность анимации быстрого падения
        hard_drop_start_time: Время начала анимации быстрого падения
    """
    grid: List[List[Optional[str]]] = field(default_factory=lambda: [[None for _ in range(PLAY_COLS)] for _ in range(PLAY_ROWS)])
    bag: List[str] = field(default_factory=list)
    next_queue: List[str] = field(default_factory=list)
    hold: Optional[str] = None
    can_hold: bool = True
    current: Optional[Piece] = None
    score: int = 0
    lines: int = 0
    level: int = 1
    combo: int = -1
    back_to_back: bool = False
    game_over: bool = False
    paused: bool = False
    fall_interval: float = 1.0
    # hard-drop animation state
    hard_drop_anim: bool = False
    hard_drop_start_y: int = 0
    hard_drop_target_y: int = 0
    hard_drop_duration: float = 0.0
    hard_drop_start_time: float = 0.0
    # smooth falling animation state
    smooth_fall_anim: bool = False
    smooth_fall_speed: float = 1.0
    smooth_fall_start_time: float = 0.0
    smooth_fall_last_press: float = 0.0
    smooth_fall_double_press: bool = False
    
    # Animation drawing position
    _anim_draw_y: int = 0
    
    # Игровой режим и прогресс
    game_mode: GameMode = GameMode.ENDLESS_IMMERSIVE
    current_campaign_level: int = 1
    campaign_objectives_progress: dict = field(default_factory=dict)
    session_start_time: float = 0.0
    mode_config: Optional[GameModeConfig] = None

    def to_dict(self):
        """
        Преобразует состояние игры в словарь для сохранения в JSON.
        
        Returns:
            Словарь с всеми полями состояния игры
        """
        return {
            'grid': [[cell if cell is not None else None for cell in row] for row in self.grid],
            'bag': list(self.bag),
            'next_queue': list(self.next_queue),
            'hold': self.hold,
            'can_hold': self.can_hold,
            'current': None if self.current is None else {'kind': self.current.kind, 'x': self.current.x, 'y': self.current.y, 'r': self.current.r},
            'score': self.score,
            'lines': self.lines,
            'level': self.level,
            'combo': self.combo,
            'back_to_back': self.back_to_back,
            'game_over': self.game_over,
            # Новые поля для игровых режимов
            'game_mode': self.game_mode.value,
            'current_campaign_level': self.current_campaign_level,
            'campaign_objectives_progress': self.campaign_objectives_progress,
            'session_start_time': self.session_start_time
        }

    @staticmethod
    def from_dict(d):
        """
        Создает объект GameState из словаря (загрузка из JSON).
        
        Args:
            d: Словарь с данными состояния игры
            
        Returns:
            Новый объект GameState с загруженными данными
        """
        s = GameState()
        s.grid = [[cell if cell is not None else None for cell in row] for row in d.get('grid', s.grid)]
        s.bag = d.get('bag', [])
        s.next_queue = d.get('next_queue', [])
        s.hold = d.get('hold', None)
        s.can_hold = d.get('can_hold', True)
        cur = d.get('current', None)
        if cur:
            s.current = Piece(cur['kind'], cur['x'], cur['y'], cur['r'])
        s.score = d.get('score', 0)
        s.lines = d.get('lines', 0)
        s.level = d.get('level', 1)
        s.combo = d.get('combo', -1)
        s.back_to_back = d.get('back_to_back', False)
        s.game_over = d.get('game_over', False)
        
        # Загрузка новых полей для игровых режимов
        mode_str = d.get('game_mode', 'endless_immersive')
        try:
            s.game_mode = GameMode(mode_str)
        except ValueError:
            s.game_mode = GameMode.ENDLESS_IMMERSIVE
        
        s.current_campaign_level = d.get('current_campaign_level', 1)
        s.campaign_objectives_progress = d.get('campaign_objectives_progress', {})
        s.session_start_time = d.get('session_start_time', 0.0)
        s.mode_config = GAME_MODE_CONFIGS.get(s.game_mode)
        
        s.fall_interval = gravity_for_level(s.level)
        return s

# -------------------- Core game logic --------------------
def reset_animation_state(state: GameState):
    """
    Полностью сбрасывает все состояния анимации падения.
    
    Args:
        state: Текущее состояние игры
    """
    state.smooth_fall_anim = False
    state.smooth_fall_speed = 1.0
    state.smooth_fall_double_press = False
    state.hard_drop_anim = False

def gravity_for_level(level: int) -> float:
    """
    Вычисляет скорость падения фигур для указанного уровня.
    
    Args:
        level: Уровень сложности (1 и выше)
        
    Returns:
        Интервал в секундах между падениями фигур
    """
    return max(0.05, 0.8 * (0.9 ** (level - 1)))

def spawn_x(kind: str) -> int:
    """
    Определяет начальную X-позицию для новой фигуры.
    
    Args:
        kind: Тип тетромино
        
    Returns:
        X-координата для спауна фигуры
    """
    return 3 if kind != 'I' else 3

def collides(state: GameState, piece: Piece) -> bool:
    """
    Проверяет, сталкивается ли фигура с границами стакана или другими фигурами.
    
    Args:
        state: Текущее состояние игры
        piece: Фигура для проверки
        
    Returns:
        True, если есть столкновение, иначе False
    """
    for x, y in piece.cells():
        if x < 0 or x >= PLAY_COLS or y >= PLAY_ROWS:
            return True
        if y >= 0 and state.grid[y][x] is not None:
            return True
    return False

def lock_piece(state: GameState):
    """
    Фиксирует текущую фигуру на стакане и очищает заполненные линии.
    
    Args:
        state: Текущее состояние игры
        
    Returns:
        Количество очищенных линий
    """
    if state.current is None:
        return 0
    for x, y in state.current.cells():
        if y < 0:
            state.game_over = True
            return 0
        state.grid[y][x] = state.current.kind
    cleared = clear_lines(state)
    state.can_hold = True
    state.current = None
    # Полный сброс состояния анимации при блокировке
    reset_animation_state(state)
    spawn_next(state)
    return cleared

def is_t_spin(state: GameState, piece: Piece, kicked: bool) -> str:
    """
    Определяет, является ли последний поворот T-спином.
    
    T-спин - это особый тип поворота T-тетромино, когда он зажат с трех сторон и дает дополнительные очки.
    
    Args:
        state: Текущее состояние игры
        piece: T-тетромино для проверки
        kicked: Был ли поворот выполнен с киком (wall kick)
        
    Returns:
        'tspin' если это T-спин, 'none' в противном случае
    """
    if piece.kind != 'T':
        return 'none'
    corners = [(piece.x, piece.y), (piece.x+2, piece.y), (piece.x, piece.y+2), (piece.x+2, piece.y+2)]
    occupied = 0
    for cx, cy in corners:
        if cy < 0 or cx < 0 or cx >= PLAY_COLS or cy >= PLAY_ROWS:
            occupied += 1
        elif state.grid[cy][cx] is not None:
            occupied += 1
    if occupied >= 3:
        return 'tspin'
    return 'none'

def score_lines(state: GameState, lines: int, tspin: str):
    """
    Начисляет очки за очищенные линии и обновляет статистику игры.
    
    Очки зависят от:
    - Количества очищенных линий
    - Наличия T-спина
    - Комбо (последовательные очистки)
    - Back-to-Back бонуса (за тетрисы и T-спины подряд)
    
    Args:
        state: Текущее состояние игры
        lines: Количество очищенных линий
        tspin: Тип T-спина ('tspin' или 'none')
    """
    pts = 0
    if tspin != 'none':
        if lines == 1:
            pts = 400
        elif lines == 2:
            pts = 700
        else:
            pts = 100
        b2b_candidate = True
    else:
        if lines == 1:
            pts = 100
        elif lines == 2:
            pts = 300
        elif lines == 3:
            pts = 500
        elif lines >= 4:
            pts = 800
        b2b_candidate = (lines >= 4)

    if lines > 0:
        state.combo += 1
        if state.combo > 0:
            pts += 50 * state.combo
        if b2b_candidate:
            if state.back_to_back:
                pts = int(pts * 1.5)
            state.back_to_back = True
        else:
            state.back_to_back = False
        state.lines += lines
        if state.lines // 10 + 1 > state.level:
            state.level = state.lines // 10 + 1
            state.fall_interval = gravity_for_level(state.level)
    else:
        state.combo = -1
        state.back_to_back = False

    state.score += pts

def clear_lines(state: GameState) -> int:
    """
    Очищает все заполненные линии с игрового поля.
    
    Удаляет все строки, где все клетки заняты, а сверху добавляет пустые строки.
    
    Args:
        state: Текущее состояние игры
        
    Returns:
        Количество очищенных линий
    """
    new_grid = [row for row in state.grid if any(cell is None for cell in row)]
    cleared = PLAY_ROWS - len(new_grid)
    while len(new_grid) < PLAY_ROWS:
        new_grid.insert(0, [None for _ in range(PLAY_COLS)])
    state.grid = new_grid
    return cleared

def refill_bag(state: GameState):
    """
    Пополняет мешок с типами тетромино.
    
    Использует систему "7-bag" - в каждом мешке есть ровно одна фигура каждого типа, перемешанные случайно.
    
    Args:
        state: Текущее состояние игры
    """
    bag = list(SHAPES.keys())
    random.shuffle(bag)
    state.bag.extend(bag)

def spawn_next(state: GameState):
    """
    Создает новую падающую фигуру из очереди.
    
    Заполняет очередь следующих фигур до 5 элементов и берёт первую для создания текущей фигуры.
    
    Args:
        state: Текущее состояние игры
    """
    while len(state.next_queue) < 5:
        if not state.bag:
            refill_bag(state)
        state.next_queue.append(state.bag.pop(0))
    kind = state.next_queue.pop(0)
    piece = Piece(kind, spawn_x(kind), -2, 0)
    if collides(state, piece):
        state.game_over = True
    state.current = piece
    # Полный сброс состояния анимации для новой фигуры
    reset_animation_state(state)

def try_move(state: GameState, dx: int, dy: int) -> bool:
    """
    Пытается сдвинуть текущую фигуру на указанное расстояние.
    
    Args:
        state: Текущее состояние игры
        dx: Сдвиг по оси X (столбцам)
        dy: Сдвиг по оси Y (строкам)
        
    Returns:
        True, если движение возможно, иначе False
    """
    if state.current is None:
        return False
    p = Piece(state.current.kind, state.current.x + dx, state.current.y + dy, state.current.r)
    if not collides(state, p):
        state.current = p
        return True
    return False

def try_rotate(state: GameState, dr: int) -> Tuple[bool, str]:
    """
    Пытается повернуть текущую фигуру с проверкой wall kick'ов.
    
    Использует систему SRS (Super Rotation System) для попыток поворота в нескольких позициях.
    
    Args:
        state: Текущее состояние игры
        dr: Направление поворота (+1 по часовой, -1 против)
        
    Returns:
        Кортеж (удалось ли повернуть, тип T-спина)
    """
    cur = state.current
    if cur is None:
        return False, 'none'
    from_r = cur.r % len(ROTATED[cur.kind])
    to_r = (cur.r + dr) % len(ROTATED[cur.kind])
    which = 'I' if cur.kind == 'I' else 'JLTSZ'
    kicks = KICKS.get(which, {}).get((from_r, to_r), [(0, 0)])
    for (dx, dy) in kicks:
        cand = Piece(cur.kind, cur.x + dx, cur.y + dy, to_r)
        if not collides(state, cand):
            state.current = cand
            return True, is_t_spin(state, cand, kicked=(dx != 0 or dy != 0))
    return False, 'none'

def hard_drop_distance(state: GameState) -> int:
    """
    Вычисляет расстояние для быстрого падения текущей фигуры.
    
    Определяет, на сколько клеток вниз можно опустить фигуру до столкновения.
    
    Args:
        state: Текущее состояние игры
        
    Returns:
        Количество клеток до приземления
    """
    if state.current is None:
        return 0
    dist = 0
    p = state.current
    while True:
        q = Piece(p.kind, p.x, p.y + dist + 1, p.r)
        if collides(state, q):
            break
        dist += 1
    return dist

def ghost_position(state: GameState) -> Optional[Piece]:
    """
    Создает "призрачную" копию текущей фигуры в позиции приземления.
    
    Показывает игроку, где приземлится фигура при быстром падении.
    
    Args:
        state: Текущее состояние игры
        
    Returns:
        Копия текущей фигуры в позиции приземления или None, если нет текущей фигуры
    """
    if state.current is None:
        return None
    d = hard_drop_distance(state)
    p = state.current
    return Piece(p.kind, p.x, p.y + d, p.r)

def hold_swap(state: GameState):
    """
    Выполняет обмен текущей фигуры с зафиксированной (Hold).
    
    Механика Hold позволяет сохранить текущую фигуру на потом и использовать её позже.
    Можно использовать только один раз на каждую фигуру.
    
    Args:
        state: Текущее состояние игры
    """
    if state.current is None or not state.can_hold:
        return
    cur_kind = state.current.kind
    if state.hold is None:
        state.hold = cur_kind
        spawn_next(state)
    else:
        state.current = Piece(state.hold, spawn_x(state.hold), -2, 0)
        state.hold = cur_kind
        if collides(state, state.current):
            state.game_over = True
        # Полный сброс состояния анимации при смене фигуры
        reset_animation_state(state)
    state.can_hold = False

# -------------------- Audio --------------------

MUSIC_END_EVENT = pygame.USEREVENT + 1

class AudioManager:
    """
    Менеджер аудиосистемы для воспроизведения музыки и звуковых эффектов.
    
    Обрабатывает:
    - Фоновую музыку с раздельными плейлистами для меню, паузы и игры
    - Звуковые эффекты (поворот, падение, очистка линий)
    - Переключение между треками
    - Автоматическое переключение контекста музыки
    
    Attributes:
        menu_playlist: Список путей к музыкальным файлам для меню
        pause_playlist: Список путей к музыкальным файлам для меню паузы
        game_playlist: Список путей к музыкальным файлам для игры
        current_context: Текущий контекст ('menu', 'pause' или 'game')
        menu_index: Индекс текущего трека в меню
        pause_index: Индекс текущего трека в меню паузы
        game_index: Индекс текущего трека в игре
        enabled: Включена ли аудиосистема
        sounds: Словарь загруженных звуковых эффектов
    """
    def __init__(self):
        # initialize mixer safely
        try:
            pygame.mixer.init()
        except Exception:
            pass
        
        # Создаём раздельные плейлисты для меню, паузы и игры
        self.menu_playlist = [f for f in MENU_MUSIC_FILES if os.path.isfile(f)]
        self.pause_playlist = [f for f in PAUSE_MUSIC_FILES if os.path.isfile(f)]
        self.game_playlist = [f for f in GAME_MUSIC_FILES if os.path.isfile(f)]
        
        # Фолбэк логика для пустых плейлистов
        if not self.pause_playlist:
            # Если нет специальной музыки для паузы, используем меню
            self.pause_playlist = self.menu_playlist.copy() if self.menu_playlist else self.game_playlist.copy()
        if not self.menu_playlist and self.game_playlist:
            self.menu_playlist = self.game_playlist.copy()
        elif not self.game_playlist and self.menu_playlist:
            self.game_playlist = self.menu_playlist.copy()
            
        self.menu_index = 0
        self.pause_index = 0
        self.game_index = 0
        self.current_context = 'menu'  # Начинаем с меню
        
        # Для обратной совместимости
        self.playlist = self.menu_playlist if self.menu_playlist else self.game_playlist
        self.index = 0
        
        self.enabled = len(self.menu_playlist) > 0 or len(self.game_playlist) > 0
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        self.sounds = {}
        
        # load sfx if available
        if os.path.isdir(SOUNDS_DIR):
            for name in ['rotate', 'drop', 'line']:
                path = os.path.join(SOUNDS_DIR, f"{name}.wav")
                if os.path.isfile(path):
                    try:
                        self.sounds[name] = pygame.mixer.Sound(path)
                    except Exception:
                        self.sounds[name] = None
        # default volume
        try:
            pygame.mixer.music.set_volume(0.5)
        except Exception:
            pass
    
    def set_context(self, context: str):
        """Переключает контекст музыки между 'menu', 'pause' и 'game'."""
        if context not in ['menu', 'pause', 'game']:
            return
            
        old_context = self.current_context
        self.current_context = context
        
        # Обновляем текущий плейлист и индекс для обратной совместимости
        if context == 'menu':
            self.playlist = self.menu_playlist
            self.index = self.menu_index
        elif context == 'pause':
            self.playlist = self.pause_playlist
            self.index = self.pause_index
        else:
            self.playlist = self.game_playlist
            self.index = self.game_index
            
        # Если контекст изменился и есть музыка, начинаем воспроизведение
        if old_context != context and self.enabled and len(self.playlist) > 0:
            self.play_current()
    
    def get_current_playlist(self):
        """Возвращает текущий активный плейлист."""
        if self.current_context == 'menu':
            return self.menu_playlist
        elif self.current_context == 'pause':
            return self.pause_playlist
        else:
            return self.game_playlist
    
    def get_current_index(self):
        """Возвращает текущий индекс в активном плейлисте."""
        if self.current_context == 'menu':
            return self.menu_index
        elif self.current_context == 'pause':
            return self.pause_index
        else:
            return self.game_index
    
    def set_current_index(self, index: int):
        """Устанавливает индекс в текущем плейлисте."""
        playlist = self.get_current_playlist()
        if not playlist:
            return
            
        index = max(0, min(index, len(playlist) - 1))
        
        if self.current_context == 'menu':
            self.menu_index = index
        elif self.current_context == 'pause':
            self.pause_index = index
        else:
            self.game_index = index
            
        # Обновляем для обратной совместимости
        self.index = index
        self.playlist = playlist

    def play_current(self):
        """
        Воспроизводит текущий трек из активного плейлиста.
        Обрабатывает ошибки загрузки файлов.
        """
        if not self.enabled:
            return
            
        current_playlist = self.get_current_playlist()
        if not current_playlist:
            return
            
        current_index = self.get_current_index()
        if current_index >= len(current_playlist):
            current_index = 0
            self.set_current_index(current_index)
            
        path = current_playlist[current_index]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            print(f"[AudioManager] Playing {self.current_context} music: {os.path.basename(path)}")
        except Exception as e:
            print('Failed to play', path, e)

    def next(self):
        """Переключает на следующий трек в текущем плейлисте."""
        if not self.enabled:
            return
            
        current_playlist = self.get_current_playlist()
        if not current_playlist:
            return
            
        current_index = self.get_current_index()
        new_index = (current_index + 1) % len(current_playlist)
        self.set_current_index(new_index)
        self.play_current()

    def prev(self):
        """Переключает на предыдущий трек в текущем плейлисте."""
        if not self.enabled:
            return
            
        current_playlist = self.get_current_playlist()
        if not current_playlist:
            return
            
        current_index = self.get_current_index()
        new_index = (current_index - 1) % len(current_playlist)
        self.set_current_index(new_index)
        self.play_current()

    def stop(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def play_sfx(self, name: str):
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

def draw_enhanced_background(surf):
    """Рисует улучшенный фон для главной игры"""
    # Основной градиентный фон
    screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
    draw_gradient_rect(surf, screen_rect, BG_GRADIENT_TOP, BG_GRADIENT_BOTTOM)
    
    # Анимированные декоративные элементы
    current_time = time.time()
    # Геометрические фигуры в стиле тетриса
    for i in range(6):
        # Плавная анимация позиции
        offset = math.sin(current_time * 0.5 + i * 0.8) * 20
        x = WIDTH - 80 + (i % 3) * 30 + offset * 0.3
        y = 100 + i * 90 + offset
        size = 15 + (i % 2) * 5
        
        # Пульсирующая прозрачность
        alpha = int(40 + 30 * math.sin(current_time * 1.2 + i * 0.5))
        
        # Мини-блоки как у тетромино
        decoration_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        deco_color = list(COLORS.values())[i % len(COLORS)]
        decoration_surf.fill((*deco_color, alpha))
        surf.blit(decoration_surf, (x, y))
        
        # Левая сторона с другой скоростью анимации
        x_left = 20 + (i % 2) * 25 + math.cos(current_time * 0.7 + i) * 15
        y_left = 150 + i * 80 + math.sin(current_time * 0.3 + i) * 10
        decoration_left = pygame.Surface((size, size), pygame.SRCALPHA)
        decoration_left.fill((*deco_color, alpha//2))
        surf.blit(decoration_left, (x_left, y_left))

# -------------------- Smooth Animation Utilities --------------------
def smooth_lerp(start, end, t):
    """Плавная интерполяция между двумя значениями"""
    # Easing function для более плавной анимации
    t = max(0, min(1, t))
    smooth_t = t * t * (3 - 2 * t)  # Smoothstep
    return start + (end - start) * smooth_t

def pulse_effect(time_offset=0.0, frequency=1.0, amplitude=1.0):
    """Создает пульсирующий эффект"""
    current_time = time.time()
    return amplitude * (0.5 + 0.5 * math.sin((current_time + time_offset) * frequency * 2 * math.pi))

def wave_effect(time_offset=0.0, frequency=0.5, amplitude=10):
    """Создает волновой эффект для смещения"""
    current_time = time.time()
    return amplitude * math.sin((current_time + time_offset) * frequency * 2 * math.pi)

def glow_color(base_color, intensity=0.3, time_offset=0.0):
    """Создает эффект свечения цвета"""
    glow = pulse_effect(time_offset, 0.8, intensity)
    return tuple(min(255, int(c + c * glow)) for c in base_color)

def draw_enhanced_adaptive_text(surface, text: str, rect: pygame.Rect, font_size: int = 24,
                              color=(255, 255, 255), alignment="center", bold: bool = False,
                              enable_shadow: bool = True, auto_scale: bool = True) -> pygame.Surface:
    """
    Улучшенная отрисовка адаптивного текста с правильным позиционированием.
    Использует агрессивное масштабирование для лучшей читаемости.
    """
    global responsive
    
    if not text or not text.strip():
        return surface
    
    # Определяем оптимальный размер шрифта
    if auto_scale and responsive:
        text_config = responsive.get_adaptive_text_size(text, rect.width, rect.height, font_size)
        optimal_font_size = text_config['font_size']
        max_chars_per_line = text_config['max_chars_per_line']
    else:
        optimal_font_size = font_size
        max_chars_per_line = max(1, rect.width // (font_size * 0.6))
    
    # Получаем шрифт с агрессивным масштабированием
    try:
        # Приоритетные шрифты с хорошей поддержкой кириллицы
        font = get_cached_font('arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace', optimal_font_size, bold)
    except Exception:
        # Фолбэк на стандартный шрифт
        try:
            font = pygame.font.SysFont('arial', optimal_font_size, bold=bold)
        except Exception:
            font = pygame.font.Font(None, optimal_font_size)
    
    # Разбиваем текст на строки
    lines = []
    words = text.split(' ')
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_surface = font.render(test_line, True, color)
        
        if test_surface.get_width() <= rect.width - 20:  # Оставляем отступы
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Слово слишком длинное
                lines.append(word[:max_chars_per_line])
                current_line = word[max_chars_per_line:] if len(word) > max_chars_per_line else ""
    
    if current_line:
        lines.append(current_line)
    
    # Ограничиваем количество строк
    max_lines = max(1, rect.height // (font.get_height() + 4))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1][:max(1, len(lines[-1]) - 3)] + "..."
    
    # Вычисляем позицию для центрирования
    line_height = font.get_height() + 4
    total_text_height = len(lines) * line_height
    
    if alignment == "center":
        start_y = rect.y + (rect.height - total_text_height) // 2
    elif alignment == "top":
        start_y = rect.y + 10
    elif alignment == "bottom":
        start_y = rect.y + rect.height - total_text_height - 10
    else:
        start_y = rect.y + (rect.height - total_text_height) // 2
    
    # Отрисовка строк
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        
        line_surface = font.render(line, True, color)
        line_y = start_y + i * line_height
        
        # Позиционирование по горизонтали
        if alignment == "center":
            line_x = rect.x + (rect.width - line_surface.get_width()) // 2
        elif alignment == "left":
            line_x = rect.x + 10
        elif alignment == "right":
            line_x = rect.x + rect.width - line_surface.get_width() - 10
        else:
            line_x = rect.x + (rect.width - line_surface.get_width()) // 2
        
        # Отрисовка тени для лучшей читаемости
        if enable_shadow:
            shadow_surface = font.render(line, True, (0, 0, 0))
            surface.blit(shadow_surface, (line_x + 1, line_y + 1))
        
        # Основной текст
        surface.blit(line_surface, (line_x, line_y))
    
    return surface

def draw_enhanced_adaptive_button(surface, rect: pygame.Rect, text: str, 
                                 font_size: int = 24, hover: bool = False, 
                                 active: bool = False, style: str = "default",
                                 enabled: bool = True) -> pygame.Rect:
    """
    Улучшенная отрисовка адаптивных кнопок с правильным позиционированием.
    """
    global responsive
    
    current_time = time.time()
    
    # Определяем цвета на основе состояния
    if not enabled:
        bg_color = tuple(max(0, c - 40) for c in BUTTON_BG)
        border_color = tuple(max(0, c - 30) for c in BUTTON_BORDER)
        text_color = tuple(max(0, c - 60) for c in BUTTON_TEXT)
    elif active:
        bg_color = BUTTON_BG_ACTIVE
        border_color = BUTTON_BORDER_HOVER
        text_color = BUTTON_TEXT_HOVER
    elif hover:
        bg_color = BUTTON_BG_HOVER
        border_color = BUTTON_BORDER_HOVER
        text_color = BUTTON_TEXT_HOVER
        
        # Пульсация при наведении
        pulse = pulse_effect(current_time, 1.0, 0.15)
        bg_color = glow_color(bg_color, pulse, current_time)
        text_color = glow_color(text_color, pulse * 0.5, current_time)
    else:
        bg_color = BUTTON_BG
        border_color = BUTTON_BORDER
        text_color = BUTTON_TEXT
    
    # Стили кнопок
    if style == "primary":
        bg_color = ACCENT_PRIMARY if not hover else glow_color(ACCENT_PRIMARY, 0.2, current_time)
        text_color = WHITE
    elif style == "success":
        bg_color = ACCENT_SUCCESS if not hover else glow_color(ACCENT_SUCCESS, 0.2, current_time)
        text_color = WHITE
    elif style == "danger":
        bg_color = ACCENT_DANGER if not hover else glow_color(ACCENT_DANGER, 0.2, current_time)
        text_color = WHITE
    
    # Отрисовка тени
    if enabled and (hover or active):
        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surface.fill((*PANEL_SHADOW, 80))
        surface.blit(shadow_surface, shadow_rect.topleft)
    
    # Основной фон кнопки
    pygame.draw.rect(surface, bg_color, rect, border_radius=8)
    
    # Рамка
    border_width = 3 if (hover and enabled) else 2
    pygame.draw.rect(surface, border_color, rect, border_width, border_radius=8)
    
    # Внутренний отблеск при наведении
    if hover and enabled:
        highlight_rect = rect.copy()
        highlight_rect.inflate(-6, -6)
        highlight_alpha = int(30 + 20 * pulse_effect(current_time, 1.5, 0.5))
        highlight_color = tuple(min(255, c + 20) for c in bg_color)
        highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        highlight_surface.fill((*highlight_color, highlight_alpha))
        surface.blit(highlight_surface, highlight_rect.topleft)
    
    # Отрисовка текста с адаптивным масштабированием
    text_rect = rect.copy()
    text_rect.inflate(-20, -10)  # Отступы внутри кнопки
    
    draw_enhanced_adaptive_text(
        surface, text, text_rect, font_size, 
        text_color, "center", bold=True,
        enable_shadow=(style in ["primary", "success", "danger"] or hover),
        auto_scale=True
    )
    
    return rect
def draw_gradient_rect(surf, rect, color_top, color_bottom, vertical=True, animated=False):
    """Рисует прямоугольник с плавным градиентом"""
    gradient_surf = pygame.Surface((rect.width, rect.height))
    
    # Анимированные цвета для плавных эффектов
    if animated:
        color_top = glow_color(color_top, 0.2, 0)
        color_bottom = glow_color(color_bottom, 0.2, 0.5)
    
    if vertical:
        for y in range(rect.height):
            ratio = y / rect.height
            # Плавная интерполяция для мягкого перехода
            smooth_ratio = ratio * ratio * (3 - 2 * ratio)  # Smoothstep
            r = int(color_top[0] * (1 - smooth_ratio) + color_bottom[0] * smooth_ratio)
            g = int(color_top[1] * (1 - smooth_ratio) + color_bottom[1] * smooth_ratio)
            b = int(color_top[2] * (1 - smooth_ratio) + color_bottom[2] * smooth_ratio)
            pygame.draw.line(gradient_surf, (r, g, b), (0, y), (rect.width, y))
    else:
        for x in range(rect.width):
            ratio = x / rect.width
            smooth_ratio = ratio * ratio * (3 - 2 * ratio)
            r = int(color_top[0] * (1 - smooth_ratio) + color_bottom[0] * smooth_ratio)
            g = int(color_top[1] * (1 - smooth_ratio) + color_bottom[1] * smooth_ratio)
            b = int(color_top[2] * (1 - smooth_ratio) + color_bottom[2] * smooth_ratio)
            pygame.draw.line(gradient_surf, (r, g, b), (x, 0), (x, rect.height))
    
    surf.blit(gradient_surf, rect.topleft)

def draw_shadow(surf, rect, offset=(3, 3), blur=2, color=PANEL_SHADOW):
    """Рисует тень для прямоугольника"""
    shadow_rect = rect.copy()
    shadow_rect.x += offset[0]
    shadow_rect.y += offset[1]
    
    # Простая тень без размытия для производительности
    shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
    shadow_surf.fill((*color, 80))  # Полупрозрачная тень
    surf.blit(shadow_surf, shadow_rect.topleft)

def draw_enhanced_panel(surf, rect, title=None, font=None, animated=False):
    """Рисует улучшенную панель с плавными эффектами"""
    # Многослойная тень для глубины
    for i in range(3):
        shadow_offset = (2 + i, 2 + i)
        shadow_alpha = 60 - i * 15
        shadow_rect = rect.copy()
        shadow_rect.x += shadow_offset[0]
        shadow_rect.y += shadow_offset[1]
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((*PANEL_SHADOW, shadow_alpha))
        surf.blit(shadow_surf, shadow_rect.topleft)
    
    # Основной фон с плавным градиентом
    if animated:
        panel_top = glow_color((35, 40, 50), 0.15, 0)
        panel_bottom = glow_color((25, 30, 38), 0.1, 0.3)
    else:
        panel_top = (35, 40, 50)
        panel_bottom = (25, 30, 38)
    
    draw_gradient_rect(surf, rect, panel_top, panel_bottom, animated=animated)
    
    # Многослойная рамка
    # Основная рамка
    border_color = glow_color(PANEL_BORDER, 0.1, 0) if animated else PANEL_BORDER
    pygame.draw.rect(surf, border_color, rect, 2, border_radius=12)
    
    # Внутренняя подсветка
    inner_rect = rect.copy()
    inner_rect.inflate(-4, -4)
    inner_color = (45, 52, 65) if not animated else glow_color((45, 52, 65), 0.2, 0.7)
    pygame.draw.rect(surf, inner_color, inner_rect, 1, border_radius=10)
    
    # Наружное свечение (для анимированных панелей)
    if animated:
        glow_rect = rect.copy()
        glow_rect.inflate(4, 4)
        glow_alpha = int(20 + 15 * pulse_effect(0, 0.5))
        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        glow_surf.fill((*ACCENT_PRIMARY, glow_alpha))
        surf.blit(glow_surf, glow_rect.topleft)
    
    # Заголовок (если указан)
    if title and font:
        title_color = glow_color(WHITE, 0.1, 0) if animated else WHITE
        title_surf = font.render(title, True, title_color)
        title_x = rect.x + (rect.width - title_surf.get_width()) // 2
        title_y = rect.y + 10
        surf.blit(title_surf, (title_x, title_y))

# -------------------- Enhanced Drawing --------------------
def draw_block(surf, x, y, color, border=True, alpha=None, enhanced=True, animate_glow=False, kind=None):
    rect = pygame.Rect(x, y, BLOCK-1, BLOCK-1)
    corner_radius = 8  # Увеличиваем радиус закругления для более мягкого вида
    
    if enhanced:
        # Полная заливка цветом без градиентов
        base_color = color
        # Полная заливка цветом с отблесками
        if alpha is not None:
            # Полупрозрачный блок (для ghost piece)
            block_surf = pygame.Surface((BLOCK-1, BLOCK-1), pygame.SRCALPHA)
            pygame.draw.rect(block_surf, (*base_color, alpha), block_surf.get_rect(), border_radius=corner_radius)
            surf.blit(block_surf, rect.topleft)
        else:
            # Обычный блок с полной заливкой и отблесками
            pygame.draw.rect(surf, base_color, rect, border_radius=corner_radius)
            
            # Верхний отблеск (светлый)
            highlight_rect = pygame.Rect(x + 2, y + 2, BLOCK - 6, 6)
            highlight_color = tuple(min(255, c + 80) for c in base_color)
            pygame.draw.rect(surf, highlight_color, highlight_rect, border_radius=corner_radius//2)
            
            # Левый отблеск
            left_highlight = pygame.Rect(x + 2, y + 2, 4, BLOCK - 6)
            pygame.draw.rect(surf, highlight_color, left_highlight, border_radius=corner_radius//2)
            
            # Нижняя тень
            shadow_rect = pygame.Rect(x + 4, y + BLOCK - 8, BLOCK - 8, 4)
            shadow_color = tuple(max(0, c - 60) for c in base_color)
            pygame.draw.rect(surf, shadow_color, shadow_rect, border_radius=corner_radius//2)
            
            # Правая тень
            right_shadow = pygame.Rect(x + BLOCK - 8, y + 4, 4, BLOCK - 8)
            pygame.draw.rect(surf, shadow_color, right_shadow, border_radius=corner_radius//2)
            
        if border:
            # Красивая рамка с закругленными углами
            border_color = tuple(max(0, c - 80) for c in base_color)
            pygame.draw.rect(surf, border_color, rect, 2, border_radius=corner_radius)
    else:
        # Оригинальная отрисовка с закругленными углами
        if alpha is not None:
            block = pygame.Surface((BLOCK-1, BLOCK-1), pygame.SRCALPHA)
            c = (*color, alpha)
            pygame.draw.rect(block, c, block.get_rect(), border_radius=corner_radius)
            surf.blit(block, rect.topleft)
        else:
            pygame.draw.rect(surf, color, rect, border_radius=corner_radius)
        if border:
            pygame.draw.rect(surf, (0,0,0), rect, 2, border_radius=corner_radius)

def draw_grid(surf, origin_x, origin_y, state: GameState):
    # Улучшенная отрисовка игрового поля
    playfield_rect = pygame.Rect(origin_x, origin_y, PLAY_W, PLAY_H)
    
    # Тень игрового поля
    draw_shadow(surf, playfield_rect, (4, 4))
    
    # Фон с градиентом
    bg_top = (28, 32, 40)
    bg_bottom = (20, 24, 32)
    draw_gradient_rect(surf, playfield_rect, bg_top, bg_bottom)
    
    # Внешняя рамка с более выраженными закругленными углами
    field_corner_radius = 16  # Увеличиваем радиус закругления для игрового поля
    pygame.draw.rect(surf, PLAYFIELD_BORDER, playfield_rect, 3, border_radius=field_corner_radius)
    
    # Внутренняя подсветка с соответствующим радиусом
    inner_rect = playfield_rect.copy()
    inner_rect.inflate(-6, -6)
    pygame.draw.rect(surf, (45, 50, 62), inner_rect, 1, border_radius=field_corner_radius-3)
    
    # Линии сетки (более тонкие)
    grid_color = (35, 40, 50)
    for i in range(1, PLAY_COLS):
        x = origin_x + i * BLOCK
        pygame.draw.line(surf, grid_color, (x, origin_y + 3), (x, origin_y + PLAY_H - 3))
    for j in range(1, PLAY_ROWS):
        y = origin_y + j * BLOCK
        pygame.draw.line(surf, grid_color, (origin_x + 3, y), (origin_x + PLAY_W - 3, y))
    
    # Отрисовка блоков
    for y in range(PLAY_ROWS):
        for x in range(PLAY_COLS):
            kind = state.grid[y][x]
            if kind:
                color = COLORS[kind]
                draw_block(surf, origin_x + x*BLOCK, origin_y + y*BLOCK, color, kind=kind)

def draw_piece(surf, origin_x, origin_y, piece: Piece, ghost=False, animate_current=False):
    if piece is None:
        return
    color = GHOST if ghost else COLORS[piece.kind]
    for x, y in piece.cells():
        if y >= 0:
            # Анимированные эффекты для текущей фигуры
            use_animation = animate_current and not ghost
            kind = piece.kind if not ghost else None
            draw_block(surf, origin_x + x*BLOCK, origin_y + y*BLOCK, color, 
                      border=not ghost, alpha=120 if ghost else None, 
                      animate_glow=use_animation, kind=kind)

def draw_panel(surf, origin_x, origin_y, state: GameState, font, small, audio: AudioManager):
    current_time = time.time()
    
    # Основная панель с плавной анимацией
    panel_float = wave_effect(current_time, 0.5, 2)
    panel_rect = pygame.Rect(origin_x - 10, origin_y - 10 + int(panel_float), PANEL_W + 20, HEIGHT - 40)
    draw_enhanced_panel(surf, panel_rect, animated=True)
    
    # Анимированный заголовок TETRIS
    title_rect = pygame.Rect(origin_x, origin_y + int(panel_float), PANEL_W, 50)
    title_pulse = pulse_effect(0, 0.8, 0.2)
    title_top = glow_color(ACCENT_PRIMARY, title_pulse, 0)
    title_bottom = glow_color(ACCENT_SECONDARY, title_pulse, 0.5)
    draw_gradient_rect(surf, title_rect, title_top, title_bottom, vertical=False, animated=True)
    pygame.draw.rect(surf, glow_color((100, 120, 150), 0.3, current_time), title_rect, 1, border_radius=8)
    
    title = font.render("TETRIS", True, WHITE)
    title_shadow = font.render("TETRIS", True, (0, 0, 0))
    title_x = origin_x + (PANEL_W - title.get_width()) // 2
    title_y = origin_y + (50 - title.get_height()) // 2
    surf.blit(title_shadow, (title_x + 2, title_y + 2))
    surf.blit(title, (title_x, title_y))
    
    def draw_info_section(y_pos, title_text, content_lines, accent_color=ACCENT_PRIMARY):
        """Рисует секцию информации с заголовком и содержимым"""
        section_rect = pygame.Rect(origin_x + 5, y_pos, PANEL_W - 10, len(content_lines) * 26 + 30)
        
        # Фон секции
        section_bg_top = (30, 35, 45)
        section_bg_bottom = (25, 30, 38)
        draw_gradient_rect(surf, section_rect, section_bg_top, section_bg_bottom)
        pygame.draw.rect(surf, (50, 60, 75), section_rect, 1, border_radius=6)
        
        # Заголовок секции
        title_surf = small.render(title_text, True, accent_color)
        surf.blit(title_surf, (origin_x + 10, y_pos + 5))
        
        # Содержимое
        for i, line in enumerate(content_lines):
            text_surf = small.render(line, True, WHITE)
            surf.blit(text_surf, (origin_x + 15, y_pos + 25 + i * 22))
        
        return y_pos + section_rect.height + 10
    
    y = origin_y + 70
    
    # Информация о режиме игры
    mode_info = []
    mode_name = get_mode_display_name(state.game_mode)
    mode_info.append(f'Режим: {mode_name}')
    
    # Информация о кампании (если активна)
    if state.game_mode == GameMode.CAMPAIGN and state.current_campaign_level <= len(CAMPAIGN_LEVELS):
        level_config = CAMPAIGN_LEVELS[state.current_campaign_level - 1]
        mode_info.append(f'Уровень {state.current_campaign_level}: {level_config.name}')
        
        # Отображение целей
        objectives_info = []
        for obj in level_config.objectives:
            current_progress = state.campaign_objectives_progress.get(obj.type, 0)
            if obj.type == "time":
                mins = current_progress // 60
                secs = current_progress % 60
                target_mins = obj.target // 60
                target_secs = obj.target % 60
                progress_text = f'{mins:02d}:{secs:02d}/{target_mins:02d}:{target_secs:02d}'
            else:
                progress_text = f'{current_progress}/{obj.target}'
            
            completed = current_progress >= obj.target
            status = "✓" if completed else "○"
            objectives_info.append(f'{status} {obj.description}: {progress_text}')
        
        y = draw_info_section(y, "ЗАДАЧИ", objectives_info, ACCENT_WARNING)
    else:
        y = draw_info_section(y, "РЕЖИМ ИГРЫ", mode_info, ACCENT_PRIMARY)
    
    # Игровая статистика
    stats_info = [
        f"Очки: {state.score:,}",
        f"Линии: {state.lines}",
        f"Уровень: {state.level}"
    ]
    if state.combo >= 1:
        stats_info.append(f"Комбо: x{state.combo}")
    
    y = draw_info_section(y, "СТАТИСТИКА", stats_info, ACCENT_SUCCESS)
    
    # Следующие фигуры - более компактный вертикальный столбец
    next_section_width = int((PANEL_W - 10) * 0.6)  # 60% ширины панели для следующих фигур
    buttons_section_width = int((PANEL_W - 10) * 0.35)  # 35% для кнопок
    
    next_rect = pygame.Rect(origin_x + 5, y, next_section_width, 320)
    draw_gradient_rect(surf, next_rect, (30, 35, 45), (25, 30, 38))
    pygame.draw.rect(surf, (50, 60, 75), next_rect, 1, border_radius=6)
    
    next_title = small.render("СЛЕДУЮЩИЕ", True, ACCENT_SECONDARY)
    surf.blit(next_title, (origin_x + 10, y + 5))
    
    ny = y + 25
    # Меньшие мини-фигуры для более компактного вида
    for i, kind in enumerate(state.next_queue[:5]):
        mini_y = ny + i * 55  # Меньший интервал
        draw_mini_compact(surf, origin_x + 5, mini_y, kind, small, next_section_width)
    
    # Кнопки с описаниями справа - расширяем и добавляем больше информации
    buttons_x = origin_x + next_section_width + 15
    buttons_rect = pygame.Rect(buttons_x, y, buttons_section_width, 400)  # Увеличиваем высоту
    draw_gradient_rect(surf, buttons_rect, (30, 35, 45), (25, 30, 38))
    pygame.draw.rect(surf, (50, 60, 75), buttons_rect, 1, border_radius=6)
    
    buttons_title = small.render("УПРАВЛЕНИЕ", True, ACCENT_PRIMARY)
    surf.blit(buttons_title, (buttons_x + 5, y + 5))
    
    # Основные действия с клавишами
    main_actions = [
        ("Движение", "← →", ACCENT_PRIMARY),
        ("Мягкое пад.", "↓", ACCENT_SUCCESS),
        ("Жёсткое пад.", "Space", ACCENT_WARNING),
        ("Поворот", "Z/↑", ACCENT_PRIMARY),
        ("Обратный", "X", ACCENT_SECONDARY),
        ("Резерв", "C/Shift", ACCENT_DANGER),
        ("Пауза", "P/Esc", (160, 160, 180)),
        ("Рестарт", "R", (180, 140, 100))
    ]
    
    for i, (action, key, color) in enumerate(main_actions):
        btn_y = y + 30 + i * 42
        btn_rect = pygame.Rect(buttons_x + 5, btn_y, buttons_section_width - 10, 32)
        
        # Фон кнопки
        button_bg = tuple(max(0, c - 30) for c in color)
        pygame.draw.rect(surf, button_bg, btn_rect, border_radius=4)
        pygame.draw.rect(surf, color, btn_rect, 1, border_radius=4)
        
        # Текст действия
        action_surf = small.render(action, True, WHITE)
        surf.blit(action_surf, (buttons_x + 8, btn_y + 2))
        
        # Клавиша
        key_surf = small.render(key, True, color)
        key_x = buttons_x + buttons_section_width - key_surf.get_width() - 8
        surf.blit(key_surf, (key_x, btn_y + 13))
    
    # Hold фигура - размещаем под следующими фигурами
    hold_y = y + 330
    hold_rect = pygame.Rect(origin_x + 5, hold_y, next_section_width, 70)
    draw_gradient_rect(surf, hold_rect, (30, 35, 45), (25, 30, 38))
    pygame.draw.rect(surf, (50, 60, 75), hold_rect, 1, border_radius=6)
    
    hold_title = small.render("РЕЗЕРВ", True, ACCENT_SECONDARY)
    surf.blit(hold_title, (origin_x + 10, hold_y + 5))
    
    draw_mini_compact(surf, origin_x + 5, hold_y + 20, state.hold, small, next_section_width)
    
    # Управление и музыка внизу
    help_y = hold_y + 80  # Под hold секцией
    controls = [
        "← → : Движение",
        "↓ : Мягкое падение (2x)", 
        "Space : Мягкое/Жесткое падение",
        "Z / ↑ : Поворот",
        "X : Обратный поворот",
        "C/Shift : Резерв",
        "P/Esc : Пауза, R : Рестарт",
    ]
    
    control_rect = pygame.Rect(origin_x + 5, help_y, PANEL_W - 10, len(controls) * 18 + 20)
    draw_gradient_rect(surf, control_rect, (25, 30, 38), (20, 25, 33))
    pygame.draw.rect(surf, (45, 55, 70), control_rect, 1, border_radius=6)
    
    control_title = small.render("УПРАВЛЕНИЕ", True, DIM)
    surf.blit(control_title, (origin_x + 10, help_y + 5))
    
    for i, line in enumerate(controls):
        t = small.render(line, True, (180, 185, 195))
        surf.blit(t, (origin_x + 10, help_y + 25 + i * 18))
    
    # Информация о музыке
    if audio.enabled:
        music_y = help_y - 25
        music_name = os.path.basename(audio.playlist[audio.index])
        if len(music_name) > 30:
            music_name = music_name[:27] + "..."
        music_text = small.render(f"♪ {music_name}", True, ACCENT_SECONDARY)
        surf.blit(music_text, (origin_x + 5, music_y))

def draw_mini_compact(surf, origin_x, origin_y, kind: Optional[str], small, width):
    """Отрисовка компактной мини-фигуры для вертикального столбца"""
    box = pygame.Rect(origin_x, origin_y, width, 50)  # Меньшая высота для компактности
    
    # Основной фон с градиентом
    draw_gradient_rect(surf, box, (35, 40, 50), (25, 30, 38))
    pygame.draw.rect(surf, (60, 70, 85), box, 1, border_radius=4)
    
    if not kind:
        # Пустое место
        empty_text = small.render("Пусто", True, DIM)
        text_x = box.x + (box.width - empty_text.get_width()) // 2
        text_y = box.y + (box.height - empty_text.get_height()) // 2
        surf.blit(empty_text, (text_x, text_y))
        return
    
    grid = ROTATED[kind][0]
    cells = [(i, j) for j in range(4) for i in range(4) if grid[j][i] != '.']
    if not cells:
        return
    
    minx = min(i for i, _ in cells)
    maxx = max(i for i, _ in cells)
    miny = min(j for _, j in cells)
    maxy = max(j for _, j in cells)
    w = maxx - minx + 1
    h = maxy - miny + 1
    scale = 12  # Меньший масштаб для компактности
    offset_x = origin_x + 5 + (width - 10 - w*scale) // 2
    offset_y = origin_y + 5 + (40 - h*scale) // 2
    
    for i, j in cells:
        x = (i - minx) * scale
        y = (j - miny) * scale
        rect = pygame.Rect(offset_x + x, offset_y + y, scale-1, scale-1)
        
        # Мини-версия блока с отблесками
        color = COLORS[kind]
        mini_corner_radius = 2
        
        # Основная заливка цветом
        pygame.draw.rect(surf, color, rect, border_radius=mini_corner_radius)
        
        # Мини-отблеск
        if scale > 8:  # Только если блок достаточно большой
            highlight_size = max(1, scale//6)
            highlight_rect = pygame.Rect(offset_x + x + 1, offset_y + y + 1, highlight_size, highlight_size)
            highlight_color = tuple(min(255, c + 60) for c in color)
            pygame.draw.rect(surf, highlight_color, highlight_rect, border_radius=1)
        
        # Рамка
        border_color = tuple(max(0, c - 30) for c in color)
        pygame.draw.rect(surf, border_color, rect, 1, border_radius=mini_corner_radius)

def draw_mini(surf, origin_x, origin_y, kind: Optional[str], small):
    box = pygame.Rect(origin_x, origin_y, PANEL_W-10, 80)
    
    # Улучшенный фон с градиентом
    draw_enhanced_panel(surf, box)
    
    if not kind:
        # Пустое место
        empty_text = small.render("Пусто", True, DIM)
        text_x = box.x + (box.width - empty_text.get_width()) // 2
        text_y = box.y + (box.height - empty_text.get_height()) // 2
        surf.blit(empty_text, (text_x, text_y))
        return
    
    grid = ROTATED[kind][0]
    cells = [(i, j) for j in range(4) for i in range(4) if grid[j][i] != '.']
    if not cells:
        return
    
    minx = min(i for i, _ in cells)
    maxx = max(i for i, _ in cells)
    miny = min(j for _, j in cells)
    maxy = max(j for _, j in cells)
    w = maxx - minx + 1
    h = maxy - miny + 1
    scale = 18  # Немного меньше для лучшего вида
    offset_x = origin_x + 10 + (PANEL_W - 20 - w*scale) // 2
    offset_y = origin_y + 8 + (80 - 16 - h*scale) // 2
    
    for i, j in cells:
        x = (i - minx) * scale
        y = (j - miny) * scale
        rect = pygame.Rect(offset_x + x, offset_y + y, scale-2, scale-2)
        
        # Мини-версия блока с отблесками и закругленными углами
        color = COLORS[kind]
        mini_corner_radius = 3  # Меньший радиус для мини-блоков
        
        # Основная заливка цветом
        pygame.draw.rect(surf, color, rect, border_radius=mini_corner_radius)
        
        # Мини-отблеск
        highlight_size = max(2, scale//4)
        highlight_rect = pygame.Rect(offset_x + x + 1, offset_y + y + 1, highlight_size, highlight_size)
        highlight_color = tuple(min(255, c + 80) for c in color)
        pygame.draw.rect(surf, highlight_color, highlight_rect, border_radius=1)
        
        # Рамка с закругленными углами
        border_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(surf, border_color, rect, 1, border_radius=mini_corner_radius)

# -------------------- Game Mode Functions --------------------

def initialize_game_mode(state: GameState, mode: GameMode, campaign_level: int = 1):
    """Инициализация игрового режима"""
    state.game_mode = mode
    state.mode_config = GAME_MODE_CONFIGS[mode]
    state.session_start_time = pygame.time.get_ticks() / 1000.0
    
    if mode == GameMode.CAMPAIGN:
        state.current_campaign_level = campaign_level
        # Устанавливаем начальные параметры уровня
        if campaign_level <= len(CAMPAIGN_LEVELS):
            level_config = CAMPAIGN_LEVELS[campaign_level - 1]
            state.level = level_config.starting_level
            state.campaign_objectives_progress = {}
            for obj in level_config.objectives:
                state.campaign_objectives_progress[obj.type] = 0
    
    # Применяем модификаторы скорости
    state.fall_interval = gravity_for_level(state.level) * state.mode_config.gravity_multiplier

def update_campaign_progress(state: GameState):
    """Постоянное обновление прогресса целей кампании"""
    if state.game_mode != GameMode.CAMPAIGN:
        return
    
    if state.current_campaign_level > len(CAMPAIGN_LEVELS):
        return
    
    level_config = CAMPAIGN_LEVELS[state.current_campaign_level - 1]
    
    for obj in level_config.objectives:
        if obj.type == "lines":
            state.campaign_objectives_progress["lines"] = state.lines
        elif obj.type == "score":
            state.campaign_objectives_progress["score"] = state.score
        elif obj.type == "time":
            current_time = pygame.time.get_ticks() / 1000.0
            elapsed = current_time - state.session_start_time
            state.campaign_objectives_progress["time"] = int(elapsed)

def check_campaign_objectives(state: GameState) -> bool:
    """Проверка выполнения целей кампании"""
    if state.game_mode != GameMode.CAMPAIGN:
        return False
    
    if state.current_campaign_level > len(CAMPAIGN_LEVELS):
        return False
    
    level_config = CAMPAIGN_LEVELS[state.current_campaign_level - 1]
    all_completed = True
    
    # Просто проверяем, выполнены ли все цели
    for obj in level_config.objectives:
        current_progress = state.campaign_objectives_progress.get(obj.type, 0)
        if current_progress < obj.target:
            all_completed = False
            break
    
    return all_completed

def unlock_next_campaign_level():
    """Открывает следующий уровень кампании"""
    # Логика открытия следующего уровня
    # В будущем можно сохранять прогресс в отдельный файл
    pass

def get_mode_display_name(mode: GameMode) -> str:
    """Получает отображаемое имя режима"""
    return GAME_MODE_CONFIGS[mode].name

def apply_mode_gravity_modifier(base_gravity: float, mode: GameMode) -> float:
    """Применяет модификатор скорости для режима"""
    config = GAME_MODE_CONFIGS.get(mode)
    if config:
        return base_gravity * config.gravity_multiplier
    return base_gravity

def apply_mode_score_modifier(base_score: int, mode: GameMode) -> int:
    """Применяет модификатор очков для режима"""
    config = GAME_MODE_CONFIGS.get(mode)
    if config:
        return int(base_score * config.scoring_multiplier)
    return base_score

# -------------------- Save / Load --------------------

SAVE_FILE = 'saves/tetris_save.json'
SAVE_DIR = 'saves'

def ensure_save_directory():
    """Создаёт папку saves, если её нет."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        print(f'Создана папка для сохранений: {SAVE_DIR}')

def save_game(state: GameState, filename: str = SAVE_FILE):
    try:
        ensure_save_directory()  # Убеждаемся, что папка существует
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        print('Игра сохранена в', filename)
    except Exception as e:
        print('Ошибка сохранения:', e)

def load_game(filename: str = SAVE_FILE) -> Optional[GameState]:
    if not os.path.isfile(filename):
        print('Файл сохранения не найден:', filename)
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
        state = GameState.from_dict(d)
        print('Игра загружена из', filename)
        return state
    except Exception as e:
        print('Ошибка загрузки:', e)
        return None

# -------------------- Menus --------------------
def button_rect(x, y, w, h):
    return pygame.Rect(x, y, w, h)

# Глобальные переменные для отслеживания переходов мыши
mouse_transition_states = {}  # rect_id -> {transition_progress, last_hover_time, is_hovering}
click_states = {}  # rect_id -> {click_start_time, is_clicking}

def get_button_id(rect: pygame.Rect) -> str:
    """Генерирует уникальный ID для кнопки на основе её позиции"""
    return f"{rect.x}_{rect.y}_{rect.width}_{rect.height}"

def update_mouse_transition(rect: pygame.Rect, is_hovering: bool, dt: float) -> float:
    """Обновляет и возвращает прогресс перехода для кнопки (0.0 - 1.0)"""
    button_id = get_button_id(rect)
    current_time = time.time()
    
    if button_id not in mouse_transition_states:
        mouse_transition_states[button_id] = {
            'transition_progress': 0.0,
            'last_hover_time': current_time,
            'is_hovering': False,
            'target_progress': 0.0
        }
    
    state = mouse_transition_states[button_id]
    
    # Обновляем целевое состояние
    if is_hovering != state['is_hovering']:
        state['is_hovering'] = is_hovering
        state['last_hover_time'] = current_time
    
    # Плавный переход к целевому значению
    target = 1.0 if is_hovering else 0.0
    transition_speed = 8.0  # Скорость перехода
    
    if state['transition_progress'] < target:
        state['transition_progress'] = min(target, state['transition_progress'] + transition_speed * dt)
    elif state['transition_progress'] > target:
        state['transition_progress'] = max(target, state['transition_progress'] - transition_speed * dt)
    
    return state['transition_progress']

def handle_click_effect(rect: pygame.Rect, is_clicked: bool) -> bool:
    """Обрабатывает эффект клика для кнопки"""
    button_id = get_button_id(rect)
    current_time = time.time()
    
    if is_clicked:
        if button_id not in click_states:
            click_states[button_id] = {
                'click_start_time': current_time,
                'is_clicking': True
            }
        return True
    else:
        # Убираем состояние клика через короткое время
        if button_id in click_states:
            if current_time - click_states[button_id]['click_start_time'] > 0.15:
                del click_states[button_id]
                return False
            return True
        return False

def set_cursor_for_interaction(is_interactive: bool):
    """Устанавливает соответствующий курсор мыши"""
    if is_interactive:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

def handle_enhanced_button_interaction(rect: pygame.Rect, mouse_pos: tuple, mouse_clicked: bool, dt: float) -> tuple:
    """Комплексная обработка взаимодействия с кнопкой. Возвращает (hover, transition_progress, click_effect)"""
    is_hovering = rect.collidepoint(mouse_pos)
    transition_progress = update_mouse_transition(rect, is_hovering, dt)
    
    # Проверяем клик только если мышь наведена
    is_clicked = is_hovering and mouse_clicked
    click_effect = handle_click_effect(rect, is_clicked)
    
    return is_hovering, transition_progress, click_effect



def get_adaptive_font(text: str, base_font, max_width: int, max_height: int, use_responsive: bool = True):
    """
    Кардинально улучшенная функция адаптивного масштабирования шрифта с кэшированием.
    Автоматически масштабирует шрифт для помещения текста в заданные размеры.
    """
    global responsive, _adaptive_font_cache
    
    # Создаем ключ кэша
    cache_key = f"{hash(text[:50]) if len(text) > 0 else 0}_{max_width}_{max_height}_{base_font.get_height()}_{use_responsive}"
    
    if cache_key in _adaptive_font_cache:
        return _adaptive_font_cache[cache_key]
    
    # Приоритетные шрифты с хорошей поддержкой кириллицы
    font_path = 'arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace'
    is_bold = True
    
    # Значительно увеличенный начальный размер с учетом адаптивности
    if responsive and use_responsive:
        base_size = responsive.scale_font(base_font.get_height())
    else:
        base_size = base_font.get_height()
    
    # Начинаем с увеличенного размера и минимумом 18px
    current_size = max(18, int(base_size * 0.9))  # Начинаем с 90% от базового
    
    # Быстрая оценка - если текст короткий, скорее всего поместится
    if len(text) <= 5:
        font = get_cached_font(font_path, current_size, is_bold)
        _adaptive_font_cache[cache_key] = font
        return font
    
    # Адаптация к длинному тексту
    if len(text) > 20:
        current_size = max(18, int(current_size * 0.7))
    elif len(text) > 15:
        current_size = max(18, int(current_size * 0.8))
    elif len(text) > 10:
        current_size = max(18, int(current_size * 0.9))
    
    # Предварительная оценка размера
    char_width_estimate = current_size * 0.6
    estimated_width = len(text) * char_width_estimate
    
    if estimated_width > max_width:
        scale_factor = max_width / estimated_width
        current_size = max(18, int(current_size * scale_factor * 0.9))
    
    # Точная проверка (максимум 5 итераций)
    for attempt in range(5):
        try:
            test_font = get_cached_font(font_path, current_size, is_bold)
            text_surface = test_font.render(text, True, (255, 255, 255))
            
            if (text_surface.get_width() <= max_width and 
                text_surface.get_height() <= max_height):
                # Пытаемся увеличить (но не больше базового)
                max_allowed_size = int(base_size * 0.85)
                if current_size < max_allowed_size and attempt < 2:
                    larger_size = min(current_size + 1, max_allowed_size)
                    larger_font = get_cached_font(font_path, larger_size, is_bold)
                    larger_surface = larger_font.render(text, True, (255, 255, 255))
                    
                    if (larger_surface.get_width() <= max_width and 
                        larger_surface.get_height() <= max_height):
                        current_size = larger_size
                        continue
                
                # Текущий размер оптимален
                _adaptive_font_cache[cache_key] = test_font
                return test_font
            else:
                # Уменьшаем размер
                current_size = max(18, current_size - max(1, current_size // 15))
                
        except Exception:
            current_size = max(18, current_size - 2)
    
    # Финальный результат
    final_font = get_cached_font(font_path, current_size, is_bold)
    _adaptive_font_cache[cache_key] = final_font
    
    # Ограничиваем размер кэша
    if len(_adaptive_font_cache) > 30:
        oldest_keys = list(_adaptive_font_cache.keys())[:10]
        for old_key in oldest_keys:
            del _adaptive_font_cache[old_key]
    
    return final_font
    
    if estimated_width > max_width:
        scale_factor = max_width / estimated_width
        current_size = max(8, int(current_size * scale_factor * 0.9))
    
    # Точная проверка (максимум 5 итераций)
    for attempt in range(5):
        try:
            test_font = get_cached_font(font_path, current_size, is_bold)
            text_surface = test_font.render(text, True, (255, 255, 255))
            
            if (text_surface.get_width() <= max_width and 
                text_surface.get_height() <= max_height):
                # Пытаемся увеличить (но не больше базового)
                max_allowed_size = int(base_size * 0.85)
                if current_size < max_allowed_size and attempt < 2:
                    larger_size = min(current_size + 1, max_allowed_size)
                    larger_font = get_cached_font(font_path, larger_size, is_bold)
                    larger_surface = larger_font.render(text, True, (255, 255, 255))
                    
                    if (larger_surface.get_width() <= max_width and 
                        larger_surface.get_height() <= max_height):
                        current_size = larger_size
                        continue
                
                # Текущий размер оптимален
                _adaptive_font_cache[cache_key] = test_font
                return test_font
            else:
                # Уменьшаем размер
                current_size = max(8, current_size - max(1, current_size // 15))
                
        except Exception:
            current_size = max(8, current_size - 2)
    
    # Финальный результат
    final_font = get_cached_font(font_path, current_size, is_bold)
    _adaptive_font_cache[cache_key] = final_font
    
    # Ограничиваем размер кэша
    if len(_adaptive_font_cache) > 30:
        oldest_keys = list(_adaptive_font_cache.keys())[:10]
        for old_key in oldest_keys:
            del _adaptive_font_cache[old_key]
    
    return final_font

def init_responsive_design_with_config():
    """
    Объединенная функция инициализации улучшенной адаптивной системы.
    """
    global responsive, WIDTH, HEIGHT, ORIGIN_X, ORIGIN_Y, PLAY_W, PLAY_H, BLOCK, PANEL_W, MARGIN, game_config
    
    try:
        # Используем разрешение из конфигурации
        WIDTH = game_config.screen_width
        HEIGHT = game_config.screen_height
        
        print(f"[AdvancedResponsiveDesign] Использование конфигурации: {WIDTH}x{HEIGHT}")
        
        # Определяем DPI (пока используем стандартное значение)
        dpi = 96.0  # Можно расширить в будущем
        
        # Создаем новую улучшенную систему
        responsive = AdvancedResponsiveDesign(WIDTH, HEIGHT, dpi)
        
        # Применяем множители из конфигурации
        if hasattr(game_config, 'ui_scale_factor') and game_config.ui_scale_factor != 1.0:
            print(f"[AdvancedResponsiveDesign] Применение UI множителя: {game_config.ui_scale_factor}")
            # Корректируем масштабирование с учетом конфигурации
            for key in responsive.scale_factors:
                responsive.scale_factors[key] *= game_config.ui_scale_factor
        
        # Обновляем позиции игрового поля
        ORIGIN_X, ORIGIN_Y, PLAY_W, PLAY_H, BLOCK = responsive.get_grid_position()
        MARGIN = responsive.get_margin(25)
        PANEL_W = responsive.get_panel_position(ORIGIN_X, PLAY_W)[2]
        
        print(f"[AdvancedResponsiveDesign] Оптимизированная компоновка: Поле на ({ORIGIN_X}, {ORIGIN_Y}), Размер: {PLAY_W}x{PLAY_H}, Блок: {BLOCK}px")
        print(f"[AdvancedResponsiveDesign] Панель: Ширина {PANEL_W}px, Отступ: {MARGIN}px")
        
    except Exception as e:
        print(f"[AdvancedResponsiveDesign] Ошибка инициализации: {e}")
        print(f"[AdvancedResponsiveDesign] Использование стандартных настроек: {WIDTH}x{HEIGHT}")
        responsive = AdvancedResponsiveDesign(WIDTH, HEIGHT)
        
        # Fallback: обновляем позиции
        ORIGIN_X, ORIGIN_Y, PLAY_W, PLAY_H, BLOCK = responsive.get_grid_position()
        MARGIN = responsive.get_margin(25)
        PANEL_W = responsive.get_panel_position(ORIGIN_X, PLAY_W)[2]
    
    return WIDTH, HEIGHT



def get_menu_button_font(text: str, base_font, max_width: int, max_height: int):
    """
    Кардинально улучшенная функция для кнопок меню с оптимальным масштабированием.
    """
    global responsive
    
    # Приоритетные шрифты с хорошей поддержкой кириллицы
    font_path = 'arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace'
    is_bold = True
    
    # Определяем значительно увеличенные базовые размеры
    if responsive:
        screen_width = responsive.screen_width
        if screen_width >= 1920:
            base_size = 36  # Очень большой для 4K/1920+
        elif screen_width >= 1600:
            base_size = 32  # Большой для 1600+
        elif screen_width >= 1366:
            base_size = 28  # Средний для 1366+
        elif screen_width >= 1280:
            base_size = 26  # Стандартный для 1280+
        else:
            base_size = 24  # Минимальный
    else:
        base_size = 26  # Большое значение по умолчанию
    
    # Начинаем с оптимального размера (без уменьшения)
    current_size = base_size
    
    # Минимальное сокращение только для очень длинного текста
    if len(text) > 40:
        current_size = max(16, int(current_size * 0.85))
    elif len(text) > 25:
        current_size = max(18, int(current_size * 0.9))
    
    # Простой подбор размера (максимум 15 попыток)
    for attempt in range(15):
        try:
            test_font = pygame.font.SysFont(font_path, current_size, bold=is_bold)
            text_surface = test_font.render(text, True, (255, 255, 255))
            
            if (text_surface.get_width() <= max_width and 
                text_surface.get_height() <= max_height):
                return test_font
            else:
                current_size = max(18, current_size - 1)  # Минимум 18px
        except Exception:
            current_size = max(18, current_size - 1)
    
    # Минимальный читаемый размер
    try:
        return pygame.font.SysFont(font_path, 18, bold=is_bold)
    except Exception:
        return base_font

def wrap_text_for_button(text: str, font, max_width: int):
    """
    Разбивает длинный текст на несколько строк для кнопки.
    Возвращает список строк, которые помещаются в указанную ширину.
    """
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_surface = font.render(test_line, True, (255, 255, 255))
        
        if test_surface.get_width() <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Если даже одно слово не помещается, принудительно разбиваем
                # Для русских слов часто требуется больше места
                chars_per_part = max(3, len(word) // 2) # Минимум 3 буквы для русских слов
                
                # Более умное разбиение длинных слов на части
                i = 0
                while i < len(word):
                    part = word[i:i+chars_per_part]
                    test_part = font.render(part, True, (255, 255, 255))
                    
                    # Проверяем, что часть помещается
                    if test_part.get_width() <= max_width:
                        lines.append(part)
                        i += chars_per_part
                    else:
                        # Если даже часть не помещается, уменьшаем её
                        chars_per_part = max(1, chars_per_part - 1)
    
    if current_line:
        lines.append(current_line)
    
    return lines

def draw_adaptive_button(surface, rect: pygame.Rect, text: str, font, hover=False, active=False, 
                        style="default", transition_progress=1.0, click_effect=False, 
                        auto_size=True, text_wrap=True):
    """
    Улучшенная адаптивная отрисовка кнопок с автоматическим масштабированием текста и переносом строк.
    Автоматически подбирает оптимальный размер текста и размещение в зависимости от размера кнопки.
    """
    global responsive
    
    current_time = time.time()
    
    # Определяем доступное пространство для текста с учетом отступов
    if responsive:
        spacing = responsive.get_adaptive_spacing("button")
        text_padding_x = spacing['padding']
        text_padding_y = spacing['padding'] // 2
    else:
        text_padding_x = 15
        text_padding_y = 8
    
    text_area_width = rect.width - (text_padding_x * 2)
    text_area_height = rect.height - (text_padding_y * 2)
    
    # Автоматическое масштабирование текста
    if auto_size and responsive:
        # Используем новую систему адаптивного текста
        text_config = responsive.get_adaptive_text_size(
            text, text_area_width, text_area_height, font.get_height()
        )
        optimal_font_size = text_config['font_size']
        max_chars_per_line = text_config['max_chars_per_line']
        
        # Создаем оптимальный шрифт
        try:
            optimal_font = get_cached_font('arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace', 
                                         optimal_font_size, True)
        except:
            optimal_font = font
    else:
        optimal_font = font
        max_chars_per_line = text_area_width // (font.get_height() * 0.6)
    
    # Обработка переноса текста если включен
    if text_wrap and len(text) > max_chars_per_line:
        # Разбиваем текст на строки
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Слово слишком длинное, принудительно разбиваем
                    lines.append(word[:max_chars_per_line])
                    current_line = word[max_chars_per_line:] if len(word) > max_chars_per_line else ""
        
        if current_line:
            lines.append(current_line)
        
        # Ограничиваем количество строк
        max_lines = max(1, text_area_height // (optimal_font.get_height() + 2))
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            if lines:
                lines[-1] = lines[-1][:max(1, len(lines[-1]) - 3)] + "..."
    else:
        lines = [text]
    
    # Используем стандартную отрисовку кнопки (фон, тень, эффекты)
    draw_button(surface, rect, "", optimal_font, hover, active, style, transition_progress, click_effect)
    
    # Отрисовка адаптивного текста
    if lines:
        total_text_height = len(lines) * optimal_font.get_height() + (len(lines) - 1) * 2
        start_y = rect.y + (rect.height - total_text_height) // 2
        
        # Определяем цвет текста в зависимости от стиля
        if style == "primary":
            base_text_color = WHITE
        elif style == "success":
            base_text_color = WHITE
        elif style == "danger":
            base_text_color = WHITE
        elif active:
            base_text_color = BUTTON_TEXT_HOVER
        elif hover:
            pulse_intensity = pulse_effect(current_time, 1.0, 0.2)
            base_text_color = glow_color(BUTTON_TEXT_HOVER, 0.1 + pulse_intensity * 0.08, current_time)
        else:
            base_text_color = BUTTON_TEXT
        
        # Отрисовка каждой строки
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            line_surface = optimal_font.render(line, True, base_text_color)
            line_x = rect.x + (rect.width - line_surface.get_width()) // 2
            line_y = start_y + i * (optimal_font.get_height() + 2)
            
            # Тень для текста (для важных кнопок)
            if style in ["primary", "success", "danger"] or (hover and transition_progress > 0.3):
                shadow_surface = optimal_font.render(line, True, (0, 0, 0))
                shadow_offset = 1 + (1 if hover else 0)
                surface.blit(shadow_surface, (line_x + shadow_offset, line_y + shadow_offset))
            
            # Основной текст с микро-анимацией при клике
            if click_effect:
                text_shake_x = int(1 * pulse_effect(current_time * 12, 0.8))
                text_shake_y = int(1 * pulse_effect(current_time * 10, 0.6))
                surface.blit(line_surface, (line_x + text_shake_x, line_y + text_shake_y))
            else:
                surface.blit(line_surface, (line_x, line_y))


def draw_smart_text_block(surface, text: str, rect: pygame.Rect, base_font_size: int = 24, 
                         alignment="center", color=WHITE, auto_size=True, max_lines=None):
    """
    Рисует блок текста с автоматическим переносом и масштабированием.
    Идеально подходит для информационных панелей и описаний.
    """
    global responsive
    
    if not text.strip():
        return
    
    # Получаем адаптивные настройки текста
    if responsive and auto_size:
        text_config = responsive.get_adaptive_text_size(
            text, rect.width - 20, rect.height - 20, base_font_size
        )
        font_size = text_config['font_size']
        max_chars_per_line = text_config['max_chars_per_line']
        line_height = text_config['line_height']
    else:
        font_size = base_font_size
        line_height = int(base_font_size * 1.2)
        max_chars_per_line = max(1, (rect.width - 20) // (base_font_size * 0.6))
    
    # Создаем шрифт
    try:
        font = get_cached_font('arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace', font_size, False)
    except:
        try:
            font = pygame.font.SysFont('arial', font_size, False)
        except:
            font = pygame.font.Font(None, font_size)
    
    # Разбиваем текст на строки
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_surface = font.render(test_line, True, color)
        
        if test_surface.get_width() <= rect.width - 20:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Слово слишком длинное, принудительно разбиваем
                lines.append(word)
                current_line = ""
    
    if current_line:
        lines.append(current_line)
    
    # Ограничиваем количество строк если задано
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1][:max(1, len(lines[-1]) - 3)] + "..."
    
    # Вычисляем позицию для центрирования по вертикали
    total_height = len(lines) * line_height
    start_y = rect.y + (rect.height - total_height) // 2
    
    # Отрисовываем строки
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        line_surface = font.render(line, True, color)
        
        # Выравнивание по горизонтали
        if alignment == "center":
            line_x = rect.x + (rect.width - line_surface.get_width()) // 2
        elif alignment == "left":
            line_x = rect.x + 10
        elif alignment == "right":
            line_x = rect.x + rect.width - line_surface.get_width() - 10
        else:
            line_x = rect.x + 10
        
        line_y = start_y + i * line_height
        surface.blit(line_surface, (line_x, line_y))


def draw_enhanced_panel_with_content(surface, rect: pygame.Rect, title: str = "", content: str = "", 
                                   title_style="heading", animated=True):
    """
    Рисует улучшенную панель с заголовком и содержимым, автоматически адаптируясь под размер.
    """
    global responsive
    
    # Рисуем основную панель
    draw_enhanced_panel(surface, rect, animated)
    
    if not responsive:
        return
    
    # Получаем размеры для иерархии
    hierarchy = responsive.get_visual_hierarchy_sizes()
    spacing = responsive.get_adaptive_spacing("panel")
    
    current_y = rect.y + spacing['padding']
    available_width = rect.width - spacing['padding'] * 2
    
    # Отрисовка заголовка
    if title:
        title_height = hierarchy[title_style] + spacing['margin']
        title_rect = pygame.Rect(rect.x + spacing['padding'], current_y, 
                               available_width, title_height)
        
        try:
            title_font = get_cached_font('consolas,dejavusansmono,menlo,monospace', 
                                       hierarchy[title_style], True)
            title_surface = title_font.render(title, True, WHITE)
            title_x = title_rect.x + (title_rect.width - title_surface.get_width()) // 2
            surface.blit(title_surface, (title_x, title_rect.y))
        except:
            pass  # Пропускаем при ошибке
        
        current_y += title_height + spacing['spacing']
    
    # Отрисовка содержимого
    if content:
        content_height = rect.bottom - current_y - spacing['padding']
        content_rect = pygame.Rect(rect.x + spacing['padding'], current_y, 
                                 available_width, content_height)
        
        draw_smart_text_block(surface, content, content_rect, 
                            hierarchy['body'], "left", WHITE)


def create_adaptive_layout_manager():
    """
    Создает менеджер адаптивной компоновки для упрощения работы с UI.
    """
    global responsive
    
    if not responsive:
        return None
    
    class AdaptiveLayoutManager:
        def __init__(self, responsive_system):
            self.responsive = responsive_system
            self.elements = []
        
        def add_button(self, text, position_type="center", style="default", 
                      min_width=None, min_height=None):
            """Добавляет кнопку с автоматическими размерами"""
            if min_width is None or min_height is None:
                min_width, min_height = self.responsive.get_smart_button_dimensions(text)
            
            return {
                'type': 'button',
                'text': text,
                'width': min_width,
                'height': min_height,
                'position_type': position_type,
                'style': style
            }
        
        def add_text_block(self, text, position_type="center", width_ratio=0.8, height_ratio=0.3):
            """Добавляет блок текста с автоматическим размером"""
            return {
                'type': 'text_block',
                'text': text,
                'width_ratio': width_ratio,
                'height_ratio': height_ratio,
                'position_type': position_type
            }
        
        def layout_in_container(self, container_rect):
            """Размещает все элементы в контейнере с оптимальной компоновкой"""
            if not self.elements:
                return []
            
            # Для простоты сейчас размещаем элементы вертикально
            spacing = self.responsive.get_adaptive_spacing("menu_item")['spacing']
            total_height = sum(elem.get('height', container_rect.height * elem.get('height_ratio', 0.1)) 
                             for elem in self.elements)
            total_spacing = spacing * max(0, len(self.elements) - 1)
            
            start_y = container_rect.y + (container_rect.height - total_height - total_spacing) // 2
            current_y = start_y
            
            positioned_elements = []
            
            for element in self.elements:
                if element['type'] == 'button':
                    width = element['width']
                    height = element['height']
                elif element['type'] == 'text_block':
                    width = int(container_rect.width * element['width_ratio'])
                    height = int(container_rect.height * element['height_ratio'])
                else:
                    continue
                
                x, y = self.responsive.get_smart_positioning(
                    width, height, container_rect.width, container_rect.height, 
                    element['position_type']
                )
                
                # Корректируем Y-координату для последовательного размещения
                y = current_y
                x = container_rect.x + (container_rect.width - width) // 2  # Центрируем по X
                
                positioned_elements.append({
                    **element,
                    'rect': pygame.Rect(x, y, width, height)
                })
                
                current_y += height + spacing
            
            return positioned_elements
    
    return AdaptiveLayoutManager(responsive)

def draw_button(surface, rect: pygame.Rect, text: str, font, hover=False, active=False, 
               style="default", transition_progress=1.0, click_effect=False):
    """
    Расширенная функция отрисовки кнопок с продвинутыми эффектами и анимацией.
    """
    current_time = time.time()
    
    # Прогрессивный эффект клика с микро-анимацией
    click_intensity = 0.3 if click_effect else 0.0
    click_offset = int(3 * click_intensity * pulse_effect(current_time * 8, 0.8))
    display_rect = rect.copy()
    display_rect.x += click_offset
    display_rect.y += click_offset
    
    # Динамическая тень с адаптивной интенсивностью
    if not active:
        hover_boost = smooth_lerp(0.0, 1.2, transition_progress) if hover else 0.0
        click_boost = click_intensity * 0.8
        shadow_intensity = 1.0 + hover_boost + click_boost
        shadow_layers = max(2, min(6, int(3 * shadow_intensity)))
        
        for i in range(shadow_layers):
            layer_factor = (i + 1) / shadow_layers
            shadow_offset_x = 2 + i * (1.2 if hover else 0.6) + click_offset * 0.5
            shadow_offset_y = 2 + i * (1.2 if hover else 0.6) + click_offset * 0.5
            shadow_alpha = int((50 - i * 7) * shadow_intensity * (1 - layer_factor * 0.3))
            
            shadow_rect = display_rect.copy()
            shadow_rect.x += int(shadow_offset_x)
            shadow_rect.y += int(shadow_offset_y)
            
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_surf.fill((*PANEL_SHADOW, max(10, shadow_alpha)))
            surface.blit(shadow_surf, shadow_rect.topleft)
    
    # Максимально оптимизированные цвета с продвинутыми эффектами
    hover_multiplier = smooth_lerp(0.0, 1.0, transition_progress) if hover else 0.0
    pulse_intensity = pulse_effect(current_time, 1.0, 0.2) if hover else 0.0
    
    if style == "primary":
        if active:
            bg_top, bg_bottom = (45, 110, 180), (35, 90, 160)
            border_color = (60, 130, 200)
            text_color = WHITE
        elif hover:
            # Прогрессивный переход с пульсацией
            base_top, base_bottom = (64, 146, 245), (44, 126, 225)
            hover_top, hover_bottom = (104, 186, 255), (84, 166, 255)
            click_boost = click_intensity * 20
            
            bg_top = tuple(min(255, int(smooth_lerp(base_top[i], hover_top[i], hover_multiplier) + 
                                      pulse_intensity * 15 + click_boost)) for i in range(3))
            bg_bottom = tuple(min(255, int(smooth_lerp(base_bottom[i], hover_bottom[i], hover_multiplier) + 
                                         pulse_intensity * 12 + click_boost)) for i in range(3))
            border_color = glow_color((120, 200, 255), 0.4 + pulse_intensity * 0.2, current_time)
            text_color = glow_color(WHITE, 0.15 + pulse_intensity * 0.1, current_time)
        else:
            bg_top, bg_bottom = (64, 146, 245), (44, 126, 225)
            border_color = (80, 160, 240)
            text_color = WHITE
            
    elif style == "success":
        if active:
            bg_top, bg_bottom = (30, 150, 90), (25, 130, 75)
            border_color = (45, 170, 105)
            text_color = WHITE
        elif hover:
            base_top, base_bottom = (40, 200, 120), (30, 180, 100)
            hover_top, hover_bottom = (80, 240, 160), (70, 220, 140)
            click_boost = click_intensity * 25
            
            bg_top = tuple(min(255, int(smooth_lerp(base_top[i], hover_top[i], hover_multiplier) + 
                                      pulse_intensity * 20 + click_boost)) for i in range(3))
            bg_bottom = tuple(min(255, int(smooth_lerp(base_bottom[i], hover_bottom[i], hover_multiplier) + 
                                         pulse_intensity * 15 + click_boost)) for i in range(3))
            border_color = glow_color((80, 255, 160), 0.5 + pulse_intensity * 0.3, current_time)
            text_color = glow_color(WHITE, 0.2 + pulse_intensity * 0.15, current_time)
        else:
            bg_top, bg_bottom = (40, 200, 120), (30, 180, 100)
            border_color = (55, 215, 135)
            text_color = WHITE
            
    elif style == "danger":
        if active:
            bg_top, bg_bottom = (180, 40, 50), (160, 30, 40)
            border_color = (200, 55, 65)
            text_color = WHITE
        elif hover:
            base_top, base_bottom = (220, 53, 69), (200, 43, 59)
            hover_top, hover_bottom = (255, 93, 109), (235, 73, 89)
            click_boost = click_intensity * 20
            
            bg_top = tuple(min(255, int(smooth_lerp(base_top[i], hover_top[i], hover_multiplier) + 
                                      pulse_intensity * 18 + click_boost)) for i in range(3))
            bg_bottom = tuple(min(255, int(smooth_lerp(base_bottom[i], hover_bottom[i], hover_multiplier) + 
                                         pulse_intensity * 15 + click_boost)) for i in range(3))
            border_color = glow_color((255, 108, 124), 0.3 + pulse_intensity * 0.2, current_time)
            text_color = glow_color(WHITE, 0.1 + pulse_intensity * 0.1, current_time)
        else:
            bg_top, bg_bottom = (220, 53, 69), (200, 43, 59)
            border_color = (235, 68, 84)
            text_color = WHITE
            
    else:  # default - максимально оптимизированные базовые кнопки
        if active:
            bg_top, bg_bottom = BUTTON_BG_ACTIVE, tuple(max(0, c - 12) for c in BUTTON_BG_ACTIVE)
            border_color = BUTTON_BORDER_HOVER
            text_color = BUTTON_TEXT_HOVER
        elif hover:
            base_top, base_bottom = BUTTON_BG, tuple(max(0, c - 5) for c in BUTTON_BG)
            hover_top, hover_bottom = BUTTON_BG_HOVER, tuple(max(0, c - 10) for c in BUTTON_BG_HOVER)
            click_boost = click_intensity * 15
            
            bg_top = tuple(min(255, int(smooth_lerp(base_top[i], hover_top[i], hover_multiplier) + 
                                      pulse_intensity * 12 + click_boost)) for i in range(3))
            bg_bottom = tuple(min(255, int(smooth_lerp(base_bottom[i], hover_bottom[i], hover_multiplier) + 
                                         pulse_intensity * 8 + click_boost)) for i in range(3))
            border_color = glow_color(BUTTON_BORDER_HOVER, 0.2 + pulse_intensity * 0.15, current_time)
            text_color = glow_color(BUTTON_TEXT_HOVER, 0.1 + pulse_intensity * 0.08, current_time)
        else:
            bg_top, bg_bottom = BUTTON_BG, tuple(max(0, c - 5) for c in BUTTON_BG)
            border_color = BUTTON_BORDER
            text_color = BUTTON_TEXT
    
    # Продвинутый градиентный фон с анимацией
    draw_gradient_rect(surface, display_rect, bg_top, bg_bottom, animated=hover or click_effect)
    
    # Динамическая анимированная рамка
    border_pulse = pulse_effect(current_time * 1.5, 0.5) if hover else 0.0
    border_width = 2 + int(hover_multiplier * 2) + int(border_pulse)
    border_width += int(click_intensity * 2)  # Клик-эффект для рамки
    pygame.draw.rect(surface, border_color, display_rect, border_width, border_radius=8)
    
    # Многослойная внутренняя подсветка
    if hover and not active:
        # Основная подсветка
        inner_rect = display_rect.copy()
        inner_rect.inflate(-6, -6)
        highlight_alpha = int(35 * hover_multiplier + pulse_intensity * 15)
        highlight_color = tuple(min(255, c + 25 + int(pulse_intensity * 10)) for c in bg_top)
        
        highlight_surf = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
        highlight_surf.fill((*highlight_color, highlight_alpha))
        surface.blit(highlight_surf, inner_rect.topleft)
        
        # Дополнительная рамка подсветки
        inner_border_alpha = int(80 * hover_multiplier)
        inner_border_color = (*highlight_color, inner_border_alpha)
        pygame.draw.rect(surface, inner_border_color, inner_rect, 1, border_radius=6)
        
        # Центральный яркий отблеск
        if pulse_intensity > 0.1:
            center_rect = display_rect.copy()
            center_rect.inflate(-12, -12)
            center_alpha = int(20 * pulse_intensity)
            center_color = tuple(min(255, c + 40) for c in bg_top)
            center_surf = pygame.Surface((center_rect.width, center_rect.height), pygame.SRCALPHA)
            center_surf.fill((*center_color, center_alpha))
            surface.blit(center_surf, center_rect.topleft)
    
    # Продвинутое пульсирующее свечение
    if style in ["primary", "success", "danger"] and (hover or click_effect):
        glow_rect = display_rect.copy()
        glow_rect.inflate(8, 8)
        
        # Многослойное свечение
        for layer in range(3):
            layer_rect = glow_rect.copy()
            layer_rect.inflate(layer * 2, layer * 2)
            
            base_intensity = pulse_effect(current_time + layer * 0.1, 1.2) if hover else 0.5
            click_glow = click_intensity * 0.8
            glow_alpha = int((20 - layer * 5) * (base_intensity + click_glow) * hover_multiplier)
            
            if glow_alpha > 5:
                glow_surf = pygame.Surface((layer_rect.width, layer_rect.height), pygame.SRCALPHA)
                glow_surf.fill((*border_color, glow_alpha))
                surface.blit(glow_surf, layer_rect.topleft)
    
    # Адаптивный рендеринг текста с автоматическим масштабированием
    if hover and style in ["primary", "success", "danger"]:
        text_glow_intensity = pulse_intensity * 0.15
        text_color = glow_color(text_color, text_glow_intensity, current_time)
    
    # Используем адаптивный шрифт меню для лучшего помещения текста
    adaptive_font = get_menu_button_font(text, font, display_rect.width - 20, display_rect.height - 10)
    txt = adaptive_font.render(text, True, text_color)
    text_x = display_rect.x + (display_rect.w - txt.get_width()) // 2
    text_y = display_rect.y + (display_rect.h - txt.get_height()) // 2
    
    # Продвинутая тень текста с анимацией
    if style in ["primary", "success", "danger"] or (hover and transition_progress > 0.3):
        shadow_txt = adaptive_font.render(text, True, (0, 0, 0))
        shadow_offset_x = 1 + int(0.8 * hover_multiplier) + int(click_intensity)
        shadow_offset_y = 1 + int(0.8 * hover_multiplier) + int(click_intensity)
        
        # Множественная тень для глубины
        for i in range(2 if hover else 1):
            offset_mult = i + 1
            shadow_alpha = 180 - i * 60
            shadow_color = (0, 0, 0, shadow_alpha) if i == 0 else (0, 0, 0, shadow_alpha)
            shadow_surface = adaptive_font.render(text, True, shadow_color[:3])
            surface.blit(shadow_surface, 
                        (text_x + shadow_offset_x * offset_mult, text_y + shadow_offset_y * offset_mult))
    
    # Основной текст с микро-анимацией при клике
    if click_effect:
        # Микро-смещение текста при клике
        text_shake_x = int(1 * pulse_effect(current_time * 12, 0.8))
        text_shake_y = int(1 * pulse_effect(current_time * 10, 0.6))
        surface.blit(txt, (text_x + text_shake_x, text_y + text_shake_y))
    else:
        surface.blit(txt, (text_x, text_y))

def mode_selection_menu(screen, clock, font, small, audio: AudioManager):
    """Меню выбора игрового режима"""
    selected_mode = 0
    modes = list(GameMode)
    mode_rects = []  # Будем хранить прямоугольники для режимов
    
    while True:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    selected_mode = (selected_mode - 1) % len(modes)
                elif ev.key == pygame.K_DOWN:
                    selected_mode = (selected_mode + 1) % len(modes)
                elif ev.key == pygame.K_RETURN:
                    return modes[selected_mode]
                elif ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:  # Левая кнопка мыши
                    mouse_clicked = True
        
        # Улучшенная отрисовка с плавными эффектами и адаптивными размерами
        # Анимированный фон
        screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        current_time = time.time()
        animated_bg_top = glow_color(BG_GRADIENT_TOP, 0.1, current_time)
        animated_bg_bottom = glow_color(BG_GRADIENT_BOTTOM, 0.05, current_time + 1)
        draw_gradient_rect(screen, screen_rect, animated_bg_top, animated_bg_bottom)
        
        # Плавающие декоративные элементы (меньше и аккуратнее)
        decoration_count = max(4, responsive.scale_size(6)) if responsive else 6
        for i in range(decoration_count):
            wave_x = wave_effect(i * 0.7, 0.3, responsive.scale_size(20) if responsive else 20)
            wave_y = wave_effect(i * 0.5 + 1, 0.2, responsive.scale_size(12) if responsive else 12)
            x = i * (WIDTH // decoration_count) + responsive.scale_size(60) if responsive else i * (WIDTH // 6) + 60
            y = HEIGHT // 5 + (i % 2) * responsive.scale_size(120) if responsive else HEIGHT // 5 + (i % 2) * 120
            x += wave_x
            y += wave_y
            size = responsive.scale_size(16 + (i % 3) * 6) if responsive else 16 + (i % 3) * 6
            alpha = int(25 + 20 * pulse_effect(i * 0.3, 0.8))
            decoration = pygame.Surface((size, size), pygame.SRCALPHA)
            decoration.fill((*ACCENT_PRIMARY, alpha))
            screen.blit(decoration, (x, y))
        
        # Адаптивная главная панель
        panel_width = responsive.get_panel_width(800) if responsive else 800
        main_panel = responsive.get_rect(WIDTH // 2 - panel_width // 2, 50, panel_width, HEIGHT - 100) if responsive else pygame.Rect(WIDTH // 2 - 400, 50, 800, HEIGHT - 100)
        float_offset = wave_effect(current_time, 0.4, 2)
        main_panel.y += int(float_offset)
        draw_enhanced_panel(screen, main_panel, animated=True)
        
        # Адаптивный анимированный заголовок
        title_width = int(panel_width * 0.9)
        title_height = responsive.scale_height(50) if responsive else 50
        title_rect = responsive.get_rect(WIDTH // 2 - title_width // 2, 70 + int(float_offset), title_width, title_height) if responsive else pygame.Rect(WIDTH // 2 - 350, 70 + int(float_offset), 700, 50)
        title_glow = pulse_effect(0, 0.7, 0.3)
        title_top = glow_color(ACCENT_PRIMARY, title_glow, 0)
        title_bottom = glow_color(ACCENT_SECONDARY, title_glow, 0.5)
        draw_gradient_rect(screen, title_rect, title_top, title_bottom, vertical=False, animated=True)
        pygame.draw.rect(screen, glow_color((120, 140, 170), 0.4, current_time), title_rect, 2, border_radius=12)
        
        # Адаптивный шрифт для заголовка
        title_font_size = responsive.scale_font(48) if responsive else 48
        title_font = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', title_font_size, bold=True)
        title = title_font.render('Выберите режим игры', True, WHITE)
        title_shadow = title_font.render('Выберите режим игры', True, (0, 0, 0))
        title_x = WIDTH // 2 - title.get_width() // 2
        title_y = title_rect.y + (title_rect.height - title.get_height()) // 2
        text_wave = wave_effect(current_time, 1.0, 1)
        screen.blit(title_shadow, (title_x + 2 + int(text_wave), title_y + 2))
        screen.blit(title, (title_x + int(text_wave), title_y))
        
        # Опции режимов с улучшенным размещением
        y_start = 150
        mode_rects = []  # Обновляем список прямоугольников
        
        for i, mode in enumerate(modes):
            config = GAME_MODE_CONFIGS[mode]
            is_selected = i == selected_mode
            
            # Панель режима с лучшим размещением
            mode_rect = pygame.Rect(WIDTH // 2 - 370, y_start + i * 110, 740, 90)
            mode_rects.append(mode_rect)
            
        # Проверка наведения мыши
            is_hovered = mode_rect.collidepoint(mouse_pos)
            if is_hovered:
                selected_mode = i  # Автоматически выбираем при наведении
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)  # Меняем курсор
                if mouse_clicked:
                    return modes[selected_mode]  # Клик для выбора
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)  # Обычный курсор
            
            if is_selected or is_hovered:
                # Анимация выделения
                glow_rect = mode_rect.copy()
                glow_rect.inflate(8, 8)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                glow_alpha = 120 if is_selected else 80
                glow_surf.fill((*ACCENT_PRIMARY, glow_alpha))
                screen.blit(glow_surf, glow_rect.topleft)
                
                # Яркий фон для выбранного/наведенного
                bg_intensity = (50, 60, 75) if is_selected else (45, 55, 70)
                draw_gradient_rect(screen, mode_rect, bg_intensity, tuple(max(0, c - 10) for c in bg_intensity))
                border_color = ACCENT_PRIMARY if is_selected else (100, 120, 150)
                pygame.draw.rect(screen, border_color, mode_rect, 3, border_radius=12)
            else:
                # Обычный фон
                draw_gradient_rect(screen, mode_rect, (35, 42, 52), (25, 32, 42))
                pygame.draw.rect(screen, (60, 70, 85), mode_rect, 2, border_radius=12)
            
            # Название режима с адаптивным шрифтом
            mode_color = WHITE if (is_selected or is_hovered) else (200, 210, 220)
            # Используем специальную функцию для кнопок меню
            mode_font = get_menu_button_font(config.name, font, mode_rect.width - 40, 40)
            mode_text = mode_font.render(config.name, True, mode_color)
            mode_x = mode_rect.x + 20
            mode_y = mode_rect.y + 15
            
            if is_selected or is_hovered:
                mode_shadow = mode_font.render(config.name, True, (0, 0, 0))
                screen.blit(mode_shadow, (mode_x + 1, mode_y + 1))
            
            screen.blit(mode_text, (mode_x, mode_y))
            
            # Описание режима с адаптивным шрифтом
            desc_color = (180, 190, 200) if (is_selected or is_hovered) else (140, 150, 160)
            desc_font = get_menu_button_font(config.description, small, mode_rect.width - 40, 25)
            desc_text = desc_font.render(config.description, True, desc_color)
            screen.blit(desc_text, (mode_x, mode_y + 40))
            
            # Дополнительная информация с адаптивным шрифтом
            if mode == GameMode.CAMPAIGN:
                info_text = 'Последовательное прохождение уровней'
                info_color = ACCENT_WARNING
            elif mode == GameMode.ENDLESS_IMMERSIVE:
                info_text = 'Увеличивающаяся сложность, высокие очки'
                info_color = ACCENT_DANGER
            else:  # ENDLESS_RELAXED
                info_text = 'Медленный темп, ограниченная скорость'
                info_color = ACCENT_SUCCESS
            
            info_font = get_menu_button_font(info_text, small, mode_rect.width - 40, 20)
            info_surf = info_font.render(info_text, True, info_color)
            screen.blit(info_surf, (mode_x, mode_y + 65))
            
            # Иконка режима
            icon_rect = pygame.Rect(mode_rect.right - 60, mode_rect.y + 20, 40, 40)
            if mode == GameMode.CAMPAIGN:
                icon_color = ACCENT_WARNING
            elif mode == GameMode.ENDLESS_IMMERSIVE:
                icon_color = ACCENT_DANGER
            else:
                icon_color = ACCENT_SUCCESS
            
            pygame.draw.circle(screen, icon_color, icon_rect.center, 20)
            pygame.draw.circle(screen, WHITE, icon_rect.center, 20, 2)
        
        # Кнопка настроек разрешения в правом нижнем углу
        resolution_btn_width = 200
        resolution_btn_height = 45
        resolution_btn_x = WIDTH - resolution_btn_width - 20
        resolution_btn_y = HEIGHT - resolution_btn_height - 20
        resolution_btn_rect = pygame.Rect(resolution_btn_x, resolution_btn_y, resolution_btn_width, resolution_btn_height)
        
        resolution_hover = resolution_btn_rect.collidepoint(mouse_pos)
        if resolution_hover:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            if mouse_clicked:
                # Открываем меню выбора разрешения
                try:
                    selected_resolution = resolution_selection_menu()
                    if selected_resolution:
                        # Применяем новое разрешение немедленно
                        new_screen = apply_resolution_change(screen, selected_resolution)
                        if new_screen:
                            screen = new_screen  # Обновляем экран
                            
                            # Пересоздаем шрифты с новыми размерами
                            font_size = responsive.scale_font(48) if responsive else 48
                            small_size = responsive.scale_font(20) if responsive else 20
                            font = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', font_size, bold=True)
                            small = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', small_size)
                            
                            print(f"[Меню] Разрешение успешно изменено на: {selected_resolution[0]}x{selected_resolution[1]}")
                except Exception as e:
                    print(f"[Ошибка] Не удалось открыть меню разрешения: {e}")
        
        # Отрисовка кнопки разрешения
        resolution_style = "default" if not resolution_hover else "primary"
        draw_button(screen, resolution_btn_rect, "Настройки экрана", small, hover=resolution_hover, style=resolution_style)
        
        # Инструкции с лучшим размещением
        controls_rect = pygame.Rect(WIDTH // 2 - 350, HEIGHT - 60, 700, 35)
        draw_gradient_rect(screen, controls_rect, (25, 30, 38), (20, 25, 33))
        pygame.draw.rect(screen, (50, 60, 75), controls_rect, 1, border_radius=8)
        
        controls_text = small.render('↑↓/Клик - выбор, Enter/Клик - подтвердить, Esc - выход', True, WHITE)
        controls_x = WIDTH // 2 - controls_text.get_width() // 2
        screen.blit(controls_text, (controls_x, HEIGHT - 50))
        
        pygame.display.flip()

def campaign_level_selection_menu(screen, clock, font, small, audio: AudioManager):
    """Меню выбора уровня кампании"""
    selected_level = 0
    available_levels = [level for level in CAMPAIGN_LEVELS if level.unlocked]
    
    if not available_levels:
        available_levels = [CAMPAIGN_LEVELS[0]]  # Первый уровень всегда доступен
    
    while True:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    selected_level = (selected_level - 1) % len(available_levels)
                elif ev.key == pygame.K_DOWN:
                    selected_level = (selected_level + 1) % len(available_levels)
                elif ev.key == pygame.K_RETURN:
                    return available_levels[selected_level].level_num
                elif ev.key == pygame.K_ESCAPE:
                    return None  # Возврат к выбору режима
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:  # Левая кнопка мыши
                    mouse_clicked = True
        
        # Отрисовка с улучшенным фоном
        draw_enhanced_background(screen)
        
        # Главная панель
        main_panel = pygame.Rect(WIDTH // 2 - 450, 40, 900, HEIGHT - 80)
        draw_enhanced_panel(screen, main_panel, animated=True)
        
        # Заголовок
        title_rect = pygame.Rect(WIDTH // 2 - 400, 60, 800, 60)
        draw_gradient_rect(screen, title_rect, ACCENT_WARNING, ACCENT_PRIMARY, vertical=False)
        pygame.draw.rect(screen, (150, 120, 80), title_rect, 2, border_radius=12)
        
        title = font.render('КАМПАНИЯ - Выберите уровень', True, WHITE)
        title_shadow = font.render('КАМПАНИЯ - Выберите уровень', True, (0, 0, 0))
        title_x = WIDTH // 2 - title.get_width() // 2
        screen.blit(title_shadow, (title_x + 2, 82))
        screen.blit(title, (title_x, 80))
        
        # Уровни с лучшим размещением
        y_start = 160
        for i, level in enumerate(available_levels):
            is_selected = i == selected_level
            
            # Панель уровня
            level_rect = pygame.Rect(WIDTH // 2 - 420, y_start + i * 130, 840, 110)
            
        # Проверка наведения мыши
            is_hovered = level_rect.collidepoint(mouse_pos)
            if is_hovered:
                selected_level = i  # Автоматически выбираем при наведении
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)  # Меняем курсор
                if mouse_clicked:
                    return available_levels[selected_level].level_num  # Клик для выбора
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)  # Обычный курсор
            
            if is_selected or is_hovered:
                # Яркий фон для выбранного/наведенного
                bg_intensity = (50, 65, 80) if is_selected else (45, 60, 75)
                draw_gradient_rect(screen, level_rect, bg_intensity, tuple(max(0, c - 10) for c in bg_intensity))
                border_color = ACCENT_WARNING if is_selected else (150, 120, 80)
                pygame.draw.rect(screen, border_color, level_rect, 3, border_radius=12)
                
                # Эффект свечения
                glow_rect = level_rect.copy()
                glow_rect.inflate(6, 6)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                glow_alpha = 80 if is_selected else 50
                glow_surf.fill((*ACCENT_WARNING, glow_alpha))
                screen.blit(glow_surf, glow_rect.topleft)
            else:
                # Обычный фон
                draw_gradient_rect(screen, level_rect, (35, 45, 60), (25, 35, 50))
                pygame.draw.rect(screen, (70, 85, 100), level_rect, 2, border_radius=12)
            
            # Название уровня с адаптивным шрифтом
            color = WHITE if (is_selected or is_hovered) else (200, 210, 220)
            level_title_text = f"Уровень {level.level_num}: {level.name}"
            level_font = get_menu_button_font(level_title_text, font, level_rect.width - 120, 40)
            level_text = level_font.render(level_title_text, True, color)
            level_x = level_rect.x + 25
            level_y = level_rect.y + 15
            
            if is_selected or is_hovered:
                level_shadow = level_font.render(level_title_text, True, (0, 0, 0))
                screen.blit(level_shadow, (level_x + 2, level_y + 2))
            
            screen.blit(level_text, (level_x, level_y))
            
            # Описание с адаптивным шрифтом
            desc_color = (180, 190, 200) if (is_selected or is_hovered) else (140, 150, 160)
            desc_font = get_menu_button_font(level.description, small, level_rect.width - 120, 25)
            desc_text = desc_font.render(level.description, True, desc_color)
            screen.blit(desc_text, (level_x, level_y + 45))
            
            # Цели с адаптивным шрифтом
            objectives_text_str = ' | '.join([obj.description for obj in level.objectives])
            objectives_font = get_menu_button_font(objectives_text_str, small, level_rect.width - 120, 20)
            objectives_text = objectives_font.render(objectives_text_str, True, ACCENT_WARNING)
            screen.blit(objectives_text, (level_x, level_y + 70))
            
            # Иконка статуса
            status_icon_rect = pygame.Rect(level_rect.right - 60, level_rect.y + 30, 40, 40)
            if level.completed:
                pygame.draw.circle(screen, ACCENT_SUCCESS, status_icon_rect.center, 20)
                pygame.draw.circle(screen, WHITE, status_icon_rect.center, 20, 2)
                # Галочка
                checkmark = small.render('✓', True, WHITE)
                check_x = status_icon_rect.centerx - checkmark.get_width() // 2
                check_y = status_icon_rect.centery - checkmark.get_height() // 2
                screen.blit(checkmark, (check_x, check_y))
            else:
                pygame.draw.circle(screen, ACCENT_WARNING, status_icon_rect.center, 20)
                pygame.draw.circle(screen, WHITE, status_icon_rect.center, 20, 2)
        
        # Инструкции внизу
        controls_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT - 60, 600, 35)
        draw_gradient_rect(screen, controls_rect, (25, 30, 38), (20, 25, 33))
        pygame.draw.rect(screen, (50, 60, 75), controls_rect, 1, border_radius=8)
        
        controls_text = small.render('↑↓/Клик - выбор, Enter/Клик - начать, Esc - назад', True, WHITE)
        controls_x = WIDTH // 2 - controls_text.get_width() // 2
        screen.blit(controls_text, (controls_x, HEIGHT - 50))
        
        pygame.display.flip()

def start_menu(screen, clock, font, small, audio: AudioManager):
    selected_level = 1
    music_index = audio.index if audio.enabled else -1
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q:
                    pygame.quit(); sys.exit(0)
                if ev.key == pygame.K_RETURN:
                    return selected_level, music_index
                if ev.key == pygame.K_RIGHT:
                    selected_level = min(10, selected_level + 1)
                if ev.key == pygame.K_LEFT:
                    selected_level = max(1, selected_level - 1)
                if ev.key == pygame.K_DOWN:
                    if audio.enabled:
                        music_index = (music_index + 1) % len(audio.playlist)
                        # Проигрываем выбранный трек
                        if music_index >= 0:
                            audio.index = music_index
                            audio.play_current()
                if ev.key == pygame.K_UP:
                    if audio.enabled:
                        music_index = (music_index - 1) % len(audio.playlist)
                        # Проигрываем выбранный трек
                        if music_index >= 0:
                            audio.index = music_index
                            audio.play_current()
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:  # Левая кнопка мыши
                    mouse_clicked = True
            elif ev.type == pygame.MOUSEWHEEL:
                # Колесо мыши для смены уровня
                if ev.y > 0:  # Прокрутка вверх
                    selected_level = min(10, selected_level + 1)
                elif ev.y < 0:  # Прокрутка вниз
                    selected_level = max(1, selected_level - 1)
        # Улучшенный фон и современный UI
        draw_enhanced_background(screen)
        
        # Адаптивные размеры с безопасностью
        panel_width = responsive.get_panel_width(800) if responsive else 800
        main_panel = responsive.get_rect(WIDTH // 2 - panel_width // 2, 50, panel_width, HEIGHT - 100) if responsive else pygame.Rect(WIDTH // 2 - 400, 50, 800, HEIGHT - 100)
        draw_enhanced_panel(screen, main_panel, animated=True)
        
        # Секция заголовка с адаптивным градиентом
        title_width = int(panel_width * 0.75)
        title_height = responsive.scale_height(70) if responsive else 70
        title_rect = responsive.get_rect(WIDTH // 2 - title_width // 2, 80, title_width, title_height) if responsive else pygame.Rect(WIDTH // 2 - 300, 80, 600, 70)
        draw_gradient_rect(screen, title_rect, ACCENT_PRIMARY, ACCENT_SECONDARY, vertical=False)
        pygame.draw.rect(screen, (120, 140, 170), title_rect, 2, border_radius=12)
        
        # Адаптивный заголовок
        title_font_size = responsive.scale_font(48) if responsive else 48
        title_font = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', title_font_size, bold=True)
        title = title_font.render('TETRIS ENHANCED', True, WHITE)
        title_shadow = title_font.render('TETRIS ENHANCED', True, (0, 0, 0))
        title_x = WIDTH // 2 - title.get_width() // 2
        title_y = title_rect.y + (title_rect.height - title.get_height()) // 2 + 2
        screen.blit(title_shadow, (title_x + 2, title_y + 2))
        screen.blit(title, (title_x, title_y))
        
        # Адаптивная информационная секция
        info_width = int(panel_width * 0.875)
        info_height = responsive.scale_height(45) if responsive else 45
        info_y = title_rect.bottom + responsive.get_margin(20) if responsive else title_rect.bottom + 20
        info_rect = responsive.get_rect(WIDTH // 2 - info_width // 2, info_y, info_width, info_height) if responsive else pygame.Rect(WIDTH // 2 - 350, 170, 700, 45)
        draw_gradient_rect(screen, info_rect, (35, 42, 52), (25, 32, 42))
        pygame.draw.rect(screen, (60, 70, 85), info_rect, 1, border_radius=8)
        
        # Адаптивный текст информации с фалбэком
        info_text = 'Выберите уровень (← → / Мышь) и музыку (↑ ↓ / Мышь). Enter = Старт'
        try:
            info_font = get_adaptive_font(info_text, small, info_rect.width - 20, info_rect.height - 10) if responsive else small
        except Exception:
            info_font = small  # Фалбэк на стандартный шрифт
        info = info_font.render(info_text, True, WHITE)
        info_x = WIDTH // 2 - info.get_width() // 2
        screen.blit(info, (info_x, info_rect.y + (info_rect.height - info.get_height()) // 2))
        
        # Адаптивная секция выбора уровня
        level_section_y = info_rect.bottom + responsive.get_margin(20) if responsive else info_rect.bottom + 25
        level_section_width = int(panel_width * 0.875)
        level_section_height = responsive.scale_height(120) if responsive else 120
        level_section_rect = responsive.get_rect(WIDTH // 2 - level_section_width // 2, level_section_y, level_section_width, level_section_height) if responsive else pygame.Rect(WIDTH // 2 - 350, 240, 700, 120)
        draw_gradient_rect(screen, level_section_rect, (30, 40, 55), (25, 35, 50))
        pygame.draw.rect(screen, (70, 85, 100), level_section_rect, 2, border_radius=12)
        
        # Заголовок секции уровня
        level_title = small.render('НАЧАЛЬНЫЙ УРОВЕНЬ', True, ACCENT_SUCCESS)
        level_title_x = WIDTH // 2 - level_title.get_width() // 2
        screen.blit(level_title, (level_title_x, 255))
        
        # Блок выбора уровня с увеличенными кнопками
        level_rect = pygame.Rect(WIDTH // 2 - 150, 285, 300, 70)  # Увеличиваем с 240х60 до 300х70
        level_left_btn = pygame.Rect(level_rect.x - 80, level_rect.y + 10, 60, 50)  # Увеличиваем с 40х40 до 60х50
        level_right_btn = pygame.Rect(level_rect.right + 20, level_rect.y + 10, 60, 50)  # Увеличиваем с 40х40 до 60х50
        
        # Обработка мыши для уровня
        level_hover = level_rect.collidepoint(mouse_pos)
        left_hover = level_left_btn.collidepoint(mouse_pos)
        right_hover = level_right_btn.collidepoint(mouse_pos)
        
        if mouse_clicked:
            if left_hover:
                selected_level = max(1, selected_level - 1)
            elif right_hover:
                selected_level = min(10, selected_level + 1)
        
        # Рисуем кнопки уровня
        left_color = (100, 180, 120) if left_hover else (80, 150, 100)
        right_color = (100, 180, 120) if right_hover else (80, 150, 100)
        
        pygame.draw.rect(screen, left_color, level_left_btn, border_radius=5)
        pygame.draw.rect(screen, right_color, level_right_btn, border_radius=5)
        
        # Стрелки на кнопках с безопасным адаптивным шрифтом
        try:
            level_arrow_font = get_adaptive_font('<', small, level_left_btn.width - 4, level_left_btn.height - 4) if responsive else small
        except Exception:
            level_arrow_font = small
        left_arrow = level_arrow_font.render('<', True, WHITE)
        right_arrow = level_arrow_font.render('>', True, WHITE)
        screen.blit(left_arrow, (level_left_btn.centerx - left_arrow.get_width() // 2, level_left_btn.centery - left_arrow.get_height() // 2))
        screen.blit(right_arrow, (level_right_btn.centerx - right_arrow.get_width() // 2, level_right_btn.centery - right_arrow.get_height() // 2))
        
        # Улучшенный фон для уровня
        level_bg_color = tuple(min(255, c + 20) for c in ACCENT_SUCCESS) if level_hover else ACCENT_SUCCESS
        draw_gradient_rect(screen, level_rect, level_bg_color, tuple(max(0, c - 30) for c in level_bg_color))
        pygame.draw.rect(screen, (80, 150, 100), level_rect, 3, border_radius=10)
        
        lvl_txt = font.render(f'УРОВЕНЬ {selected_level}', True, WHITE)
        lvl_shadow = font.render(f'УРОВЕНЬ {selected_level}', True, (0, 0, 0))
        lvl_x = WIDTH // 2 - lvl_txt.get_width() // 2
        screen.blit(lvl_shadow, (lvl_x + 2, 307))
        screen.blit(lvl_txt, (lvl_x, 305))
        # Секция музыки с улучшенным дизайном
        music_section_rect = pygame.Rect(WIDTH // 2 - 350, 380, 700, 120)
        draw_gradient_rect(screen, music_section_rect, (40, 35, 55), (30, 25, 45))
        pygame.draw.rect(screen, (80, 70, 95), music_section_rect, 2, border_radius=12)
        
        # Заголовок секции музыки
        music_title = small.render('ФОНОВАЯ МУЗЫКА', True, ACCENT_SECONDARY)
        music_title_x = WIDTH // 2 - music_title.get_width() // 2
        screen.blit(music_title, (music_title_x, 395))
        
        # Блок выбора музыки с увеличенными кнопками
        music_rect = pygame.Rect(WIDTH // 2 - 350, 425, 700, 70)  # Увеличиваем высоту с 60 до 70
        music_left_btn = pygame.Rect(music_rect.x - 80, music_rect.y + 10, 60, 50)  # Увеличиваем с 40х40 до 60х50
        music_right_btn = pygame.Rect(music_rect.right + 20, music_rect.y + 10, 60, 50)  # Увеличиваем с 40х40 до 60х50
        
        # Обработка мыши для музыки
        music_hover = music_rect.collidepoint(mouse_pos)
        music_left_hover = music_left_btn.collidepoint(mouse_pos)
        music_right_hover = music_right_btn.collidepoint(mouse_pos)
        
        if mouse_clicked and audio.enabled:
            if music_left_hover:
                music_index = (music_index - 1) % len(audio.playlist)
                # Сразу переключаем трек для предварительного прослушивания
                if music_index >= 0:
                    audio.index = music_index
                    audio.play_current()
            elif music_right_hover:
                music_index = (music_index + 1) % len(audio.playlist)
                # Сразу переключаем трек для предварительного прослушивания
                if music_index >= 0:
                    audio.index = music_index
                    audio.play_current()
        
        # Рисуем кнопки музыки с улучшенным дизайном
        if audio.enabled:
            # Кнопка "назад" с градиентом
            music_left_color = ACCENT_SECONDARY if music_left_hover else (70, 60, 90)
            draw_gradient_rect(screen, music_left_btn, music_left_color, tuple(max(0, c - 30) for c in music_left_color))
            pygame.draw.rect(screen, (140, 120, 180) if music_left_hover else (100, 80, 130), music_left_btn, 2, border_radius=8)
            
            # Кнопка "вперед" с градиентом
            music_right_color = ACCENT_SECONDARY if music_right_hover else (70, 60, 90)
            draw_gradient_rect(screen, music_right_btn, music_right_color, tuple(max(0, c - 30) for c in music_right_color))
            pygame.draw.rect(screen, (140, 120, 180) if music_right_hover else (100, 80, 130), music_right_btn, 2, border_radius=8)
            
            # Стрелки на кнопках музыки с безопасным адаптивным шрифтом
            try:
                arrow_font = get_adaptive_font('‹', font, music_left_btn.width - 4, music_left_btn.height - 4) if responsive else font
            except Exception:
                arrow_font = font
            left_arrow = arrow_font.render('‹', True, WHITE)  # Красивая стрелка назад
            right_arrow = arrow_font.render('›', True, WHITE)  # Красивая стрелка вперед
            screen.blit(left_arrow, (music_left_btn.centerx - left_arrow.get_width() // 2, music_left_btn.centery - left_arrow.get_height() // 2))
            screen.blit(right_arrow, (music_right_btn.centerx - right_arrow.get_width() // 2, music_right_btn.centery - right_arrow.get_height() // 2))
        
        # Улучшенный фон для музыки
        music_bg_color = (50, 45, 65) if music_hover else (45, 40, 60)
        draw_gradient_rect(screen, music_rect, music_bg_color, tuple(max(0, c - 10) for c in music_bg_color))
        pygame.draw.rect(screen, (85, 75, 95), music_rect, 2, border_radius=10)
        
        if audio.enabled and music_index >= 0:
            music_name = os.path.basename(audio.playlist[music_index])
            # Удаляем расширение файла для красивого отображения
            if '.' in music_name:
                music_name = music_name.rsplit('.', 1)[0]
            
            # Адаптивное масштабирование текста названия музыки с безопасностью
            try:
                music_display_font = get_adaptive_font(f'♪ {music_name}', small, music_rect.width - 20, 30) if responsive else small
            except Exception:
                music_display_font = small
            music_txt = music_display_font.render(f'♪ {music_name}', True, ACCENT_SECONDARY)
        else:
            music_txt = small.render('♪ Музыка: (не найдена)', True, DIM)
        
        music_x = WIDTH // 2 - music_txt.get_width() // 2
        screen.blit(music_txt, (music_x, 450))
        
        # Подсказка о музыке
        music_hint = small.render('↑↓ - смена трека', True, (140, 150, 160))
        music_hint_x = WIDTH // 2 - music_hint.get_width() // 2
        screen.blit(music_hint, (music_hint_x, 470))
        
        # Кнопка старта с увеличенным дизайном
        start_section_rect = pygame.Rect(WIDTH // 2 - 250, 530, 500, 100)  # Увеличиваем с 400х80 до 500х100
        start_hover = start_section_rect.collidepoint(mouse_pos)
        
        if mouse_clicked and start_hover:
            return selected_level, music_index
        
        # Эффект наведения на кнопку старта
        start_bg_color = tuple(min(255, c + 20) for c in ACCENT_PRIMARY) if start_hover else ACCENT_PRIMARY
        draw_gradient_rect(screen, start_section_rect, start_bg_color, tuple(max(0, c - 20) for c in start_bg_color))
        border_color = (110, 190, 255) if start_hover else (90, 170, 255)
        pygame.draw.rect(screen, border_color, start_section_rect, 3, border_radius=15)
        
        start_hint = font.render('ENTER - НАЧАТЬ ИГРУ', True, WHITE)
        start_shadow = font.render('ENTER - НАЧАТЬ ИГРУ', True, (0, 0, 0))
        start_x = WIDTH // 2 - start_hint.get_width() // 2
        start_y = start_section_rect.y + (start_section_rect.height - start_hint.get_height()) // 2
        screen.blit(start_shadow, (start_x + 2, start_y + 2))
        screen.blit(start_hint, (start_x, start_y))
        
        # Контрольная панель внизу с увеличенным размером
        controls_rect = pygame.Rect(WIDTH // 2 - 400, HEIGHT - 90, 800, 50)  # Увеличиваем с 600х35 до 800х50
        draw_gradient_rect(screen, controls_rect, (25, 30, 38), (20, 25, 33))
        pygame.draw.rect(screen, (50, 60, 75), controls_rect, 1, border_radius=8)
        
        controls_text = 'Уровень: ←→/Мышь | Музыка: ↑↓/Мышь | Старт: Enter/Клик | Выход: Q'
        try:
            controls_font = get_adaptive_font(controls_text, small, controls_rect.width - 20, controls_rect.height - 8) if responsive else small
        except Exception:
            controls_font = small
        controls_hint = controls_font.render(controls_text, True, WHITE)
        controls_x = WIDTH // 2 - controls_hint.get_width() // 2
        controls_y = controls_rect.y + (controls_rect.height - controls_hint.get_height()) // 2
        screen.blit(controls_hint, (controls_x, controls_y))
        
        # Меняем курсор при наведении на интерактивные элементы
        if left_hover or right_hover or start_hover or (audio.enabled and (music_left_hover or music_right_hover)):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        # Тултипы для кнопок (оптимизированные)
        if left_hover:
            draw_optimized_tooltip(screen, "Уменьшить уровень", mouse_pos, small)
        elif right_hover:
            draw_optimized_tooltip(screen, "Увеличить уровень", mouse_pos, small)
        elif start_hover:
            draw_optimized_tooltip(screen, "Начать игру", mouse_pos, small)
        elif audio.enabled and music_left_hover:
            draw_optimized_tooltip(screen, "Предыдущий трек", mouse_pos, small)
        elif audio.enabled and music_right_hover:
            draw_optimized_tooltip(screen, "Следующий трек", mouse_pos, small)
        
        pygame.display.flip()
    return selected_level, music_index

# Глобальное состояние для оптимизации тултипов
tooltip_cache = {}
tooltip_timer = 0.0
tooltip_delay = 0.8  # Задержка перед показом тултипа (секунды)
current_tooltip_text = ""
last_tooltip_pos = (0, 0)

def draw_optimized_tooltip(surf, text, mouse_pos, font, show_immediately=False):
    """Оптимизированная система тултипов с задержкой и кэшированием"""
    global tooltip_cache, tooltip_timer, current_tooltip_text, last_tooltip_pos
    
    # Проверяем, изменился ли текст тултипа или позиция
    pos_changed = abs(mouse_pos[0] - last_tooltip_pos[0]) > 5 or abs(mouse_pos[1] - last_tooltip_pos[1]) > 5
    text_changed = text != current_tooltip_text
    
    if text_changed or pos_changed:
        tooltip_timer = 0.0
        current_tooltip_text = text
        last_tooltip_pos = mouse_pos
        return  # Не показываем тултип сразу
    
    # Увеличиваем таймер только если мышь не двигается
    if not show_immediately:
        tooltip_timer += 1/60.0  # Приблизительно 60 FPS
        if tooltip_timer < tooltip_delay:
            return  # Ещё не время показывать тултип
    
    # Кэшируем рендер тултипа
    cache_key = f"{text}_{font.get_height()}"
    if cache_key not in tooltip_cache:
        tooltip_surf = font.render(text, True, WHITE)
        tooltip_cache[cache_key] = tooltip_surf
        # Ограничиваем размер кэша
        if len(tooltip_cache) > 20:
            oldest_key = next(iter(tooltip_cache))
            del tooltip_cache[oldest_key]
    else:
        tooltip_surf = tooltip_cache[cache_key]
    
    tooltip_rect = tooltip_surf.get_rect()
    
    # Умное позиционирование тултипа
    tooltip_x = mouse_pos[0] + 15
    tooltip_y = mouse_pos[1] - 35
    
    # Проверяем границы экрана
    if tooltip_x + tooltip_rect.width > WIDTH - 10:
        tooltip_x = mouse_pos[0] - tooltip_rect.width - 15
    if tooltip_y < 10:
        tooltip_y = mouse_pos[1] + 20
    if tooltip_y + tooltip_rect.height > HEIGHT - 10:
        tooltip_y = HEIGHT - tooltip_rect.height - 10
    
    # Фон тултипа (простой, без градиента для производительности)
    bg_rect = pygame.Rect(tooltip_x - 6, tooltip_y - 4, tooltip_rect.width + 12, tooltip_rect.height + 8)
    pygame.draw.rect(surf, (45, 45, 55), bg_rect, border_radius=6)
    pygame.draw.rect(surf, (85, 85, 95), bg_rect, 1, border_radius=6)
    
    # Текст тултипа
    surf.blit(tooltip_surf, (tooltip_x, tooltip_y))

def reset_tooltip_state():
    """Сбрасывает состояние тултипов"""
    global tooltip_timer, current_tooltip_text
    tooltip_timer = 0.0
    current_tooltip_text = ""

def pause_menu(screen, clock, font, small, audio: AudioManager, state: GameState):
    """Оптимизированное меню паузы с адаптивным дизайном"""
    # Переключаемся на музыку паузы при входе в меню
    original_context = audio.current_context
    if audio.enabled and audio.pause_playlist:
        print("[Pause] Switching to pause music context")
        audio.set_context('pause')
        audio.play_current()
    
    # Адаптивные размеры меню
    base_w, base_h = 600, 650  # Увеличиваем высоту для дополнительной кнопки
    w = responsive.scale_width(base_w) if responsive else base_w
    h = responsive.scale_height(base_h) if responsive else base_h
    
    # Центрируем меню по всему экрану
    rx = (WIDTH - w) // 2
    ry = (HEIGHT - h) // 2
    
    # Адаптивные шрифты
    title_font_size = responsive.scale_font(36) if responsive else 36
    button_font_size = responsive.scale_font(24) if responsive else 24
    
    try:
        bigfont = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto,consolas,monospace', title_font_size, bold=True)
        button_font = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto,consolas,monospace', button_font_size, bold=True)
    except Exception:
        # Фолбэк на стандартные шрифты
        bigfont = pygame.font.SysFont('consolas,monospace', title_font_size, bold=True)
        button_font = pygame.font.SysFont('consolas,monospace', button_font_size, bold=True)
    
    buttons = [
        ('Продолжить', 'resume', 'primary'),
        ('Сохранить', 'save', 'success'),
        ('Загрузить', 'load', 'success'),
        ('Настройки экрана', 'resolution', 'default'),
        ('След. музыка', 'next', 'default'),
        ('Пред. музыка', 'prev', 'default'),
        ('Главное меню', 'main_menu', 'primary'),
        ('Выйти', 'quit', 'danger'),
    ]
    
    # Адаптивные размеры кнопок
    button_width = w - responsive.get_margin(100) if responsive else w - 100
    button_height = responsive.scale_height(52) if responsive else 52
    button_spacing = responsive.scale_height(68) if responsive else 68
    button_start_y = ry + responsive.scale_height(90) if responsive else ry + 90
    button_margin_x = responsive.get_margin(50) if responsive else 50
    
    btn_rects = [(button_rect(rx + button_margin_x, button_start_y + i * button_spacing, button_width, button_height), action, text, style)
                 for i, (text, action, style) in enumerate(buttons)]
    
    tooltip_map = {
        'resume': 'Продолжить игру', 'save': 'Сохранить текущую игру',
        'load': 'Загрузить сохранённую игру', 'resolution': 'Изменить разрешение экрана',
        'next': 'Переключить на следующий трек', 'prev': 'Переключить на предыдущий трек',
        'main_menu': 'Вернуться в главное меню', 'quit': 'Выйти из игры'
    }
    
    reset_tooltip_state()
    cached_title = bigfont.render('ПАУЗА', True, WHITE)
    cached_title_shadow = bigfont.render('ПАУЗА', True, (0, 0, 0))
    
    while True:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_p, pygame.K_ESCAPE):
                    # Возвращаем оригинальный контекст музыки
                    if audio.enabled and original_context != 'pause':
                        print(f"[Pause] Restoring {original_context} music context")
                        audio.set_context(original_context)
                        audio.play_current()
                    return 'resume'
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mouse_clicked = True
        
        # Простой фон без сложных эффектов
        menu_rect = pygame.Rect(rx, ry, w, h)
        pygame.draw.rect(screen, (25, 30, 40), menu_rect, border_radius=20)
        pygame.draw.rect(screen, (80, 120, 160), menu_rect, 3, border_radius=20)
        
        # Заголовок
        title_rect = pygame.Rect(rx + 20, ry + 20, w - 40, 50)
        pygame.draw.rect(screen, ACCENT_WARNING, title_rect, border_radius=12)
        pygame.draw.rect(screen, (200, 150, 80), title_rect, 2, border_radius=12)
        
        title_x = rx + (w - cached_title.get_width()) // 2
        title_y = ry + 35
        screen.blit(cached_title_shadow, (title_x + 2, title_y + 2))
        screen.blit(cached_title, (title_x, title_y))
        
        # Обработка кнопок
        any_hover = False
        current_tooltip_text = ""
        
        for rect, action, text, style in btn_rects:
            hover = rect.collidepoint(mouse_pos)
            
            if hover:
                any_hover = True
                current_tooltip_text = tooltip_map.get(action, text)
                
                if mouse_clicked:
                    if action == 'resume': 
                        # Возвращаем оригинальный контекст музыки
                        if audio.enabled and original_context != 'pause':
                            print(f"[Pause] Restoring {original_context} music context")
                            audio.set_context(original_context)
                            audio.play_current()
                        return 'resume'
                    elif action == 'save': save_game(state)
                    elif action == 'load':
                        loaded = load_game()
                        if loaded: 
                            # Возвращаем оригинальный контекст музыки
                            if audio.enabled and original_context != 'pause':
                                print(f"[Pause] Restoring {original_context} music context")
                                audio.set_context(original_context)
                                audio.play_current()
                            return ('load', loaded)
                    elif action == 'resolution':
                        # Открываем меню выбора разрешения с динамическим обновлением
                        try:
                            selected_resolution = resolution_selection_menu()
                            if selected_resolution:
                                # Применяем новое разрешение немедленно
                                new_screen = apply_resolution_change(screen, selected_resolution)
                                if new_screen:
                                    print(f"[Настройки] Разрешение успешно изменено на: {selected_resolution[0]}x{selected_resolution[1]}")
                                    # Возвращаем новый screen через специальный результат
                                    return ('resolution_changed', new_screen)
                        except Exception as e:
                            print(f"[Ошибка] Не удалось открыть меню разрешения: {e}")
                    elif action == 'next': audio.next()
                    elif action == 'prev': audio.prev()
                    elif action == 'main_menu': 
                        # Не восстанавливаем контекст - он будет переключён на menu в основном цикле
                        return 'main_menu'
                    elif action == 'quit': 
                        return 'quit'
            
            draw_button(screen, rect, text, button_font, hover=hover, style=style)
        
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if any_hover else pygame.SYSTEM_CURSOR_ARROW)
        
        if current_tooltip_text and any_hover:
            draw_optimized_tooltip(screen, current_tooltip_text, mouse_pos, small)
        
        pygame.display.flip()

# -------------------- Меню выбора разрешения --------------------
def resolution_selection_menu() -> Tuple[int, int]:
    """
    Полноценное меню выбора разрешения экрана с предпросмотром.
    Возвращает выбранное разрешение (width, height).
    """
    pygame.init()
    
    # Используем временное окно для меню
    temp_screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption('Выбор разрешения - Tetris Enhanced')
    clock = pygame.time.Clock()
    
    # Шрифты для меню
    try:
        title_font = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto', 36, bold=True)
        option_font = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto', 24, bold=True)
        desc_font = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto', 18)
        help_font = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto', 16)
    except Exception:
        # Фолбэк на стандартные шрифты
        title_font = pygame.font.SysFont('arial,helvetica', 36, bold=True)
        option_font = pygame.font.SysFont('arial,helvetica', 24, bold=True)
        desc_font = pygame.font.SysFont('arial,helvetica', 18)
        help_font = pygame.font.SysFont('arial,helvetica', 16)
    
    # Получаем доступные разрешения
    filtered_resolutions = game_config.get_filtered_resolutions()
    
    # Добавляем автоматическое определение как первую опцию
    options = [("Авто определение", "auto")] + [(f"{w}x{h}", (w, h)) for w, h in filtered_resolutions]
    
    selected_index = 0
    mouse_pos = (0, 0)
    
    # Колора темы
    bg_color = (15, 20, 30)
    panel_color = (25, 35, 50)
    selected_color = (45, 75, 110)
    hover_color = (35, 55, 80)
    text_color = (220, 230, 240)
    accent_color = (100, 150, 255)
    
    while True:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                elif event.key == pygame.K_UP:
                    selected_index = max(0, selected_index - 1)
                elif event.key == pygame.K_DOWN:
                    selected_index = min(len(options) - 1, selected_index + 1)
                elif event.key == pygame.K_RETURN:
                    if selected_index == 0:  # Авто
                        return (1366, 768)  # Стандартное значение
                    else:
                        return options[selected_index][1]
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ
                    # Проверяем клик по опциям
                    for i, (name, value) in enumerate(options):
                        option_y = 180 + i * 50
                        option_rect = pygame.Rect(100, option_y, 800, 45)
                        if option_rect.collidepoint(mouse_pos):
                            if i == 0:  # Авто
                                return (1366, 768)
                            else:
                                return value
        
        # Отрисовка
        temp_screen.fill(bg_color)
        
        # Заголовок
        title_text = title_font.render("Выберите разрешение экрана", True, text_color)
        title_x = (1000 - title_text.get_width()) // 2
        temp_screen.blit(title_text, (title_x, 30))
        
        # Описание
        desc_text = desc_font.render("Выберите оптимальное разрешение для вашего экрана", True, (180, 190, 200))
        desc_x = (1000 - desc_text.get_width()) // 2
        temp_screen.blit(desc_text, (desc_x, 80))
        
        # Панель опций
        panel_rect = pygame.Rect(50, 130, 900, len(options) * 50 + 40)
        pygame.draw.rect(temp_screen, panel_color, panel_rect, border_radius=15)
        pygame.draw.rect(temp_screen, (60, 80, 110), panel_rect, 2, border_radius=15)
        
        # Опции разрешений
        for i, (name, value) in enumerate(options):
            option_y = 180 + i * 50
            option_rect = pygame.Rect(100, option_y, 800, 45)
            
            # Определяем состояние (выбрано/наведено)
            is_selected = (i == selected_index)
            is_hovered = option_rect.collidepoint(mouse_pos)
            
            # Цвет фона
            if is_selected:
                bg_color_option = selected_color
            elif is_hovered:
                bg_color_option = hover_color
                selected_index = i  # Обновляем выбор при наведении
            else:
                bg_color_option = None
            
            # Отрисовка фона опции
            if bg_color_option:
                pygame.draw.rect(temp_screen, bg_color_option, option_rect, border_radius=8)
            
            # Обводка для выбранной опции
            if is_selected:
                pygame.draw.rect(temp_screen, accent_color, option_rect, 3, border_radius=8)
            
            # Текст опции
            option_text = option_font.render(name, True, text_color)
            text_x = option_rect.x + 20
            text_y = option_rect.y + (option_rect.height - option_text.get_height()) // 2
            temp_screen.blit(option_text, (text_x, text_y))
            
            # Дополнительная информация
            if i == 0:
                info_text = "Автоматически определит оптимальное разрешение"
                info_color = (120, 200, 120)
            else:
                w, h = value
                ratio = w / h
                if abs(ratio - 16/9) < 0.1:
                    aspect = "16:9"
                elif abs(ratio - 4/3) < 0.1:
                    aspect = "4:3"
                elif abs(ratio - 16/10) < 0.1:
                    aspect = "16:10"
                else:
                    aspect = f"{ratio:.2f}:1"
                info_text = f"Соотношение сторон: {aspect}"
                info_color = (150, 170, 200)
            
            info_surface = help_font.render(info_text, True, info_color)
            info_x = option_rect.right - info_surface.get_width() - 20
            info_y = text_y + 3
            temp_screen.blit(info_surface, (info_x, info_y))
        
        # Инструкции
        help_y = panel_rect.bottom + 30
        help_texts = [
            "↑↓ / Мышь - выбор",
            "Enter / Клик - подтвердить",
            "Esc - выход"
        ]
        
        for i, help_text in enumerate(help_texts):
            help_surface = help_font.render(help_text, True, (140, 150, 160))
            help_x = (1000 - help_surface.get_width()) // 2
            temp_screen.blit(help_surface, (help_x, help_y + i * 25))
        
        # Предупреждение
        warning_text = desc_font.render("Разрешение можно будет изменить в настройках игры", True, (200, 150, 100))
        warning_x = (1000 - warning_text.get_width()) // 2
        temp_screen.blit(warning_text, (warning_x, 650))
        
        pygame.display.flip()
    
    return (1366, 768)  # Фолбэк

def change_resolution_and_restart():
    """
    Позволяет пользователю выбрать новое разрешение и перезапустить игру.
    Возвращает True если нужно перезапустить игру, False если отменено.
    """
    global game_config
    
    # Показываем меню выбора разрешения
    selected_resolution = resolution_selection_menu()
    
    # Обновляем конфигурацию
    game_config.screen_width, game_config.screen_height = selected_resolution
    game_config.save_to_file()
    
    print(f"[Настройки] Выбрано новое разрешение: {selected_resolution[0]}x{selected_resolution[1]}")
    print("[Настройки] Игра будет перезапущена...")
    
    return True

def apply_resolution_change(screen, selected_resolution):
    """
    Применяет новое разрешение экрана без перезапуска игры.
    Обновляет pygame окно и все связанные компоненты.
    """
    global game_config, responsive, WIDTH, HEIGHT, ORIGIN_X, ORIGIN_Y, PLAY_W, PLAY_H, BLOCK, PANEL_W, MARGIN
    
    try:
        # Обновляем конфигурацию
        game_config.screen_width, game_config.screen_height = selected_resolution
        game_config.save_to_file()
        
        print(f"[Разрешение] Применение нового разрешения: {selected_resolution[0]}x{selected_resolution[1]}")
        
        # Пересоздаем pygame экран с новым разрешением
        new_screen = pygame.display.set_mode(selected_resolution)
        
        # Пересоздаем адаптивную систему дизайна
        WIDTH, HEIGHT = selected_resolution
        responsive = AdvancedResponsiveDesign(WIDTH, HEIGHT)
        
        # Обновляем позиции игрового поля
        ORIGIN_X, ORIGIN_Y, PLAY_W, PLAY_H, BLOCK = responsive.get_grid_position()
        MARGIN = responsive.get_margin(25)
        PANEL_W = responsive.get_panel_position(ORIGIN_X, PLAY_W)[2]
        
        print(f"[Разрешение] Обновлена компоновка: Поле на ({ORIGIN_X}, {ORIGIN_Y}), Размер: {PLAY_W}x{PLAY_H}, Блок: {BLOCK}px")
        print(f"[Разрешение] Панель: Ширина {PANEL_W}px, Отступ: {MARGIN}px")
        
        return new_screen
        
    except Exception as e:
        print(f"[Ошибка] Не удалось применить новое разрешение: {e}")
        print("[Ошибка] Возвращаемся к старому разрешению")
        return screen
def new_game(start_level=1, game_mode=GameMode.ENDLESS_IMMERSIVE, campaign_level=1) -> GameState:
    """Создаёт новую игру с указанным режимом"""
    state = GameState()
    state.level = start_level
    initialize_game_mode(state, game_mode, campaign_level)
    refill_bag(state)
    spawn_next(state)
    return state

def run():
    # Проверяем, нужно ли показывать меню выбора разрешения
    global game_config
    
    # Если конфигурация не загружена или используется стандартное разрешение,
    # показываем меню выбора
    if not os.path.exists("config.json") or (game_config.screen_width == 1366 and game_config.screen_height == 768):
        print("[Игра] Показ меню выбора разрешения")
        selected_resolution = resolution_selection_menu()
        
        # Обновляем конфигурацию с выбранным разрешением
        game_config.screen_width, game_config.screen_height = selected_resolution
        game_config.save_to_file()  # Сохраняем выбор пользователя
        
        print(f"[Игра] Выбрано разрешение: {selected_resolution[0]}x{selected_resolution[1]}")
    else:
        print(f"[Игра] Использование сохраненного разрешения: {game_config.screen_width}x{game_config.screen_height}")
    pygame.init()
    
    # Инициализируем адаптивный дизайн с выбранным разрешением
    game_width, game_height = init_responsive_design_with_config()
    
    pygame.display.set_caption('Tetris Enhanced')
    screen = pygame.display.set_mode((game_width, game_height))
    clock = pygame.time.Clock()
    
    # Используем адаптивные размеры шрифтов
    font_size = responsive.scale_font(48) if responsive else 48
    small_size = responsive.scale_font(20) if responsive else 20
    
    # Используем шрифты с поддержкой кириллицы
    try:
        font = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace', font_size, bold=True)
        small = pygame.font.SysFont('arial,verdana,tahoma,calibri,segoeui,roboto,consolas,dejavusansmono,menlo,monospace', small_size)
    except Exception as e:
        print(f"[Ошибка] Не удалось загрузить шрифты с поддержкой кириллицы: {e}")
        # Фолбэк на стандартные шрифты
        font = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', font_size, bold=True)
        small = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', small_size)

    audio = AudioManager()
    
    # Запускаем музыку меню сразу после создания AudioManager
    if audio.enabled:
        audio.set_context('menu')
        audio.play_current()
        print("[Menu] Starting menu music at game startup")

    while True:  # Основной цикл для перезапуска в главное меню
        # Меню выбора режима и стартовое меню
        selected_mode = mode_selection_menu(screen, clock, font, small, audio)
        
        # Выбор уровня кампании или обычное стартовое меню
        campaign_level = 1
        start_level = 1
        music_choice = -1
        
        if selected_mode == GameMode.CAMPAIGN:
            campaign_level = campaign_level_selection_menu(screen, clock, font, small, audio)
            if campaign_level is None:
                # Пользователь вернулся назад - перезапускаем выбор режима
                continue
            # Музыка для кампании
            start_level, music_choice = start_menu(screen, clock, font, small, audio)
        else:
            # Обычное стартовое меню для бесконечных режимов
            start_level, music_choice = start_menu(screen, clock, font, small, audio)
        
        if audio.enabled and music_choice >= 0:
            # Пользователь выбрал конкретный трек - переключаемся на него
            current_playlist = audio.get_current_playlist()
            if current_playlist and music_choice < len(current_playlist):
                print(f"[Menu] User selected specific track: {music_choice}")
                audio.set_current_index(music_choice)
                audio.play_current()

        state = new_game(start_level, selected_mode, campaign_level)

        # Используем класс InputState вместо локальных переменных
        input_state = InputState()
        das = 0.12  # Увеличиваем задержку для менее чувствительного управления влево/вправо
        arr = 0.035  # Увеличиваем интервал повтора для более медленного автоповтора

        game_result = run_game_loop(screen, clock, font, small, audio, state, input_state, das, arr, start_level, selected_mode, campaign_level)
        
        if game_result == 'main_menu':
            # Переключаемся обратно на музыку меню при возврате в главное меню
            if audio.enabled:
                print("[Menu] Switching back to menu music context")
                audio.set_context('menu')
                audio.play_current()
            continue  # Перезапускаем в главное меню
        elif isinstance(game_result, tuple) and game_result[0] == 'resolution_changed':
            # Обрабатываем изменение разрешения
            screen = game_result[1]  # Обновляем screen
            
            # Пересоздаем шрифты с новыми размерами
            font_size = responsive.scale_font(48) if responsive else 48
            small_size = responsive.scale_font(20) if responsive else 20
            font = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', font_size, bold=True)
            small = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', small_size)
            
            print(f"[Разрешение] Шрифты обновлены: Основной {font_size}px, Малый {small_size}px")
            continue  # Продолжаем игру с новым разрешением
        elif game_result == 'quit':
            break  # Выходим из игры

def run_game_loop(screen, clock, font, small, audio, state, input_state, das, arr, start_level, selected_mode, campaign_level):
    # Переключаемся на игровую музыку при входе в игру
    if audio.enabled:
        print("[Game] Switching to game music context")
        audio.set_context('game')

    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return 'quit'
            if ev.type == MUSIC_END_EVENT:
                audio.next()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q:
                    return 'quit'
                if ev.key in (pygame.K_p, pygame.K_ESCAPE):
                    # pause menu
                    action = pause_menu(screen, clock, font, small, audio, state)
                    if action == 'resume' or action == None:
                        pass
                    elif action == 'quit':
                        return 'quit'
                    elif action == 'main_menu':
                        return 'main_menu'  # Возвращаемся в главное меню
                    elif isinstance(action, tuple) and action[0] == 'load':
                        # replace state with loaded
                        loaded = action[1]
                        state = loaded
                    elif isinstance(action, tuple) and action[0] == 'resolution_changed':
                        # Обновляем screen на новый с измененным разрешением
                        new_screen = action[1]
                        return ('resolution_changed', new_screen)
                if ev.key == pygame.K_r:
                    state = new_game(start_level, selected_mode, campaign_level)
                if state.game_over or state.paused:
                    continue
                if ev.key == pygame.K_LEFT:
                    input_state.left = True
                    input_state.right = False
                    input_state.last_direction = 'L'
                    input_state.das_timer = 0.0
                    if try_move(state, -1, 0):
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_RIGHT:
                    input_state.right = True
                    input_state.left = False
                    input_state.last_direction = 'R'
                    input_state.das_timer = 0.0
                    if try_move(state, +1, 0):
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_DOWN:
                    # Оптимизированная обработка кнопки вниз
                    if input_state.can_perform_action('down'):
                        input_state.start_key_press('down')
                        input_state.down = True
                        input_state.down_activated_for_current_piece = True
                        input_state.mark_action_performed('down')
                        
                        # Немедленная обратная связь - лёгкое мовение вниз
                        if try_move(state, 0, 1):
                            state.score += 1
                            audio.play_sfx('rotate')  # Лёгкий звук обратной связи
                elif ev.key in (pygame.K_UP, pygame.K_z):
                    ok, tspin = try_rotate(state, +1)
                    if ok:
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_x:
                    ok, tspin = try_rotate(state, -1)
                    if ok:
                        audio.play_sfx('rotate')
                elif ev.key in (pygame.K_a, pygame.K_s):
                    ok, tspin = try_rotate(state, +2)
                    if ok:
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_SPACE:
                    # Оптимизированная обработка пробела
                    if input_state.can_perform_action('space'):
                        input_state.start_key_press('space')
                        input_state.mark_action_performed('space')
                elif ev.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    hold_swap(state)
            elif ev.type == pygame.KEYUP:
                if ev.key == pygame.K_LEFT:
                    input_state.left = False
                elif ev.key == pygame.K_RIGHT:
                    input_state.right = False
                elif ev.key == pygame.K_DOWN:
                    # Улучшенная обработка отпускания кнопки вниз
                    intent = input_state.get_press_intent('down')
                    press_type = input_state.end_key_press('down')
                    input_state.down = False
                    
                    # Определяем действие на основе намерения и длительности
                    if intent == 'tap':
                        # Короткое касание - минимальная активность
                        is_double = input_state.is_double_press('down')
                        if is_double:
                            input_state.start_enhanced_smooth_fall(2.5, intent, True)
                            audio.play_sfx('rotate')
                        # Одиночное короткое касание - ничего не делаем
                        
                    elif intent == 'press':
                        # Осознанное нажатие - обычное плавное падение
                        is_double = input_state.is_double_press('down')
                        input_state.start_enhanced_smooth_fall(3.5, intent, is_double)
                        if is_double:
                            audio.play_sfx('rotate')
                            
                    elif intent == 'hold':
                        # Долгое удержание - быстрое плавное падение
                        is_double = input_state.is_double_press('down')
                        input_state.start_enhanced_smooth_fall(5.0, intent, is_double)
                        if is_double:
                            audio.play_sfx('rotate')
                    
                    # Останавливаем плавное падение при отпускании клавиши (только для не-двойных)
                    if input_state.smooth_fall_active and not input_state.smooth_fall_double_press:
                        input_state.reset_falling_animation()
                elif ev.key == pygame.K_SPACE:
                    # Улучшенная обработка отпускания пробела
                    intent = input_state.get_press_intent('space')
                    press_type = input_state.end_key_press('space')
                    
                    if intent == 'tap':
                        # Короткое касание - мягкое плавное падение
                        is_double = input_state.is_double_press('space')
                        if is_double:
                            input_state.start_enhanced_smooth_fall(3.0, 'press', True)  # Уменьшаем с 6.0 до 3.0
                            audio.play_sfx('rotate')
                        else:
                            input_state.start_enhanced_smooth_fall(2.5, 'press', False)  # Уменьшаем с 4.5 до 2.5
                            
                    elif intent == 'press':
                        # Осознанное нажатие - умеренное жёсткое падение
                        is_double = input_state.is_double_press('space')
                        if is_double:
                            # Двойное среднее - быстрое жёсткое падение
                            if state.current is not None and not state.hard_drop_anim:
                                d = hard_drop_distance(state)
                                if d > 0:
                                    current_time = pygame.time.get_ticks() / 1000.0
                                    start_y = state.current.y
                                    target_y = state.current.y + d
                                    duration = min(0.20, 0.015 + 0.005 * d)  # Увеличиваем длительность анимации
                                    state.hard_drop_anim = True
                                    state.hard_drop_start_y = start_y
                                    state.hard_drop_target_y = target_y
                                    state.hard_drop_duration = duration
                                    state.hard_drop_start_time = current_time
                                    state.score += 2 * d
                                    audio.play_sfx('drop')
                        else:
                            # Одиночное среднее - плавное падение
                            input_state.start_enhanced_smooth_fall(4.5, intent, False)  # Уменьшаем с 6.0 до 4.5
                            
                    elif intent == 'hold':
                        # Долгое удержание - максимально быстрое жёсткое падение
                        if state.current is not None and not state.hard_drop_anim:
                            d = hard_drop_distance(state)
                            if d > 0:
                                current_time = pygame.time.get_ticks() / 1000.0
                                start_y = state.current.y
                                target_y = state.current.y + d
                                duration = min(0.12, 0.008 + 0.002 * d)  # Увеличиваем с очень быстрой до быстрой
                                state.hard_drop_anim = True
                                state.hard_drop_start_y = start_y
                                state.hard_drop_target_y = target_y
                                state.hard_drop_duration = duration
                                state.hard_drop_start_time = current_time
                                state.score += 2 * d
                                audio.play_sfx('drop')

        if state.game_over:
            draw_enhanced_background(screen)
            draw_grid(screen, ORIGIN_X, ORIGIN_Y, state)
            if state.current:
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, state.current)
            panel_x = ORIGIN_X + PLAY_W + MARGIN
            draw_panel(screen, panel_x, MARGIN, state, font, small, audio)
            
            # Улучшенный экран Game Over
            overlay_w, overlay_h = 480, 320
            overlay_x = ORIGIN_X + (PLAY_W - overlay_w) // 2
            overlay_y = ORIGIN_Y + (PLAY_H - overlay_h) // 2
            
            # Тень оверлея
            shadow_surf = pygame.Surface((overlay_w + 8, overlay_h + 8), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, 150))
            screen.blit(shadow_surf, (overlay_x - 4, overlay_y - 4))
            
            # Основной оверлей с градиентом
            overlay_rect = pygame.Rect(overlay_x, overlay_y, overlay_w, overlay_h)
            draw_gradient_rect(screen, overlay_rect, (40, 25, 25), (25, 15, 15))
            pygame.draw.rect(screen, (120, 60, 60), overlay_rect, 3, border_radius=20)
            
            # Анимированный заголовок GAME OVER
            title_rect = pygame.Rect(overlay_x + 20, overlay_y + 20, overlay_w - 40, 60)
            current_time = time.time()
            title_glow = pulse_effect(0, 0.6, 0.4)
            title_top = glow_color((255, 100, 100), title_glow, 0)
            title_bottom = glow_color((200, 50, 50), title_glow, 0.5)
            draw_gradient_rect(screen, title_rect, title_top, title_bottom, vertical=False)
            pygame.draw.rect(screen, (180, 80, 80), title_rect, 2, border_radius=12)
            
            go_txt = font.render('GAME OVER', True, WHITE)
            go_shadow = font.render('GAME OVER', True, (0, 0, 0))
            go_x = overlay_x + (overlay_w - go_txt.get_width()) // 2
            go_y = overlay_y + 40
            screen.blit(go_shadow, (go_x + 2, go_y + 2))
            screen.blit(go_txt, (go_x, go_y))
            
            # Статистика игры
            stats_y = overlay_y + 120
            stats_info = [
                f'Финальный счёт: {state.score:,}',
                f'Очищено линий: {state.lines}',
                f'Достигнутый уровень: {state.level}'
            ]
            
            if state.combo > 0:
                stats_info.append(f'Максимальное комбо: x{state.combo}')
            
            for i, info in enumerate(stats_info):
                stats_text = small.render(info, True, WHITE)
                stats_x = overlay_x + (overlay_w - stats_text.get_width()) // 2
                screen.blit(stats_text, (stats_x, stats_y + i * 25))
            
            # Инструкции с улучшенным дизайном
            controls_y = overlay_y + overlay_h - 80
            controls_rect = pygame.Rect(overlay_x + 20, controls_y, overlay_w - 40, 50)
            draw_gradient_rect(screen, controls_rect, (30, 35, 45), (25, 30, 38))
            pygame.draw.rect(screen, (60, 70, 85), controls_rect, 1, border_radius=8)
            
            restart_text = small.render('R - Перезапуск | Esc - Выход', True, (200, 210, 220))
            restart_x = overlay_x + (overlay_w - restart_text.get_width()) // 2
            screen.blit(restart_text, (restart_x, controls_y + 15))
            
            pygame.display.flip()
            continue

        if state.paused:
            # shouldn't happen; we use explicit pause menu
            pygame.time.delay(100)
            continue


        # Smooth falling animation handling
        if input_state.smooth_fall_active and state.current is not None:
            input_state.smooth_fall_timer += dt
            enhanced_gravity = state.fall_interval / (input_state.smooth_fall_speed * 15.0)  # Увеличиваем плавность для лучшей отзывчивости
            
            while input_state.smooth_fall_timer >= enhanced_gravity:
                input_state.smooth_fall_timer -= enhanced_gravity
                moved = try_move(state, 0, +1)
                if moved:
                    state.score += 1  # Начисляем очки за ручное падение
                else:
                    # Останавливаем плавное падение при закреплении фигуры
                    input_state.reset_falling_animation()
                    cleared = lock_piece(state)
                    if cleared > 0:
                        audio.play_sfx('line')
                        score_lines(state, cleared, 'none')
                    break
            
            # Автоматическая остановка плавного падения через разумное время
            if input_state.smooth_fall_double_press:
                current_time = pygame.time.get_ticks() / 1000.0
                # Оптимизированное время остановки для более отзывчивого управления
                timeout = 0.7 if input_state.smooth_fall_speed > 4.0 else 1.0
                if current_time - input_state.smooth_fall_start_time > timeout:
                    input_state.reset_falling_animation()

        # Hard-drop animation handling
        if state.hard_drop_anim and state.current is not None:
            now = pygame.time.get_ticks() / 1000.0
            elapsed = now - state.hard_drop_start_time
            t = min(1.0, elapsed / state.hard_drop_duration) if state.hard_drop_duration > 0 else 1.0
            # ease out for nicer feel
            ease = 1 - (1 - t) * (1 - t)
            draw_y = int(state.hard_drop_start_y + (state.hard_drop_target_y - state.hard_drop_start_y) * ease)
            # If animation finished, set position and lock
            if t >= 1.0:
                state.current.y = state.hard_drop_target_y
                # finalize lock
                lock_piece(state)
                state.hard_drop_anim = False
                fall_accum = 0.0
            else:
                # temporary draw position is stored for rendering
                state._anim_draw_y = draw_y
        # Auto shift left/right
        if input_state.last_direction == 'L' and input_state.left:
            input_state.das_timer += dt
            if input_state.das_timer >= das:
                while input_state.das_timer >= das:
                    if not try_move(state, -1, 0):
                        break
                    input_state.das_timer -= arr
        elif input_state.last_direction == 'R' and input_state.right:
            input_state.das_timer += dt
            if input_state.das_timer >= das:
                while input_state.das_timer >= das:
                    if not try_move(state, +1, 0):
                        break
                    input_state.das_timer -= arr
        else:
            input_state.das_timer = 0.0

        if state.current is None:
            spawn_next(state)
            # Полный сброс всех состояний при создании новой фигуры
            input_state.reset_all()

        # Normal gravity (only if not in special animation modes)
        if not input_state.smooth_fall_active and not getattr(state, 'hard_drop_anim', False):
            gravity = state.fall_interval
            # Улучшенное традиционное мягкое падение
            if (input_state.down and input_state.down_activated_for_current_piece):
                current_duration = input_state.get_key_press_duration('down')
                if current_duration >= input_state.short_press_threshold:
                    # Адаптивное ускорение на основе длительности нажатия
                    if current_duration < input_state.long_press_threshold:
                        gravity = gravity / 7.0  # Средняя скорость
                    else:
                        gravity = gravity / 13.0  # Быстрая скорость для долгого удержания
            
            input_state.gravity_timer += dt
            while input_state.gravity_timer >= gravity:
                input_state.gravity_timer -= gravity
                moved = try_move(state, 0, +1)
                if moved:
                    if (input_state.down and input_state.down_activated_for_current_piece and 
                        input_state.get_key_press_duration('down') >= input_state.short_press_threshold):
                        state.score += 1
                else:
                    # lock
                    cleared = lock_piece(state)
                    if cleared > 0:
                        audio.play_sfx('line')
                        score_lines(state, cleared, 'none')
                        
                        # Проверка целей кампании
                        if state.game_mode == GameMode.CAMPAIGN:
                            if check_campaign_objectives(state):
                                # Уровень пройден!
                                print(f"Поздравляем! Уровень {state.current_campaign_level} пройден!")
                                unlock_next_campaign_level()

        # Постоянное обновление прогресса целей кампании
        if state.game_mode == GameMode.CAMPAIGN:
            update_campaign_progress(state)

        # Draw with enhanced animations
        draw_enhanced_background(screen)
        draw_grid(screen, ORIGIN_X, ORIGIN_Y, state)
        if state.current:
            ghost = ghost_position(state)
            if ghost is not None:
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, ghost, ghost=True)
            # if animating hard-drop, draw the current piece at intermediate y
            if getattr(state, 'hard_drop_anim', False) and hasattr(state, '_anim_draw_y'):
                temp_piece = Piece(state.current.kind, state.current.x, state._anim_draw_y, state.current.r)
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, temp_piece, animate_current=True)
            else:
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, state.current, animate_current=True)
        
        panel_x = ORIGIN_X + PLAY_W + MARGIN
        draw_panel(screen, panel_x, MARGIN, state, font, small, audio)

        pygame.display.flip()

if __name__ == '__main__':
    run()
