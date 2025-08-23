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
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

try:
    import pygame
except Exception:
    print("This script requires pygame. Install with: pip install pygame")
    raise

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
WIDTH, HEIGHT = 1024, 768
PLAY_COLS, PLAY_ROWS = 10, 20
BLOCK = 32
PLAY_W, PLAY_H = PLAY_COLS * BLOCK, PLAY_ROWS * BLOCK
MARGIN = 20
PANEL_W = WIDTH - PLAY_W - MARGIN * 3
FPS = 60

# Origin of playfield (centered vertically)
ORIGIN_X = MARGIN
ORIGIN_Y = max(MARGIN, MARGIN + (HEIGHT - 2*MARGIN - PLAY_H) // 2)

# Music directory scanning
MUSIC_DIR = "music"
MUSIC_FILES = []

def scan_music_files(directory):
    """Рекурсивно сканирует директорию в поисках музыкальных файлов."""
    music_files = []
    if os.path.isdir(directory):
        for root, dirs, files in os.walk(directory):
            for fname in sorted(files):
                if fname.lower().endswith(('.mp3', '.ogg', '.wav')):
                    music_files.append(os.path.join(root, fname))
    return music_files

MUSIC_FILES = scan_music_files(MUSIC_DIR)
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

# Colors
BLACK = (18, 18, 20)
BG = (24, 24, 28)
GRID = (40, 40, 48)
WHITE = (240, 240, 250)
DIM = (180, 180, 200)
GHOST = (120, 120, 140)
BUTTON_BG = (40, 40, 45)
BUTTON_BORDER = (10, 10, 12)

# Tetromino colors (I, O, T, S, Z, J, L)
COLORS = {
    'I': (0, 186, 255),
    'O': (255, 214, 0),
    'T': (175, 96, 234),
    'S': (0, 200, 120),
    'Z': (230, 30, 80),
    'J': (0, 120, 255),
    'L': (255, 140, 0),
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
    стакан с заполненными клетками, текущую фигуру,
    очки, уровень, статистику и т.д.
    
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
    
    T-спин - это особый тип поворота T-тетромино,
    когда он зажат с трех сторон и дает дополнительные очки.
    
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
    
    Удаляет все строки, где все клетки заняты,
    а сверху добавляет пустые строки.
    
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
    
    Использует систему "7-bag" - в каждом мешке есть 
    ровно одна фигура каждого типа, перемешанные случайно.
    
    Args:
        state: Текущее состояние игры
    """
    bag = list(SHAPES.keys())
    random.shuffle(bag)
    state.bag.extend(bag)

def spawn_next(state: GameState):
    """
    Создает новую падающую фигуру из очереди.
    
    Заполняет очередь следующих фигур до 5 элементов
    и берёт первую для создания текущей фигуры.
    
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
    
    Использует систему SRS (Super Rotation System) для
    попыток поворота в нескольких позициях.
    
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
    
    Определяет, на сколько клеток вниз можно опустить
    фигуру до столкновения.
    
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

def ghost_position(state: GameState) -> Piece:
    """
    Создает "призрачную" копию текущей фигуры в позиции приземления.
    
    Показывает игроку, где приземлится фигура
    при быстром падении.
    
    Args:
        state: Текущее состояние игры
        
    Returns:
        Копия текущей фигуры в позиции приземления
    """
    d = hard_drop_distance(state)
    p = state.current
    return Piece(p.kind, p.x, p.y + d, p.r)

def hold_swap(state: GameState):
    """
    Выполняет обмен текущей фигуры с зафиксированной (Hold).
    
    Механика Hold позволяет сохранить текущую фигуру
    на потом и использовать её позже.
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
    - Фоновую музыку (плейлист mp3/ogg/wav файлов)
    - Звуковые эффекты (поворот, падение, очистка линий)
    - Переключение между треками
    
    Attributes:
        playlist: Список путей к музыкальным файлам
        index: Индекс текущего трека
        enabled: Включена ли аудиосистема
        sounds: Словарь загруженных звуковых эффектов
    """
    def __init__(self):
        # initialize mixer safely
        try:
            pygame.mixer.init()
        except Exception:
            pass
        # Используем уже просканированный список музыкальных файлов
        self.playlist = [f for f in MUSIC_FILES if os.path.isfile(f)]
        self.index = 0
        self.enabled = len(self.playlist) > 0
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

    def play_current(self):
        """
        Воспроизводит текущий трек из плейлиста.
        Обрабатывает ошибки загрузки файлов.
        """
        if not self.enabled:
            return
        path = self.playlist[self.index]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print('Failed to play', path, e)

    def next(self):
        if not self.enabled:
            return
        self.index = (self.index + 1) % len(self.playlist)
        self.play_current()

    def prev(self):
        if not self.enabled:
            return
        self.index = (self.index - 1) % len(self.playlist)
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

# -------------------- Drawing --------------------
def draw_block(surf, x, y, color, border=True, alpha=None):
    rect = pygame.Rect(x, y, BLOCK-1, BLOCK-1)
    if alpha is not None:
        block = pygame.Surface((BLOCK-1, BLOCK-1), pygame.SRCALPHA)
        c = (*color, alpha)
        pygame.draw.rect(block, c, block.get_rect(), border_radius=6)
        surf.blit(block, rect.topleft)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=6)
    if border:
        pygame.draw.rect(surf, (0,0,0), rect, 2, border_radius=6)

def draw_grid(surf, origin_x, origin_y, state: GameState):
    pygame.draw.rect(surf, (32, 32, 38), (origin_x, origin_y, PLAY_W, PLAY_H), border_radius=12)
    for i in range(PLAY_COLS + 1):
        x = origin_x + i * BLOCK
        pygame.draw.line(surf, GRID, (x, origin_y), (x, origin_y + PLAY_H))
    for j in range(PLAY_ROWS + 1):
        y = origin_y + j * BLOCK
        pygame.draw.line(surf, GRID, (origin_x, y), (origin_x + PLAY_W, y))
    for y in range(PLAY_ROWS):
        for x in range(PLAY_COLS):
            kind = state.grid[y][x]
            if kind:
                color = COLORS[kind]
                draw_block(surf, origin_x + x*BLOCK, origin_y + y*BLOCK, color)

def draw_piece(surf, origin_x, origin_y, piece: Piece, ghost=False):
    if piece is None:
        return
    color = GHOST if ghost else COLORS[piece.kind]
    for x, y in piece.cells():
        if y >= 0:
            draw_block(surf, origin_x + x*BLOCK, origin_y + y*BLOCK, color, border=not ghost, alpha=120 if ghost else None)

def draw_panel(surf, origin_x, origin_y, state: GameState, font, small, audio: AudioManager):
    title = font.render("TETRIS", True, WHITE)
    surf.blit(title, (origin_x, origin_y))
    
    def label(y, text):
        t = small.render(text, True, DIM)
        surf.blit(t, (origin_x, y))
    
    y = origin_y + 50
    
    # Информация о режиме игры
    mode_name = get_mode_display_name(state.game_mode)
    mode_text = small.render(f'Режим: {mode_name}', True, WHITE)
    surf.blit(mode_text, (origin_x, y))
    y += 26
    
    # Информация о кампании (если активна)
    if state.game_mode == GameMode.CAMPAIGN and state.current_campaign_level <= len(CAMPAIGN_LEVELS):
        level_config = CAMPAIGN_LEVELS[state.current_campaign_level - 1]
        campaign_text = small.render(f'Кампания: Уровень {state.current_campaign_level}', True, WHITE)
        surf.blit(campaign_text, (origin_x, y))
        y += 20
        
        level_name_text = small.render(level_config.name, True, (200, 200, 220))
        surf.blit(level_name_text, (origin_x, y))
        y += 25
        
        # Отображение целей
        objectives_title = small.render('Цели:', True, (180, 180, 200))
        surf.blit(objectives_title, (origin_x, y))
        y += 20
        
        for obj in level_config.objectives:
            current_progress = state.campaign_objectives_progress.get(obj.type, 0)
            if obj.type == "time":
                # Отображаем время в формате мин:сек
                mins = current_progress // 60
                secs = current_progress % 60
                target_mins = obj.target // 60
                target_secs = obj.target % 60
                progress_text = f'{mins:02d}:{secs:02d}/{target_mins:02d}:{target_secs:02d}'
            else:
                progress_text = f'{current_progress}/{obj.target}'
            
            # Цвет в зависимости от выполнения
            completed = current_progress >= obj.target
            color = (100, 255, 100) if completed else (255, 255, 255)
            
            obj_text = small.render(f'  {obj.description}: {progress_text}', True, color)
            surf.blit(obj_text, (origin_x, y))
            y += 18
        
        y += 10  # Дополнительный отступ
    
    # Остальная информация
    label(y, f"Score: {state.score}")
    label(y + 26, f"Lines: {state.lines}")
    label(y + 52, f"Level: {state.level}")
    if state.combo >= 1:
        label(y + 78, f"Combo: x{state.combo}")
    nxt = small.render("Next:", True, DIM)
    surf.blit(nxt, (origin_x, y + 120))
    ny = y + 150
    for i, kind in enumerate(state.next_queue[:5]):
        draw_mini(surf, origin_x, ny + i * 70, kind, small)
    hold_lbl = small.render("Hold:", True, DIM)
    surf.blit(hold_lbl, (origin_x, y + 120 + 5 * 70))
    draw_mini(surf, origin_x, y + 120 + 5 * 70 + 30, state.hold, small)
    help_y = HEIGHT - 160
    for i, line in enumerate([
        "← → : Move",
        "↓ : Smooth fall (2x fast)",
        "Space : Smooth/Hard drop",
        "Z / ↑ : Rotate",
        "X : Counter-rotate",
        "C/Shift : Hold",
        "P/Esc : Pause, R : Restart",
    ]):
        t = small.render(line, True, (150, 150, 165))
        surf.blit(t, (origin_x, help_y + i * 18))
    # music info
    if audio.enabled:
        txt = small.render(f"Music: {os.path.basename(audio.playlist[audio.index])}", True, DIM)
        surf.blit(txt, (origin_x, help_y - 26))

def draw_mini(surf, origin_x, origin_y, kind: Optional[str], small):
    box = pygame.Rect(origin_x, origin_y, PANEL_W-10, 80)
    pygame.draw.rect(surf, (32, 32, 36), box, border_radius=10)
    pygame.draw.rect(surf, (0,0,0), box, 2, border_radius=10)
    if not kind:
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
    scale = 20
    offset_x = origin_x + 10 + (PANEL_W - 20 - w*scale) // 2
    offset_y = origin_y + 8 + (60 - 16 - h*scale) // 2
    for i, j in cells:
        x = (i - minx) * scale
        y = (j - miny) * scale
        rect = pygame.Rect(offset_x + x, offset_y + y, scale-1, scale-1)
        pygame.draw.rect(surf, COLORS[kind], rect, border_radius=4)
        pygame.draw.rect(surf, (0,0,0), rect, 1, border_radius=4)

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

def draw_button(surface, rect: pygame.Rect, text: str, font, hover=False):
    color = (70, 70, 74) if hover else BUTTON_BG
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, BUTTON_BORDER, rect, 2, border_radius=8)
    txt = font.render(text, True, WHITE)
    surface.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2, rect.y + (rect.h - txt.get_height()) // 2))

