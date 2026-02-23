#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Achievements system for Tetris Enhanced

Features:
- Track player progress and milestones
- Unlock achievements based on gameplay
- Persistent storage of unlocked achievements
- Visual notifications for unlocks
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("TetrisEnhanced.Achievements")


class AchievementType(Enum):
    """Типы достижений"""
    LINES = "lines"           # Очистка линий
    SCORE = "score"           # Набор очков
    LEVEL = "level"           # Достигнутый уровень
    COMBO = "combo"           # Комбо
    TETRIS = "tetris"         # Очистка 4 линий
    T_SPIN = "t_spin"         # T-Spin
    PERFECT = "perfect"       # Идеальная игра
    SURVIVAL = "survival"     # Выживание
    SPEED = "speed"           # Скорость
    SPECIAL = "special"       # Специальное


class AchievementTier(Enum):
    """Уровни редкости достижений"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


@dataclass
class Achievement:
    """Достижение"""
    id: str
    name: str
    description: str
    type: AchievementType
    tier: AchievementTier
    condition: Dict[str, Any]  # {field: target_value}
    
    icon_path: Optional[str] = None
    hidden: bool = False
    category: str = "general"
    
    def check(self, stats: Dict[str, Any]) -> bool:
        """
        Проверяет, выполнено ли условие достижения
        
        Args:
            stats: Текущая статистика игрока
        
        Returns:
            True если условие выполнено
        """
        for stat_name, target_value in self.condition.items():
            player_value = stats.get(stat_name, 0)
            
            if isinstance(target_value, (int, float)):
                # Числовое сравнение
                if player_value < target_value:
                    return False
            elif isinstance(target_value, list):
                # Проверка наличия в списке
                if player_value not in target_value:
                    return False
            elif isinstance(target_value, dict):
                # Сложное условие
                for op, value in target_value.items():
                    if op == "gte" and player_value < value:
                        return False
                    if op == "lte" and player_value > value:
                        return False
                    if op == "eq" and player_value != value:
                        return False
                    if op == "in" and player_value not in value:
                        return False
        
        return True


@dataclass
class UnlockedAchievement:
    """Разблокированное достижение"""
    achievement: Achievement
    unlocked_at: float  # timestamp
    game_context: Optional[Dict[str, Any]] = None  # Контекст игры при разблокировке
    
    def to_dict(self) -> dict:
        return {
            'achievement_id': self.achievement.id,
            'unlocked_at': self.unlocked_at,
            'game_context': self.game_context
        }
    
    @classmethod
    def from_dict(cls, data: dict, achievements_db: Dict[str, Achievement]) -> 'UnlockedAchievement':
        achievement = achievements_db.get(data['achievement_id'])
        if not achievement:
            raise ValueError(f"Achievement {data['achievement_id']} not found")
        
        return cls(
            achievement=achievement,
            unlocked_at=data['unlocked_at'],
            game_context=data.get('game_context')
        )


class AchievementProgress:
    """Прогресс достижения"""
    
    def __init__(self, achievement: Achievement):
        self.achievement = achievement
        self.current_value = 0
        self.target_value = self._get_target_value()
        self.percentage = 0.0
    
    def _get_target_value(self) -> float:
        """Получает целевое значение из условия"""
        condition = self.achievement.condition
        if not condition:
            return 0
        
        # Берём первое значение из условия как целевое
        for value in condition.values():
            if isinstance(value, (int, float)):
                return value
            elif isinstance(value, dict) and 'gte' in value:
                return value['gte']
        
        return 0
    
    def update(self, stats: Dict[str, Any]):
        """Обновляет прогресс"""
        stat_name = list(self.achievement.condition.keys())[0]
        self.current_value = stats.get(stat_name, 0)
        self.percentage = min(100, (self.current_value / self.target_value * 100) if self.target_value > 0 else 0)


class AchievementNotification:
    """Визуальное уведомление о достижении"""
    
    def __init__(self, achievement: Achievement, duration: float = 5.0):
        self.achievement = achievement
        self.duration = duration
        self.start_time = time.time()
        self.visible = True
        self.animation_progress = 0.0
        self.slide_in_duration = 0.5
        self.display_duration = duration - 1.0
        self.slide_out_duration = 0.5
    
    def update(self, dt: float) -> bool:
        """
        Обновляет уведомление
        
        Returns:
            True если уведомление ещё активно
        """
        elapsed = time.time() - self.start_time
        
        if elapsed >= self.duration:
            self.visible = False
            return False
        
        # Анимация появления
        if elapsed < self.slide_in_duration:
            self.animation_progress = elapsed / self.slide_in_duration
        # Удержание
        elif elapsed < self.display_duration:
            self.animation_progress = 1.0
        # Анимация исчезновения
        else:
            self.animation_progress = 1.0 - (elapsed - self.display_duration) / self.slide_out_duration
        
        return True
    
    def get_position(self, screen_width: int, screen_height: int) -> tuple:
        """Получает позицию уведомления"""
        # Появляется сверху экрана
        base_y = 20
        target_x = screen_width // 2
        
        # Easing function
        t = self.animation_progress
        ease_out = t * (2 - t)
        
        # Вычисляем Y с анимацией
        slide_distance = 100
        current_y = base_y - slide_distance * (1 - ease_out)
        
        return target_x, current_y


class AchievementsManager:
    """
    Менеджер достижений
    
    Features:
    - Register and track achievements
    - Check unlock conditions
    - Persistent storage
    - Visual notifications
    - Statistics tracking
    """
    
    def __init__(self, save_path: str = "achievements_save.json"):
        self.save_path = save_path
        
        # База данных достижений
        self.achievements_db: Dict[str, Achievement] = {}
        
        # Разблокированные достижения
        self.unlocked: Dict[str, UnlockedAchievement] = {}
        
        # Прогресс по заблокированным достижениям
        self.progress: Dict[str, AchievementProgress] = {}
        
        # Текущая статистика игрока
        self.player_stats: Dict[str, Any] = {}
        
        # Активные уведомления
        self.notifications: List[AchievementNotification] = []
        
        # Callbacks
        self.on_achievement_unlocked: Optional[Callable[[Achievement], None]] = None
        
        # Инициализация
        self._load_default_achievements()
        self.load()
    
    def _load_default_achievements(self):
        """Загрувает стандартные достижения"""
        default_achievements = [
            # Достижения за линии
            Achievement(
                id="first_line",
                name="Первая линия",
                description="Очистите свою первую линию",
                type=AchievementType.LINES,
                tier=AchievementTier.BRONZE,
                condition={"lines_cleared": 1},
                category="lines"
            ),
            Achievement(
                id="line_master",
                name="Мастер линий",
                description="Очистите 100 линий",
                type=AchievementType.LINES,
                tier=AchievementTier.SILVER,
                condition={"lines_cleared": 100},
                category="lines"
            ),
            Achievement(
                id="line_legend",
                name="Легенда линий",
                description="Очистите 500 линий",
                type=AchievementType.LINES,
                tier=AchievementTier.GOLD,
                condition={"lines_cleared": 500},
                category="lines"
            ),
            
            # Достижения за очки
            Achievement(
                id="first_points",
                name="Первые очки",
                description="Наберите 1000 очков",
                type=AchievementType.SCORE,
                tier=AchievementTier.BRONZE,
                condition={"score": 1000},
                category="score"
            ),
            Achievement(
                id="score_chaser",
                name="Охотник за очками",
                description="Наберите 10000 очков",
                type=AchievementType.SCORE,
                tier=AchievementTier.SILVER,
                condition={"score": 10000},
                category="score"
            ),
            Achievement(
                id="score_master",
                name="Мастер очков",
                description="Наберите 50000 очков",
                type=AchievementType.SCORE,
                tier=AchievementTier.GOLD,
                condition={"score": 50000},
                category="score"
            ),
            Achievement(
                id="score_legend",
                name="Легенда очков",
                description="Наберите 100000 очков",
                type=AchievementType.SCORE,
                tier=AchievementTier.PLATINUM,
                condition={"score": 100000},
                category="score"
            ),
            
            # Достижения за уровни
            Achievement(
                id="level_5",
                name="Новичок",
                description="Достигните уровня 5",
                type=AchievementType.LEVEL,
                tier=AchievementTier.BRONZE,
                condition={"level": 5},
                category="level"
            ),
            Achievement(
                id="level_10",
                name="Опытный",
                description="Достигните уровня 10",
                type=AchievementType.LEVEL,
                tier=AchievementTier.SILVER,
                condition={"level": 10},
                category="level"
            ),
            Achievement(
                id="level_15",
                name="Эксперт",
                description="Достигните уровня 15",
                type=AchievementType.LEVEL,
                tier=AchievementTier.GOLD,
                condition={"level": 15},
                category="level"
            ),
            
            # Достижения за комбо
            Achievement(
                id="combo_3",
                name="Комбо-мастер",
                description="Сделайте комбо x3",
                type=AchievementType.COMBO,
                tier=AchievementTier.BRONZE,
                condition={"max_combo": 3},
                category="combo"
            ),
            Achievement(
                id="combo_5",
                name="Комбо-легенда",
                description="Сделайте комбо x5",
                type=AchievementType.COMBO,
                tier=AchievementTier.SILVER,
                condition={"max_combo": 5},
                category="combo"
            ),
            
            # Достижения за тетрисы
            Achievement(
                id="first_tetris",
                name="Тетрис!",
                description="Очистите 4 линии одновременно",
                type=AchievementType.TETRIS,
                tier=AchievementTier.BRONZE,
                condition={"tetrises": 1},
                category="special"
            ),
            Achievement(
                id="tetris_master",
                name="Мастер тетрисов",
                description="Очистите 50 тетрисов",
                type=AchievementType.TETRIS,
                tier=AchievementTier.GOLD,
                condition={"tetrises": 50},
                category="special"
            ),
            
            # Достижения за T-Spin
            Achievement(
                id="first_t_spin",
                name="T-Spin!",
                description="Выполните T-Spin",
                type=AchievementType.T_SPIN,
                tier=AchievementTier.SILVER,
                condition={"t_spins": 1},
                category="special"
            ),
            
            # Достижения за выживание
            Achievement(
                id="survivor_60",
                name="Выживший",
                description="Продержитесь 60 секунд",
                type=AchievementType.SURVIVAL,
                tier=AchievementTier.BRONZE,
                condition={"survival_time": 60},
                category="survival"
            ),
            Achievement(
                id="survivor_300",
                name="Долгожитель",
                description="Продержитесь 5 минут",
                type=AchievementType.SURVIVAL,
                tier=AchievementTier.SILVER,
                condition={"survival_time": 300},
                category="survival"
            ),
            
            # Специальные достижения
            Achievement(
                id="perfect_game",
                name="Идеальная игра",
                description="Завершите игру без проигрыша на уровне 10+",
                type=AchievementType.PERFECT,
                tier=AchievementTier.DIAMOND,
                condition={"perfect_game": True},
                category="special",
                hidden=True
            ),
            Achievement(
                id="speed_demon",
                name="Скоростной демон",
                description="Сделайте 10 жестких падений за 10 секунд",
                type=AchievementType.SPEED,
                tier=AchievementTier.GOLD,
                condition={"hard_drops_per_second": {"gte": 1.0}},
                category="special",
                hidden=True
            ),
        ]
        
        for achievement in default_achievements:
            self.achievements_db[achievement.id] = achievement
            self.progress[achievement.id] = AchievementProgress(achievement)
    
    def update_stats(self, stats: Dict[str, Any]):
        """
        Обновляет статистику игрока и проверяет достижения
        
        Args:
            stats: Новые значения статистики
        """
        # Обновляем статистику
        for key, value in stats.items():
            if key in self.player_stats:
                # Для числовых значений берём максимум
                if isinstance(self.player_stats[key], (int, float)):
                    self.player_stats[key] = max(self.player_stats[key], value)
                else:
                    self.player_stats[key] = value
            else:
                self.player_stats[key] = value
        
        # Проверяем достижения
        self._check_achievements()
        
        # Обновляем прогресс
        self._update_progress()
    
    def _check_achievements(self):
        """Проверяет условия разблокировки достижений"""
        for achievement_id, achievement in self.achievements_db.items():
            # Пропускаем уже разблокированные
            if achievement_id in self.unlocked:
                continue
            
            # Проверяем условие
            if achievement.check(self.player_stats):
                self._unlock_achievement(achievement)
    
    def _unlock_achievement(self, achievement: Achievement):
        """Разблокирует достижение"""
        unlocked = UnlockedAchievement(
            achievement=achievement,
            unlocked_at=time.time(),
            game_context=self._get_game_context()
        )
        
        self.unlocked[achievement.id] = unlocked
        
        # Создаём уведомление
        self.notifications.append(AchievementNotification(achievement))
        
        # Вызываем callback
        if self.on_achievement_unlocked:
            self.on_achievement_unlocked(achievement)
        
        logger.info(f"Achievement unlocked: {achievement.name}")
    
    def _get_game_context(self) -> Dict[str, Any]:
        """Возвращает текущий контекст игры"""
        return {
            'score': self.player_stats.get('score', 0),
            'level': self.player_stats.get('level', 1),
            'lines': self.player_stats.get('lines_cleared', 0)
        }
    
    def _update_progress(self):
        """Обновляет прогресс достижений"""
        for achievement_id, progress in self.progress.items():
            if achievement_id not in self.unlocked:
                progress.update(self.player_stats)
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """Возвращает список разблокированных достижений"""
        return [self.achievements_db[uid] for uid in self.unlocked]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """Возвращает список заблокированных достижений"""
        return [
            ach for ach_id, ach in self.achievements_db.items()
            if ach_id not in self.unlocked
        ]
    
    def get_progress(self, achievement_id: str) -> Optional[AchievementProgress]:
        """Возвращает прогресс конкретного достижения"""
        return self.progress.get(achievement_id)
    
    def get_completion_percentage(self) -> float:
        """Возвращает процент выполнения всех достижений"""
        if not self.achievements_db:
            return 0.0
        return len(self.unlocked) / len(self.achievements_db) * 100
    
    def get_achievements_by_category(self) -> Dict[str, List[Achievement]]:
        """Группирует достижения по категориям"""
        categories = {}
        for achievement in self.achievements_db.values():
            cat = achievement.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(achievement)
        return categories
    
    def save(self):
        """Сохраняет прогресс достижений"""
        try:
            data = {
                'unlocked': [u.to_dict() for u in self.unlocked.values()],
                'player_stats': self.player_stats,
                'version': '1.0'
            }
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Achievements saved to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save achievements: {e}")
    
    def load(self):
        """Загружает прогресс достижений"""
        if not os.path.exists(self.save_path):
            logger.info("No achievements save file found, starting fresh")
            return
        
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загружаем разблокированные достижения
            for item in data.get('unlocked', []):
                try:
                    unlocked = UnlockedAchievement.from_dict(item, self.achievements_db)
                    self.unlocked[unlocked.achievement.id] = unlocked
                except ValueError as e:
                    logger.warning(f"Failed to load achievement: {e}")
            
            # Загружаем статистику
            self.player_stats = data.get('player_stats', {})
            
            # Обновляем прогресс
            self._update_progress()
            
            logger.info(f"Achievements loaded from {self.save_path}")
            logger.info(f"Unlocked: {len(self.unlocked)}/{len(self.achievements_db)}")
        except Exception as e:
            logger.error(f"Failed to load achievements: {e}")
    
    def update_notifications(self, dt: float):
        """Обновляет уведомления"""
        for notification in self.notifications[:]:
            if not notification.update(dt):
                self.notifications.remove(notification)
    
    def reset_progress(self):
        """Сбрасывает весь прогресс"""
        self.unlocked.clear()
        self.player_stats.clear()
        self.notifications.clear()
        
        for achievement in self.achievements_db.values():
            self.progress[achievement.id] = AchievementProgress(achievement)
        
        logger.info("Achievements progress reset")


# Глобальный экземпляр
_achievements_manager: Optional[AchievementsManager] = None


def get_achievements_manager() -> AchievementsManager:
    """Возвращает глобальный менеджер достижений"""
    global _achievements_manager
    if _achievements_manager is None:
        _achievements_manager = AchievementsManager()
    return _achievements_manager


def init_achievements_manager(save_path: str = "achievements_save.json") -> AchievementsManager:
    """Инициализирует менеджер достижений"""
    global _achievements_manager
    _achievements_manager = AchievementsManager(save_path=save_path)
    return _achievements_manager
