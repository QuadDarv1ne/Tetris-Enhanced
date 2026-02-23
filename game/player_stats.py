#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Player Statistics Module for Tetris Enhanced

Отслеживает детальную статистику игрока:
- Общее время игры
- Количество сыгранных игр
- Статистика по фигурам
- Точность и эффективность
- Рекорды и достижения
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger("TetrisEnhanced.PlayerStats")


@dataclass
class PieceStatistics:
    """Статистика по использованию фигур"""
    pieces_placed: int = 0
    rotations_performed: int = 0
    hard_drops: int = 0
    soft_drops: int = 0
    
    # Для каждой фигуры отдельно
    piece_counts: Dict[str, int] = field(default_factory=dict)
    piece_rotations: Dict[str, int] = field(default_factory=dict)
    piece_drops: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PieceStatistics':
        return cls(**data)
    
    def update(self, piece_kind: str, rotations: int = 0, is_hard_drop: bool = False, 
               is_soft_drop: bool = False):
        """Обновляет статистику"""
        self.pieces_placed += 1
        
        # Статистика по типу фигуры
        self.piece_counts[piece_kind] = self.piece_counts.get(piece_kind, 0) + 1
        self.piece_rotations[piece_kind] = self.piece_rotations.get(piece_kind, 0) + rotations
        if is_hard_drop:
            self.piece_drops[piece_kind] = self.piece_drops.get(piece_kind, 0) + 1
        
        self.rotations_performed += rotations
        if is_hard_drop:
            self.hard_drops += 1
        if is_soft_drop:
            self.soft_drops += 1


@dataclass
class SessionStatistics:
    """Статистика текущей сессии"""
    start_time: float = field(default_factory=time.time)
    games_played: int = 0
    games_won: int = 0
    total_score: int = 0
    total_lines: int = 0
    total_time: float = 0.0
    
    best_score: int = 0
    best_lines: int = 0
    best_level: int = 0
    
    tetrises: int = 0
    t_spins: int = 0
    combos: int = 0
    max_combo: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionStatistics':
        return cls(**data)
    
    def update(self, score: int, lines: int, level: int, 
               tetris: bool = False, t_spin: bool = False, combo: int = 0):
        """Обновляет статистику сессии"""
        self.games_played += 1
        self.total_score += score
        self.total_lines += lines
        
        if score > self.best_score:
            self.best_score = score
        if lines > self.best_lines:
            self.best_lines = lines
        if level > self.best_level:
            self.best_level = level
        
        if tetris:
            self.tetrises += 1
        if t_spin:
            self.t_spins += 1
        if combo > 0:
            self.combos += 1
            if combo > self.max_combo:
                self.max_combo = combo


