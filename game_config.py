#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game configuration module for Tetris Enhanced
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Tuple

logger = logging.getLogger("TetrisEnhanced.Config")

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
    
    # Новые настройки интерфейса и доступности
    ui_theme: str = "dark"  # "dark", "light"
    enable_high_contrast: bool = False  # Режим высокого контраста для лучшей доступности
    text_size_multiplier: float = 1.0  # Множитель размера текста для лучшей читаемости
    enable_text_shadows: bool = True  # Тени текста для лучшей читаемости
    enable_motion_effects: bool = True  # Анимации и эффекты движения
    
    @classmethod
    def load_from_file(cls, filename: str = "config.json") -> "GameConfig":
        """Загружает конфигурацию из файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Configuration loaded from {filename}")
                return cls(**data)
            else:
                logger.warning(f"Configuration file {filename} not found, using defaults")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {filename}: {e}")
        except Exception as e:
            logger.error(f"Error loading configuration from {filename}: {e}")
        logger.info("Using default configuration")
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
                'game_field_cols': self.game_field_cols,
                'game_field_rows': self.game_field_rows,
                'block_size_base': self.block_size_base,
                'enable_audio': self.enable_audio,
                'music_volume': self.music_volume,
                'sound_volume': self.sound_volume,
                'enable_animations': self.enable_animations,
                'enable_shadows': self.enable_shadows,
                'render_quality': self.render_quality,
                'cache_size_multiplier': self.cache_size_multiplier,
                'auto_save_enabled': self.auto_save_enabled,
                'auto_save_interval': self.auto_save_interval,
                'show_debug_info': self.show_debug_info,
                'ui_theme': self.ui_theme,
                'enable_high_contrast': self.enable_high_contrast,
                'text_size_multiplier': self.text_size_multiplier,
                'enable_text_shadows': self.enable_text_shadows,
                'enable_motion_effects': self.enable_motion_effects
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving configuration to {filename}: {e}")

# Глобальная конфигурация
game_config = GameConfig.load_from_file()