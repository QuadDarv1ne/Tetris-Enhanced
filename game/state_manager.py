#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game State Manager for Tetris Enhanced

Manages different game states:
- Menu
- Playing
- Paused
- Game Over
- Settings
"""

import pygame
import time
from typing import Dict, Optional, Callable, Any, Type
from enum import Enum, auto
from dataclasses import dataclass
import logging

logger = logging.getLogger("TetrisEnhanced.StateManager")


class GameStateType(Enum):
    """Типы состояний игры"""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    SETTINGS = auto()
    LEADERBOARD = auto()
    ACHIEVEMENTS = auto()
    TRANSITION = auto()


class StateTransition(Enum):
    """Типы переходов между состояниями"""
    NONE = auto()
    FADE_IN = auto()
    FADE_OUT = auto()
    SLIDE_LEFT = auto()
    SLIDE_RIGHT = auto()
    ZOOM_IN = auto()
    ZOOM_OUT = auto()


@dataclass
class StateConfig:
    """Конфигурация состояния"""
    name: str
    background_color: tuple = (0, 0, 0)
    transition_in: StateTransition = StateTransition.FADE_IN
    transition_out: StateTransition = StateTransition.FADE_OUT
    transition_duration: float = 0.3
    pause_music: bool = False
    clear_screen: bool = True


class GameState:
    """Базовый класс для состояния игры"""
    
    def __init__(self, manager: 'StateManager'):
        self.manager = manager
        self.screen = manager.screen
        self.clock = manager.clock
        self.config = StateConfig(name=self.__class__.__name__)
        self.initialized = False
        self.enter_time = 0.0
        
    def initialize(self):
        """Инициализирует состояние (вызывается один раз)"""
        self.initialized = True
        logger.debug(f"Initialized state: {self.config.name}")
    
    def enter(self, **kwargs):
        """Вызывается при входе в состояние"""
        self.enter_time = time.time()
        logger.debug(f"Entering state: {self.config.name}")
    
    def exit(self):
        """Вызывается при выходе из состояния"""
        logger.debug(f"Exiting state: {self.config.name}")
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Обрабатывает событие
        
        Returns:
            True если событие обработано
        """
        return False
    
    def update(self, dt: float):
        """Обновляет состояние"""
        pass
    
    def render(self, surface: pygame.Surface):
        """Рендерит состояние"""
        if self.config.clear_screen:
            surface.fill(self.config.background_color)
    
    def render_transition(self, surface: pygame.Surface, progress: float):
        """Рендерит переход"""
        pass
    
    def is_transition_complete(self) -> bool:
        """Проверяет завершён ли переход"""
        return True