def mode_selection_menu(screen, clock, font, small, audio: AudioManager):
    """Меню выбора игрового режима"""
    selected_mode = 0
    modes = list(GameMode)
    
    while True:
        dt = clock.tick(FPS) / 1000.0
        
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
        
        # Отрисовка
        screen.fill(BG)
        
        # Заголовок
        title = font.render('Выберите режим игры', True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        
        # Опции режимов
        y_start = 200
        for i, mode in enumerate(modes):
            config = GAME_MODE_CONFIGS[mode]
            color = WHITE if i == selected_mode else DIM
            
            # Название режима
            mode_text = font.render(config.name, True, color)
            x = WIDTH // 2 - mode_text.get_width() // 2
            y = y_start + i * 120
            
            # Подсветка выбранного режима
            if i == selected_mode:
                highlight_rect = pygame.Rect(x - 20, y - 10, mode_text.get_width() + 40, mode_text.get_height() + 20)
                pygame.draw.rect(screen, (40, 40, 50), highlight_rect, border_radius=10)
                pygame.draw.rect(screen, (100, 100, 120), highlight_rect, 2, border_radius=10)
            
            screen.blit(mode_text, (x, y))
            
            # Описание режима
            desc_text = small.render(config.description, True, DIM)
            desc_x = WIDTH // 2 - desc_text.get_width() // 2
            screen.blit(desc_text, (desc_x, y + 35))
            
            # Дополнительная информация
            if mode == GameMode.CAMPAIGN:
                info_text = small.render('Последовательное прохождение уровней', True, (120, 120, 140))
            elif mode == GameMode.ENDLESS_IMMERSIVE:
                info_text = small.render('Увеличивающаяся сложность, высокие очки', True, (120, 120, 140))
            else:  # ENDLESS_RELAXED
                info_text = small.render('Медленный темп, ограниченная скорость', True, (120, 120, 140))
            
            info_x = WIDTH // 2 - info_text.get_width() // 2
            screen.blit(info_text, (info_x, y + 55))
        
        # Инструкции
        controls_text = small.render('↑↓ - выбор, Enter - подтвердить, Esc - выход', True, DIM)
        screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT - 50))
        
        pygame.display.flip()

