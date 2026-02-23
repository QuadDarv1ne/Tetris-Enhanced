#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game Integration Module for Tetris Enhanced

Интегрирует все системы (частицы, достижения, ежедневные испытания) 
в основной игровой цикл.
"""

import pygame
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("TetrisEnhanced.Integration")


class GameIntegration:
    """
    Класс для интеграции всех систем игры
    
    Usage:
        integration = GameIntegration()
        
        # В игровом цикле:
        integration.update(dt, game_state)
        integration.draw(screen)
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Импортируем системы
        try:
            from game import get_particle_system, init_particle_system
            self.particle_system = init_particle_system(max_particles=2000)
            logger.info("Particle system initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize particle system: {e}")
            self.particle_system = None
        
        try:
            from game import get_achievements_manager, init_achievements_manager
            self.achievements = init_achievements_manager()
            logger.info("Achievements system initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize achievements: {e}")
            self.achievements = None
        
        try:
            from game import get_daily_challenges_manager, init_daily_challenges_manager
            self.daily_challenges = init_daily_challenges_manager()
            logger.info("Daily challenges initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize daily challenges: {e}")
            self.daily_challenges = None
        
        try:
            from game import get_leaderboard_manager, init_leaderboard_manager
            self.leaderboard = init_leaderboard_manager()
            logger.info("Leaderboard initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize leaderboard: {e}")
            self.leaderboard = None
    
    def update(self, dt: float, game_state: Any):
        """
        Обновляет все системы
        
        Args:
            dt: Дельта времени
            game_state: Объект состояния игры
        """
        # Обновляем частицы
        if self.particle_system:
            self.particle_system.update(dt)
        
        # Обновляем достижения
        if self.achievements and game_state:
            stats = self._extract_stats(game_state)
            self.achievements.update_stats(stats)
        
        # Обновляем ежедневные испытания
        if self.daily_challenges and game_state:
            stats = self._extract_stats(game_state)
            self.daily_challenges.update_progress(stats)
    
    def draw(self, surface: pygame.Surface):
        """Рисует все эффекты"""
        if self.particle_system:
            self.particle_system.draw(surface)
    
    def emit_line_clear(self, x: int, y: int, width: int, lines: int = 1):
        """Эффект очистки линии"""
        if self.particle_system:
            self.particle_system.emit_line_clear(x, y, width, lines)
    
    def emit_tetris(self, x: int, y: int):
        """Эффект тетриса (4 линии)"""
        if self.particle_system:
            self.particle_system.emit_at(x, y, 'tetris')
    
    def emit_combo(self, x: int, y: int):
        """Эффект комбо"""
        if self.particle_system:
            self.particle_system.emit_at(x, y, 'combo')
    
    def emit_t_spin(self, x: int, y: int):
        """Эффект T-спина"""
        if self.particle_system:
            self.particle_system.emit_at(x, y, 't_spin')
    
    def emit_level_up(self, x: int, y: int):
        """Эффект повышения уровня"""
        if self.particle_system:
            self.particle_system.emit_at(x, y, 'level_up')
    
    def emit_drop(self, x: int, y: int):
        """Эффект падения фигуры"""
        if self.particle_system:
            self.particle_system.emit_at(x, y, 'drop')
    
    def emit_rotate(self, x: int, y: int):
        """Эффект поворота фигуры"""
        if self.particle_system:
            self.particle_system.emit_at(x, y, 'rotate')
    
    def _extract_stats(self, game_state: Any) -> Dict[str, Any]:
        """Извлекает статистику из состояния игры"""
        if not game_state:
            return {}
        
        stats = {}
        
        # Базовая статистика
        if hasattr(game_state, 'score'):
            stats['score'] = game_state.score
        if hasattr(game_state, 'lines'):
            stats['lines_cleared'] = game_state.lines
        if hasattr(game_state, 'level'):
            stats['level'] = game_state.level
        if hasattr(game_state, 'combo'):
            stats['max_combo'] = max(stats.get('max_combo', 0), game_state.combo)
        if hasattr(game_state, 'tetrises'):
            stats['tetrises'] = game_state.tetrises
        if hasattr(game_state, 't_spins'):
            stats['t_spins'] = game_state.t_spins
        
        return stats
    
    def add_score(
        self,
        score: int,
        lines: int,
        level: int,
        game_mode: str = "endless",
        time_played: float = 0.0,
        combo_max: int = 0,
        tetris_count: int = 0,
        t_spin_count: int = 0
    ):
        """Добавляет счёт в таблицу рекордов"""
        if self.leaderboard:
            self.leaderboard.add_score(
                score=score,
                lines=lines,
                level=level,
                game_mode=game_mode,
                time_played=time_played,
                combo_max=combo_max,
                tetris_count=tetris_count,
                t_spin_count=t_spin_count
            )
    
    def save_all(self):
        """Сохраняет все системы"""
        if self.achievements:
            self.achievements.save()
        if self.daily_challenges:
            self.daily_challenges.save()
        if self.leaderboard:
            self.leaderboard.save()
    
    def get_achievements_manager(self):
        """Возвращает менеджер достижений"""
        return self.achievements
    
    def get_daily_challenges_manager(self):
        """Возвращает менеджер ежедневных испытаний"""
        return self.daily_challenges
    
    def get_leaderboard_manager(self):
        """Возвращает менеджер таблицы рекордов"""
        return self.leaderboard
    
    def get_particle_system(self):
        """Возвращает систему частиц"""
        return self.particle_system


# Глобальный экземпляр
_integration: Optional[GameIntegration] = None


def get_integration() -> GameIntegration:
    """Возвращает глобальный экземпляр интеграции"""
    global _integration
    if _integration is None:
        raise RuntimeError("GameIntegration not initialized")
    return _integration


def init_integration(screen_width: int, screen_height: int) -> GameIntegration:
    """Инициализирует глобальный экземпляр интеграции"""
    global _integration
    _integration = GameIntegration(screen_width, screen_height)
    return _integration