class MenuState(GameState):
    """Состояние главного меню"""
    
    def __init__(self, manager: 'StateManager'):
        super().__init__(manager)
        self.config = StateConfig(
            name="Menu",
            background_color=(20, 20, 40),
            transition_in=StateTransition.FADE_IN,
            transition_out=StateTransition.FADE_OUT
        )
        self.selected_option = 0
        self.options = []
    
    def initialize(self):
        super().initialize()
        # Инициализация меню
        self.options = [
            "Играть",
            "Таблица рекордов",
            "Достижения",
            "Настройки",
            "Выход"
        ]
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_option_selected(self.selected_option)
                return True
        
        return False
    
    def on_option_selected(self, index: int):
        """Обработка выбора пункта меню"""
        if index == 0:  # Играть
            self.manager.change_state(GameStateType.PLAYING)
        elif index == 1:  # Таблица рекордов
            self.manager.change_state(GameStateType.LEADERBOARD)
        elif index == 2:  # Достижения
            self.manager.change_state(GameStateType.ACHIEVEMENTS)
        elif index == 3:  # Настройки
            self.manager.change_state(GameStateType.SETTINGS)
        elif index == 4:  # Выход
            self.manager.quit()
    
    def render(self, surface: pygame.Surface):
        super().render(surface)
        # Рендер меню будет реализован в основной игре
        # Здесь только заглушка
        font = pygame.font.Font(None, 48)
        title = font.render("TETRIS ENHANCED", True, (255, 255, 255))
        title_rect = title.get_rect(center=(surface.get_width() // 2, 100))
        surface.blit(title, title_rect)


class PlayingState(GameState):
    """Состояние игры"""
    
    def __init__(self, manager: 'StateManager'):
        super().__init__(manager)
        self.config = StateConfig(
            name="Playing",
            background_color=(10, 10, 30),
            transition_in=StateTransition.FADE_IN,
            transition_out=StateTransition.FADE_OUT,
            pause_music=False
        )
        self.game_data: Dict[str, Any] = {}
    
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.game_data = kwargs
        # Инициализация игры будет в основной игре
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        # Обработка игровых событий будет в основной игре
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.manager.change_state(GameStateType.PAUSED)
                return True
            elif event.key == pygame.K_ESCAPE:
                self.manager.change_state(GameStateType.MENU)
                return True
        
        return False


class PausedState(GameState):
    """Состояние паузы"""
    
    def __init__(self, manager: 'StateManager'):
        super().__init__(manager)
        self.config = StateConfig(
            name="Paused",
            background_color=(0, 0, 0),
            transition_in=StateTransition.FADE_IN,
            transition_out=StateTransition.FADE_OUT,
            pause_music=True,
            clear_screen=False  # Не очищаем, показываем игру на фоне
        )
        self.selected_option = 0
    
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.selected_option = 0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
                self.manager.change_state(GameStateType.PLAYING)
                return True
        
        return False
    
    def render(self, surface: pygame.Surface):
        # Рендер полупрозрачного оверлея
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("PAUSED", True, (255, 255, 255))
        text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(text, text_rect)


class GameOverState(GameState):
    """Состояние конца игры"""
    
    def __init__(self, manager: 'StateManager'):
        super().__init__(manager)
        self.config = StateConfig(
            name="Game Over",
            background_color=(40, 20, 20),
            transition_in=StateTransition.FADE_IN,
            transition_out=StateTransition.FADE_OUT
        )
        self.final_score = 0
        self.final_lines = 0
        self.final_level = 0
    
    def enter(self, **kwargs):
        super().enter(**kwargs)
        self.final_score = kwargs.get('score', 0)
        self.final_lines = kwargs.get('lines', 0)
        self.final_level = kwargs.get('level', 1)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.manager.change_state(GameStateType.PLAYING)
                return True
            elif event.key == pygame.K_ESCAPE:
                self.manager.change_state(GameStateType.MENU)
                return True
        
        return False
    
    def render(self, surface: pygame.Surface):
        super().render(surface)
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # Game Over
        text1 = font_large.render("GAME OVER", True, (255, 100, 100))
        rect1 = text1.get_rect(center=(surface.get_width() // 2, 150))
        surface.blit(text1, rect1)
        
        # Score
        score_text = f"Score: {self.final_score:,}"
        text2 = font_medium.render(score_text, True, (255, 255, 255))
        rect2 = text2.get_rect(center=(surface.get_width() // 2, 250))
        surface.blit(text2, rect2)
        
        # Lines
        lines_text = f"Lines: {self.final_lines}"
        text3 = font_medium.render(lines_text, True, (255, 255, 255))
        rect3 = text3.get_rect(center=(surface.get_width() // 2, 310))
        surface.blit(text3, rect3)
        
        # Level
        level_text = f"Level: {self.final_level}"
        text4 = font_medium.render(level_text, True, (255, 255, 255))
        rect4 = text4.get_rect(center=(surface.get_width() // 2, 370))
        surface.blit(text4, rect4)


class SettingsState(GameState):
    """Состояние настроек"""
    
    def __init__(self, manager: 'StateManager'):
        super().__init__(manager)
        self.config = StateConfig(
            name="Settings",
            background_color=(20, 20, 40),
            transition_in=StateTransition.FADE_IN,
            transition_out=StateTransition.FADE_OUT
        )


class LeaderboardState(GameState):
    """Состояние таблицы рекордов"""
    
    def __init__(self, manager: 'StateManager'):
        super().__init__(manager)
        self.config = StateConfig(
            name="Leaderboard",
            background_color=(20, 30, 20),
            transition_in=StateTransition.FADE_IN,
            transition_out=StateTransition.FADE_OUT
        )


class AchievementsState(GameState):
    """Состояние достижений"""
    
    def __init__(self, manager: 'StateManager'):
        super().__init__(manager)
        self.config = StateConfig(
            name="Achievements",
            background_color=(30, 20, 40),
            transition_in=StateTransition.FADE_IN,
            transition_out=StateTransition.FADE_OUT
        )


class StateManager:
    """
    Менеджер состояний игры
    
    Usage:
        state_manager = StateManager(screen, clock)
        
        # Регистрация состояний
        state_manager.register_state(GameStateType.MENU, MenuState)
        state_manager.register_state(GameStateType.PLAYING, PlayingState)
        
        # Запуск
        state_manager.change_state(GameStateType.MENU)
        
        # В игровом цикле
        state_manager.handle_event(event)
        state_manager.update(dt)
        state_manager.render(screen)
    """
    
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        self.screen = screen
        self.clock = clock
        self.states: Dict[GameStateType, GameState] = {}
        self.current_state: Optional[GameState] = None
        self.previous_state: Optional[GameState] = None
        self.running = True
        
        # Переход
        self.transition_state: Optional[GameState] = None
        self.transition_progress = 0.0
        self.transition_duration = 0.3
        self.in_transition = False
    
    def register_state(self, state_type: GameStateType, state_class: Type[GameState]):
        """Регистрирует состояние"""
        self.states[state_type] = state_class(self)
        logger.debug(f"Registered state: {state_type.name}")
    
    def get_state(self, state_type: GameStateType) -> Optional[GameState]:
        """Получает состояние по типу"""
        return self.states.get(state_type)
    
    def change_state(self, new_state_type: GameStateType, **kwargs):
        """Изменяет текущее состояние"""
        if new_state_type not in self.states:
            logger.error(f"State not registered: {new_state_type.name}")
            return
        
        self.previous_state = self.current_state
        
        # Выход из текущего состояния
        if self.current_state:
            self.current_state.exit()
        
        # Вход в новое состояние
        new_state = self.states[new_state_type]
        
        if not new_state.initialized:
            new_state.initialize()
        
        new_state.enter(**kwargs)
        self.current_state = new_state
        
        logger.info(f"Changed state to: {new_state_type.name}")
    
    def handle_event(self, event: pygame.event.Event):
        """Обрабатывает событие"""
        if event.type == pygame.QUIT:
            self.running = False
            return
        
        if self.current_state:
            self.current_state.handle_event(event)
    
    def update(self, dt: float):
        """Обновляет состояние"""
        if self.current_state:
            self.current_state.update(dt)
    
    def render(self):
        """Рендерит текущее состояние"""
        if self.current_state:
            self.current_state.render(self.screen)
    
    def quit(self):
        """Завершает работу менеджера"""
        self.running = False
    
    def is_running(self) -> bool:
        """Проверяет, работает ли менеджер"""
        return self.running


# Глобальный экземпляр (будет создан в основной игре)
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Возвращает глобальный менеджер состояний"""
    global _state_manager
    if _state_manager is None:
        raise RuntimeError("StateManager not initialized")
    return _state_manager


def init_state_manager(screen: pygame.Surface, clock: pygame.time.Clock) -> StateManager:
    """Инициализирует менеджер состояний"""
    global _state_manager
    _state_manager = StateManager(screen, clock)
    return _state_manager