def campaign_level_selection_menu(screen, clock, font, small, audio: AudioManager):
    """Меню выбора уровня кампании"""
    selected_level = 0
    available_levels = [level for level in CAMPAIGN_LEVELS if level.unlocked]
    
    if not available_levels:
        available_levels = [CAMPAIGN_LEVELS[0]]  # Первый уровень всегда доступен
    
    while True:
        dt = clock.tick(FPS) / 1000.0
        
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
        
        # Отрисовка
        screen.fill(BG)
        
        # Заголовок
        title = font.render('Выберите уровень кампании', True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        
        # Уровни
        y_start = 150
        for i, level in enumerate(available_levels):
            color = WHITE if i == selected_level else DIM
            
            # Название уровня
            level_text = font.render(f"Уровень {level.level_num}: {level.name}", True, color)
            x = WIDTH // 2 - level_text.get_width() // 2
            y = y_start + i * 100
            
            # Подсветка
            if i == selected_level:
                highlight_rect = pygame.Rect(x - 15, y - 8, level_text.get_width() + 30, level_text.get_height() + 16)
                pygame.draw.rect(screen, (40, 40, 50), highlight_rect, border_radius=8)
                pygame.draw.rect(screen, (100, 100, 120), highlight_rect, 2, border_radius=8)
            
            screen.blit(level_text, (x, y))
            
            # Описание
            desc_text = small.render(level.description, True, DIM)
            desc_x = WIDTH // 2 - desc_text.get_width() // 2
            screen.blit(desc_text, (desc_x, y + 25))
            
            # Цели
            objectives_text = small.render(' | '.join([obj.description for obj in level.objectives]), True, (120, 120, 140))
            obj_x = WIDTH // 2 - objectives_text.get_width() // 2
            screen.blit(objectives_text, (obj_x, y + 45))
        
        # Инструкции
        controls_text = small.render('↑↓ - выбор, Enter - начать, Esc - назад', True, DIM)
        screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT - 50))
        
        pygame.display.flip()

