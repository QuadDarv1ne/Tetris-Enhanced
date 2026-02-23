#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leaderboard system for Tetris Enhanced

Features:
- Local high scores storage
- Multiple game modes support
- Statistics tracking
- Replay system (optional)
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("TetrisEnhanced.Leaderboard")


class GameMode(Enum):
    """Режимы игры для таблицы рекордов"""
    SPRINT = "sprint"              # 40 линий на время
    ULTRA = "ultra"                # 2 минуты на очки
    MASTER = "master"              # До проигрыша
    ENDLESS = "endless"            # Бесконечный
    CAMPAIGN = "campaign"          # Кампания


@dataclass
class ScoreEntry:
    """Запись в таблице рекордов"""
    player_name: str
    score: int
    lines: int
    level: int
    game_mode: str
    date: str  # ISO format timestamp
    timestamp: float  # Unix timestamp
    
    # Дополнительная статистика
    combo_max: int = 0
    tetris_count: int = 0
    t_spin_count: int = 0
    b2b_count: int = 0  # Back-to-back
    time_played: float = 0.0  # секунды
    
    # Для режима спринт
    time_to_complete: float = 0.0  # секунды
    
    # Хэш для проверки на читерство
    checksum: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScoreEntry':
        return cls(**data)
    
    def calculate_checksum(self) -> str:
        """Вычисляет контрольную сумму для проверки"""
        import hashlib
        data = f"{self.player_name}{self.score}{self.lines}{self.level}{self.timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:8]
    
    def validate(self) -> bool:
        """Проверяет валидность записи"""
        return self.checksum == "" or self.checksum == self.calculate_checksum()
    
    def format_score(self) -> str:
        """Форматирует счёт для отображения"""
        return f"{self.score:,}"
    
    def format_time(self) -> str:
        """Форматирует время для отображения"""
        minutes = int(self.time_played // 60)
        seconds = int(self.time_played % 60)
        return f"{minutes}:{seconds:02d}"


@dataclass
class Leaderboard:
    """Таблица рекордов для одного режима"""
    mode: str
    entries: List[ScoreEntry] = field(default_factory=list)
    max_entries: int = 10
    
    def add_entry(self, entry: ScoreEntry) -> Tuple[bool, int]:
        """
        Добавляет запись в таблицу
        
        Returns:
            (добавлена ли, позиция)
        """
        # Проверяем валидность
        if not entry.validate():
            logger.warning(f"Invalid score entry: {entry.player_name}")
            return False, -1
        
        # Находим позицию
        position = 0
        for i, existing in enumerate(self.entries):
            if self._compare_scores(entry, existing):
                position = i
                break
        else:
            position = len(self.entries)
        
        # Проверяем, попадает ли запись в топ
        if position >= self.max_entries and len(self.entries) >= self.max_entries:
            return False, -1
        
        # Вставляем запись
        self.entries.insert(position, entry)
        
        # Обрезаем до максимального размера
        self.entries = self.entries[:self.max_entries]
        
        return True, position + 1  # Позиции с 1
    
    def _compare_scores(self, a: ScoreEntry, b: ScoreEntry) -> bool:
        """
        Сравнивает два счёта
        
        Returns:
            True если a лучше b
        """
        # Для спринта важнее время
        if a.game_mode == "sprint" and b.game_mode == "sprint":
            if a.lines == b.lines:
                return a.time_to_complete < b.time_to_complete
            return a.lines > b.lines
        
        # Для остальных режимов важнее очки
        if a.score != b.score:
            return a.score > b.score
        
        # При равных очках смотрим на линии
        if a.lines != b.lines:
            return a.lines > b.lines
        
        # При равных линиях смотрим на уровень
        return a.level > b.level
    
    def get_top(self, count: int = 10) -> List[ScoreEntry]:
        """Возвращает топ записей"""
        return self.entries[:count]
    
    def get_position(self, score: int) -> int:
        """Возвращает позицию для данного счёта"""
        for i, entry in enumerate(self.entries):
            if score > entry.score:
                return i + 1
        return len(self.entries) + 1
    
    def clear(self):
        """Очищает таблицу"""
        self.entries.clear()


@dataclass
class PlayerStats:
    """Статистика игрока"""
    total_games: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_score: int = 0
    total_lines: int = 0
    total_time: float = 0.0  # секунды
    
    best_score: int = 0
    best_lines: int = 0
    best_level: int = 0
    best_combo: int = 0
    
    total_tetrises: int = 0
    total_t_spins: int = 0
    total_b2b: int = 0
    
    games_by_mode: Dict[str, int] = field(default_factory=dict)
    best_by_mode: Dict[str, int] = field(default_factory=dict)
    
    # Достижения
    achievements_unlocked: int = 0
    achievements_total: int = 0
    
    # Стreak
    current_streak: int = 0
    best_streak: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerStats':
        return cls(**data)
    
    def update(self, entry: ScoreEntry, is_win: bool = False):
        """Обновляет статистику на основе записи"""
        self.total_games += 1
        if is_win:
            self.total_wins += 1
        else:
            self.total_losses += 1
        
        self.total_score += entry.score
        self.total_lines += entry.lines
        self.total_time += entry.time_played
        
        self.best_score = max(self.best_score, entry.score)
        self.best_lines = max(self.best_lines, entry.lines)
        self.best_level = max(self.best_level, entry.level)
        self.best_combo = max(self.best_combo, entry.combo_max)
        
        self.total_tetrises += entry.tetris_count
        self.total_t_spins += entry.t_spin_count
        self.total_b2b += entry.b2b_count
        
        # Статистика по режимам
        mode = entry.game_mode
        self.games_by_mode[mode] = self.games_by_mode.get(mode, 0) + 1
        
        if mode not in self.best_by_mode:
            self.best_by_mode[mode] = entry.score
        else:
            # Для спринта лучше меньше время
            if mode == "sprint":
                pass  # Нужно сравнивать время
            else:
                self.best_by_mode[mode] = max(self.best_by_mode[mode], entry.score)
        
        # Streak
        if is_win:
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            self.current_streak = 0
    
    def get_win_rate(self) -> float:
        """Возвращает процент побед"""
        if self.total_games == 0:
            return 0.0
        return self.total_wins / self.total_games * 100
    
    def get_avg_score(self) -> float:
        """Возвращает средний счёт"""
        if self.total_games == 0:
            return 0.0
        return self.total_score / self.total_games
    
    def get_avg_lines(self) -> float:
        """Возвращает среднее количество линий"""
        if self.total_games == 0:
            return 0.0
        return self.total_lines / self.total_games


class LeaderboardManager:
    """
    Менеджер таблицы рекордов
    
    Features:
    - Multiple game modes
    - Persistent storage
    - Statistics tracking
    - Export/Import
    """
    
    def __init__(self, save_path: str = "leaderboard.json"):
        self.save_path = save_path
        
        # Таблицы по режимам
        self.leaderboards: Dict[str, Leaderboard] = {}
        
        # Статистика игрока
        self.player_stats = PlayerStats()
        
        # Имя игрока
        self.player_name = "Player"
        
        # Инициализация
        self._init_leaderboards()
        self.load()
    
    def _init_leaderboards(self):
        """Инициализирует таблицы рекордов"""
        for mode in GameMode:
            self.leaderboards[mode.value] = Leaderboard(mode=mode.value)
    
    def add_score(
        self,
        score: int,
        lines: int,
        level: int,
        game_mode: str,
        time_played: float = 0.0,
        combo_max: int = 0,
        tetris_count: int = 0,
        t_spin_count: int = 0,
        b2b_count: int = 0,
        time_to_complete: float = 0.0,
        is_win: bool = True
    ) -> Tuple[bool, int]:
        """
        Добавляет счёт в таблицу рекордов
        
        Returns:
            (добавлен ли, позиция)
        """
        entry = ScoreEntry(
            player_name=self.player_name,
            score=score,
            lines=lines,
            level=level,
            game_mode=game_mode,
            date=datetime.now().isoformat(),
            timestamp=time.time(),
            combo_max=combo_max,
            tetris_count=tetris_count,
            t_spin_count=t_spin_count,
            b2b_count=b2b_count,
            time_played=time_played,
            time_to_complete=time_to_complete
        )
        
        # Вычисляем checksum
        entry.checksum = entry.calculate_checksum()
        
        # Добавляем в таблицу
        if game_mode not in self.leaderboards:
            self.leaderboards[game_mode] = Leaderboard(mode=game_mode)
        
        added, position = self.leaderboards[game_mode].add_entry(entry)
        
        if added:
            # Обновляем статистику
            self.player_stats.update(entry, is_win)
            self.save()
        
        return added, position
    
    def get_leaderboard(self, mode: str) -> Optional[Leaderboard]:
        """Возвращает таблицу для режима"""
        return self.leaderboards.get(mode)
    
    def get_top_scores(self, mode: str, count: int = 10) -> List[ScoreEntry]:
        """Возвращает топ счетов для режима"""
        if mode not in self.leaderboards:
            return []
        return self.leaderboards[mode].get_top(count)
    
    def get_player_rank(self, mode: str, score: int) -> int:
        """Возвращает ранг игрока"""
        if mode not in self.leaderboards:
            return -1
        return self.leaderboards[mode].get_position(score)
    
    def set_player_name(self, name: str):
        """Устанавливает имя игрока"""
        self.player_name = name[:20]  # Ограничиваем длину
    
    def get_stats(self) -> PlayerStats:
        """Возвращает статистику игрока"""
        return self.player_stats
    
    def save(self):
        """Сохраняет таблицу рекордов"""
        try:
            data = {
                'version': '1.0',
                'player_name': self.player_name,
                'player_stats': self.player_stats.to_dict(),
                'leaderboards': {}
            }
            
            for mode, leaderboard in self.leaderboards.items():
                data['leaderboards'][mode] = {
                    'mode': leaderboard.mode,
                    'entries': [e.to_dict() for e in leaderboard.entries]
                }
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Leaderboard saved to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save leaderboard: {e}")
    
    def load(self):
        """Загружает таблицу рекордов"""
        if not os.path.exists(self.save_path):
            logger.info("No leaderboard file found, starting fresh")
            return
        
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загружаем имя игрока
            self.player_name = data.get('player_name', 'Player')
            
            # Загружаем статистику
            stats_data = data.get('player_stats', {})
            if stats_data:
                self.player_stats = PlayerStats.from_dict(stats_data)
            
            # Загружаем таблицы
            for mode, lb_data in data.get('leaderboards', {}).items():
                if mode in self.leaderboards:
                    entries = [ScoreEntry.from_dict(e) for e in lb_data.get('entries', [])]
                    self.leaderboards[mode].entries = entries
            
            logger.info(f"Leaderboard loaded from {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to load leaderboard: {e}")
    
    def export_csv(self, mode: str, filename: str) -> bool:
        """Экспортирует таблицу в CSV"""
        try:
            if mode not in self.leaderboards:
                return False
            
            leaderboard = self.leaderboards[mode]
            
            with open(filename, 'w', encoding='utf-8') as f:
                # Заголовок
                f.write("Rank,Name,Score,Lines,Level,Date,Time Played,Combo,Tetris,T-Spin\n")
                
                # Записи
                for i, entry in enumerate(leaderboard.entries, 1):
                    f.write(f"{i},{entry.player_name},{entry.score},{entry.lines},"
                           f"{entry.level},{entry.date},{entry.format_time()},"
                           f"{entry.combo_max},{entry.tetris_count},{entry.t_spin_count}\n")
            
            logger.info(f"Leaderboard exported to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to export leaderboard: {e}")
            return False
    
    def clear(self, mode: Optional[str] = None):
        """Очищает таблицу (или все таблицы)"""
        if mode:
            if mode in self.leaderboards:
                self.leaderboards[mode].clear()
                logger.info(f"Cleared leaderboard for mode: {mode}")
        else:
            for lb in self.leaderboards.values():
                lb.clear()
            self.player_stats = PlayerStats()
            logger.info("Cleared all leaderboards")
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку статистики"""
        return {
            'player_name': self.player_name,
            'total_games': self.player_stats.total_games,
            'win_rate': f"{self.player_stats.get_win_rate():.1f}%",
            'best_score': self.player_stats.best_score,
            'best_lines': self.player_stats.best_lines,
            'total_tetrises': self.player_stats.total_tetrises,
            'total_t_spins': self.player_stats.total_t_spins,
            'best_streak': self.player_stats.best_streak,
            'achievements': f"{self.player_stats.achievements_unlocked}/{self.player_stats.achievements_total}"
        }


# Глобальный экземпляр
_leaderboard_manager: Optional[LeaderboardManager] = None


def get_leaderboard_manager() -> LeaderboardManager:
    """Возвращает глобальный менеджер таблицы рекордов"""
    global _leaderboard_manager
    if _leaderboard_manager is None:
        _leaderboard_manager = LeaderboardManager()
    return _leaderboard_manager


def init_leaderboard_manager(save_path: str = "leaderboard.json") -> LeaderboardManager:
    """Инициализирует менеджер таблицы рекордов"""
    global _leaderboard_manager
    _leaderboard_manager = LeaderboardManager(save_path=save_path)
    return _leaderboard_manager