@dataclass 
class CareerStatistics:
    """Общая карьерная статистика"""
    total_games: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_playtime: float = 0.0  # секунды
    
    total_score: int = 0
    total_lines: int = 0
    total_pieces: int = 0
    
    best_score: int = 0
    best_lines: int = 0
    best_level: int = 0
    best_combo: int = 0
    
    total_tetrises: int = 0
    total_t_spins: int = 0
    total_perfect_clears: int = 0
    
    # По режимам игры
    games_by_mode: Dict[str, int] = field(default_factory=dict)
    best_by_mode: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Статистика по фигурам
    piece_stats: PieceStatistics = field(default_factory=PieceStatistics)
    
    # Достижения
    achievements_unlocked: int = 0
    achievements_total: int = 0
    
    # Серии
    current_streak: int = 0
    best_streak: int = 0
    
    # История игр
    game_history: List[Dict[str, Any]] = field(default_factory=list)
    max_history_size: int = 100
    
    # Статистика сессий
    sessions_played: int = 0
    total_session_time: float = 0.0
    
    def to_dict(self) -> dict:
        data = asdict(self)
        # Преобразуем game_history, ограничивая размер
        data['game_history'] = self.game_history[-self.max_history_size:]
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CareerStatistics':
        # Обрабатываем вложенные объекты
        piece_stats_data = data.pop('piece_stats', {})
        piece_stats = PieceStatistics.from_dict(piece_stats_data) if piece_stats_data else PieceStatistics()
        
        stats = cls(**data)
        stats.piece_stats = piece_stats
        return stats
    
    def update(self, score: int, lines: int, level: int, game_mode: str = "endless",
               tetris_count: int = 0, t_spin_count: int = 0, combo_max: int = 0,
               time_played: float = 0.0, is_win: bool = True,
               piece_stats: Optional[PieceStatistics] = None):
        """Обновляет карьерную статистику"""
        self.total_games += 1
        
        if is_win:
            self.total_wins += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            self.total_losses += 1
            self.current_streak = 0
        
        self.total_score += score
        self.total_lines += lines
        self.total_playtime += time_played
        
        if piece_stats:
            self.total_pieces += piece_stats.pieces_placed
            # Объединяем статистику по фигурам
            for kind, count in piece_stats.piece_counts.items():
                self.piece_stats.piece_counts[kind] = \
                    self.piece_stats.piece_counts.get(kind, 0) + count
        
        # Обновляем рекорды
        if score > self.best_score:
            self.best_score = score
        if lines > self.best_lines:
            self.best_lines = lines
        if level > self.best_level:
            self.best_level = level
        if combo_max > self.best_combo:
            self.best_combo = combo_max
        
        self.total_tetrises += tetris_count
        self.total_t_spins += t_spin_count
        
        # Статистика по режимам
        self.games_by_mode[game_mode] = self.games_by_mode.get(game_mode, 0) + 1
        
        if game_mode not in self.best_by_mode:
            self.best_by_mode[game_mode] = {
                'score': score,
                'lines': lines,
                'level': level
            }
        else:
            # Для спринта сравниваем время
            if game_mode == "sprint":
                # Меньше время - лучше
                pass
            else:
                if score > self.best_by_mode[game_mode]['score']:
                    self.best_by_mode[game_mode] = {
                        'score': score,
                        'lines': lines,
                        'level': level
                    }
        
        # Добавляем в историю
        self.game_history.append({
            'date': datetime.now().isoformat(),
            'score': score,
            'lines': lines,
            'level': level,
            'mode': game_mode,
            'win': is_win,
            'tetrises': tetris_count,
            't_spins': t_spin_count,
            'combo': combo_max,
            'time': time_played
        })
        
        # Ограничиваем размер истории
        if len(self.game_history) > self.max_history_size:
            self.game_history = self.game_history[-self.max_history_size:]
    
    def get_win_rate(self) -> float:
        """Процент побед"""
        if self.total_games == 0:
            return 0.0
        return (self.total_wins / self.total_games) * 100
    
    def get_avg_score(self) -> float:
        """Средний счёт"""
        if self.total_games == 0:
            return 0.0
        return self.total_score / self.total_games
    
    def get_avg_lines(self) -> float:
        """Среднее количество линий за игру"""
        if self.total_games == 0:
            return 0.0
        return self.total_lines / self.total_games
    
    def get_total_playtime_formatted(self) -> str:
        """Форматирует общее время игры"""
        hours = int(self.total_playtime // 3600)
        minutes = int((self.total_playtime % 3600) // 60)
        seconds = int(self.total_playtime % 60)
        return f"{hours}ч {minutes}м {seconds}с"
    
    def get_most_used_piece(self) -> Optional[str]:
        """Возвращает наиболее используемую фигуру"""
        if not self.piece_stats.piece_counts:
            return None
        return max(self.piece_stats.piece_counts.items(), key=lambda x: x[1])[0]
    
    def get_efficiency(self) -> float:
        """
        Возвращает коэффициент эффективности
        (средние очки за линию)
        """
        if self.total_lines == 0:
            return 0.0
        return self.total_score / self.total_lines


class PlayerStatisticsManager:
    """
    Менеджер статистики игрока
    
    Features:
    - Track career statistics
    - Session tracking
    - Piece usage statistics
    - Game history
    - Persistent storage
    """
    
    def __init__(self, save_path: str = "player_statistics.json"):
        self.save_path = save_path
        
        # Карьерная статистика
        self.career = CareerStatistics()
        
        # Текущая сессия
        self.session = SessionStatistics()
        
        # Текущая игра
        self.current_game_stats: Optional[PieceStatistics] = None
        
        # Загрузка
        self.load()
    
    def start_game(self):
        """Начинает новую игру"""
        self.current_game_stats = PieceStatistics()
        logger.info("New game started")
    
    def end_game(self, score: int, lines: int, level: int, game_mode: str = "endless",
                 tetris_count: int = 0, t_spin_count: int = 0, combo_max: int = 0,
                 time_played: float = 0.0, is_win: bool = True):
        """Завершает игру и обновляет статистику"""
        # Обновляем сессию
        self.session.update(score, lines, level, 
                           tetris_count > 0, t_spin_count > 0, combo_max)
        
        # Обновляем карьеру
        self.career.update(
            score=score,
            lines=lines,
            level=level,
            game_mode=game_mode,
            tetris_count=tetris_count,
            t_spin_count=t_spin_count,
            combo_max=combo_max,
            time_played=time_played,
            is_win=is_win,
            piece_stats=self.current_game_stats
        )
        
        # Сбрасываем текущую статистику
        self.current_game_stats = None
        
        logger.info(f"Game ended: score={score}, lines={lines}, level={level}")
    
    def record_piece_placement(self, piece_kind: str, rotations: int = 0,
                               is_hard_drop: bool = False, is_soft_drop: bool = False):
        """Записывает размещение фигуры"""
        if self.current_game_stats:
            self.current_game_stats.update(
                piece_kind, rotations, is_hard_drop, is_soft_drop
            )
    
    def record_tetris(self):
        """Записывает тетрис (4 линии)"""
        if self.current_game_stats:
            self.current_game_stats.tetrises = \
                self.current_game_stats.get('tetrises', 0) + 1
    
    def record_t_spin(self):
        """Записывает T-спин"""
        if self.current_game_stats:
            self.current_game_stats.t_spins = \
                self.current_game_stats.get('t_spins', 0) + 1
    
    def get_career_stats(self) -> CareerStatistics:
        """Возвращает карьерную статистику"""
        return self.career
    
    def get_session_stats(self) -> SessionStatistics:
        """Возвращает статистику сессии"""
        return self.session
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку статистики"""
        return {
            'total_games': self.career.total_games,
            'win_rate': f"{self.career.get_win_rate():.1f}%",
            'best_score': self.career.best_score,
            'best_lines': self.career.best_lines,
            'total_playtime': self.career.get_total_playtime_formatted(),
            'avg_score': f"{self.career.get_avg_score():.1f}",
            'avg_lines': f"{self.career.get_avg_lines():.1f}",
            'efficiency': f"{self.career.get_efficiency():.1f}",
            'total_tetrises': self.career.total_tetrises,
            'total_t_spins': self.career.total_t_spins,
            'best_streak': self.career.best_streak,
            'most_used_piece': self.career.get_most_used_piece(),
            'achievements': f"{self.career.achievements_unlocked}/{self.career.achievements_total}"
        }
    
    def save(self):
        """Сохраняет статистику"""
        try:
            data = {
                'version': '1.0',
                'career': self.career.to_dict(),
                'session': self.session.to_dict(),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Player statistics saved to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save player statistics: {e}")
    
    def load(self):
        """Загружает статистику"""
        if not os.path.exists(self.save_path):
            logger.info("No player statistics file found, starting fresh")
            return
        
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загружаем карьерную статистику
            career_data = data.get('career', {})
            if career_data:
                self.career = CareerStatistics.from_dict(career_data)
            
            # Загружаем сессию
            session_data = data.get('session', {})
            if session_data:
                self.session = SessionStatistics.from_dict(session_data)
            
            logger.info(f"Player statistics loaded from {self.save_path}")
            logger.info(f"Total games: {self.career.total_games}")
            
        except Exception as e:
            logger.error(f"Failed to load player statistics: {e}")
    
    def reset_career(self):
        """Сбрасывает карьерную статистику"""
        self.career = CareerStatistics()
        logger.info("Career statistics reset")
    
    def reset_session(self):
        """Сбрасывает статистику сессии"""
        self.session = SessionStatistics()
        logger.info("Session statistics reset")


# Глобальный экземпляр
_player_stats_manager: Optional[PlayerStatisticsManager] = None


def get_player_statistics_manager() -> PlayerStatisticsManager:
    """Возвращает глобальный менеджер статистики"""
    global _player_stats_manager
    if _player_stats_manager is None:
        _player_stats_manager = PlayerStatisticsManager()
    return _player_stats_manager


def init_player_statistics_manager(save_path: str = "player_statistics.json") -> PlayerStatisticsManager:
    """Инициализирует менеджер статистики"""
    global _player_stats_manager
    _player_stats_manager = PlayerStatisticsManager(save_path=save_path)
    return _player_stats_manager