def start_menu(screen, clock, font, small, audio: AudioManager):
    selected_level = 1
    music_index = audio.index if audio.enabled else -1
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
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
                if ev.key == pygame.K_UP:
                    if audio.enabled:
                        music_index = (music_index - 1) % len(audio.playlist)
        screen.fill(BG)
        title = font.render('TETRIS', True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))
        info = small.render('Выберите начальный уровень (← →) и музыку (↑ ↓). Enter=Старт', True, DIM)
        screen.blit(info, (WIDTH//2 - info.get_width()//2, 120))
        lvl_txt = font.render(f'Level {selected_level}', True, WHITE)
        screen.blit(lvl_txt, (WIDTH//2 - lvl_txt.get_width()//2, 200))
        if audio.enabled and music_index >= 0:
            music_txt = small.render(f'Music: {os.path.basename(audio.playlist[music_index])}', True, DIM)
        else:
            music_txt = small.render('Music: (none found)', True, DIM)
        screen.blit(music_txt, (WIDTH//2 - music_txt.get_width()//2, 260))
        start_hint = small.render('Press Enter to start', True, (200,200,200))
        screen.blit(start_hint, (WIDTH//2 - start_hint.get_width()//2, HEIGHT - 80))
        pygame.display.flip()
    return selected_level, music_index

def pause_menu(screen, clock, font, small, audio: AudioManager, state: GameState):
    # returns action: 'resume' or 'quit' or None
    w = 420; h = 360
    rx = ORIGIN_X + (PLAY_W - w)//2
    ry = ORIGIN_Y + (PLAY_H - h)//2
    bigfont = pygame.font.SysFont('consolas,monospace', 28, bold=True)
    buttons = [
        ('Продолжить', 'resume'),
        ('Сохранить', 'save'),
        ('Загрузить', 'load'),
        ('След. музыка', 'next'),
        ('Пред. музыка', 'prev'),
        ('Выйти', 'quit'),
    ]
    btn_rects = []
    for i, (t, a) in enumerate(buttons):
        bx = rx + 30
        by = ry + 40 + i * 50
        br = button_rect(bx, by, w-60, 40)
        btn_rects.append((br, a, t))
    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_p:
                    return 'resume'
                if ev.key == pygame.K_ESCAPE:
                    return 'resume'  # ESC закрывает меню паузы
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for rect, action, text in btn_rects:
                    if rect.collidepoint(mx, my):
                        if action == 'resume':
                            return 'resume'
                        if action == 'save':
                            save_game(state)
                        if action == 'load':
                            loaded = load_game()
                            if loaded:
                                return ('load', loaded)
                        if action == 'next':
                            audio.next();
                        if action == 'prev':
                            audio.prev();
                        if action == 'quit':
                            return 'quit'
        # draw overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((20, 20, 24, 220))
        screen.blit(overlay, (rx, ry))
        title = bigfont.render('ПАУЗА', True, WHITE)
        screen.blit(title, (rx + (w - title.get_width())//2, ry + 6))
        for rect, action, text in btn_rects:
            mx, my = pygame.mouse.get_pos()
            hover = rect.collidepoint(mx, my)
            draw_button(screen, rect, text, small, hover=hover)
        pygame.display.flip()

# -------------------- Game loop --------------------
def new_game(start_level=1, game_mode=GameMode.ENDLESS_IMMERSIVE, campaign_level=1) -> GameState:
    """Создаёт новую игру с указанным режимом"""
    state = GameState()
    state.level = start_level
    initialize_game_mode(state, game_mode, campaign_level)
    refill_bag(state)
    spawn_next(state)
    return state

def run():
    pygame.init()
    pygame.display.set_caption('Tetris Enhanced')
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', 48, bold=True)
    small = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', 20)

    audio = AudioManager()

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
            return run()
        # Музыка для кампании
        start_level, music_choice = start_menu(screen, clock, font, small, audio)
    else:
        # Обычное стартовое меню для бесконечных режимов
        start_level, music_choice = start_menu(screen, clock, font, small, audio)
    
    if audio.enabled and music_choice >= 0:
        audio.index = music_choice
        audio.play_current()
    elif audio.enabled:
        audio.play_current()

    state = new_game(start_level, selected_mode, campaign_level)

    # Используем класс InputState вместо локальных переменных
    input_state = InputState()
    das = 0.12  # Увеличиваем задержку для менее чувствительного управления влево/вправо
    arr = 0.035  # Увеличиваем интервал повтора для более медленного автоповтора

    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == MUSIC_END_EVENT:
                audio.next()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q:
                    pygame.quit(); sys.exit(0)
                if ev.key in (pygame.K_p, pygame.K_ESCAPE):
                    # pause menu
                    action = pause_menu(screen, clock, font, small, audio, state)
                    if action == 'resume' or action == None:
                        pass
                    elif action == 'quit':
                        pygame.quit(); sys.exit(0)
                    elif isinstance(action, tuple) and action[0] == 'load':
                        # replace state with loaded
                        loaded = action[1]
                        state = loaded
                if ev.key == pygame.K_r:
                    state = new_game(start_level)
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
            screen.fill(BG)
            draw_grid(screen, ORIGIN_X, ORIGIN_Y, state)
            if state.current:
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, state.current)
            panel_x = ORIGIN_X + PLAY_W + MARGIN
            draw_panel(screen, panel_x, MARGIN, state, font, small, audio)
            go_txt = font.render('GAME OVER', True, (255, 80, 80))
            screen.blit(go_txt, (MARGIN + (PLAY_W - go_txt.get_width()) // 2, HEIGHT // 2 - 24))
            sub = small.render('Press R to Restart, Esc to Quit', True, DIM)
            screen.blit(sub, (MARGIN + (PLAY_W - sub.get_width()) // 2, HEIGHT // 2 + 10))
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

        # Draw
        screen.fill(BG)
        draw_grid(screen, ORIGIN_X, ORIGIN_Y, state)
        if state.current:
            ghost = ghost_position(state)
            draw_piece(screen, ORIGIN_X, ORIGIN_Y, ghost, ghost=True)
            # if animating hard-drop, draw the current piece at intermediate y
            if getattr(state, 'hard_drop_anim', False) and hasattr(state, '_anim_draw_y'):
                temp_piece = Piece(state.current.kind, state.current.x, state._anim_draw_y, state.current.r)
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, temp_piece)
            else:
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, state.current)

        panel_x = ORIGIN_X + PLAY_W + MARGIN
        draw_panel(screen, panel_x, MARGIN, state, font, small, audio)

        pygame.display.flip()

if __name__ == '__main__':
    run()
