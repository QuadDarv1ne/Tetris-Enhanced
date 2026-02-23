#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Challenges System for Tetris Enhanced

Features:
- Daily challenges that reset every 24 hours
- Various challenge types with different difficulties
- Rewards for completion
- Persistent tracking of progress
"""

import os
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("TetrisEnhanced.DailyChallenges")


class ChallengeType(Enum):
    """Типы испытаний"""
    LINES = "lines"           # Очистить N линий
    SCORE = "score"           # Набрать N очков
    LEVEL = "level"           # Достичь уровня N
    TETRIS = "tetris"         # Сделать N тетрисов
    COMBO = "combo"           # Сделать комбо N
    SURVIVAL = "survival"     # Продержаться N секунд
    DROPS = "drops"           # Сделать N жестких падений
    ROTATIONS = "rotations"   # Сделать N поворотов
    PERFECT = "perfect"       # Игра без проигрыша до уровня N
    SPEED = "speed"           # Очистить N линий за M секунд


class ChallengeTier(Enum):
    """Уровни сложности испытаний"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"
    MASTER = "master"


@dataclass
class Challenge:
    """Ежедневное испытание"""
    id: str
    name: str
    description: str
    type: ChallengeType
    tier: ChallengeTier
    target: int  # Целевое значение
    bonus_target: Optional[int] = None  # Дополнительная цель (для speed и т.п.)
    
    reward_xp: int = 100      # Опыт награды
    reward_coins: int = 50    # Монеты награды
    bonus_reward_xp: int = 50  # Бонусный опыт
    bonus_reward_coins: int = 25  # Бонусные монеты
    
    seed: int = 0  # Seed для генерации дня
    completed: bool = False
    bonus_completed: bool = False
    progress: int = 0
    
    def __post_init__(self):
        if self.seed == 0:
            self.seed = random.randint(1, 999999)
    
    def check_completion(self, stats: Dict[str, Any]) -> Tuple[bool, bool]:
        """
        Проверяет выполнение испытания
        
        Returns:
            (completed, bonus_completed)
        """
        stat_name = self._get_stat_name()
        current_value = stats.get(stat_name, 0)
        
        completed = current_value >= self.target
        bonus_completed = False
        
        if self.bonus_target is not None:
            bonus_completed = current_value >= self.bonus_target
        
        return completed, bonus_completed
    
    def _get_stat_name(self) -> str:
        """Получает имя статистики для испытания"""
        mapping = {
            ChallengeType.LINES: "lines_cleared",
            ChallengeType.SCORE: "score",
            ChallengeType.LEVEL: "level",
            ChallengeType.TETRIS: "tetrises",
            ChallengeType.COMBO: "max_combo",
            ChallengeType.SURVIVAL: "survival_time",
            ChallengeType.DROPS: "hard_drops",
            ChallengeType.ROTATIONS: "rotations",
            ChallengeType.PERFECT: "level_reached_without_death",
            ChallengeType.SPEED: "lines_per_minute"
        }
        return mapping.get(self.type, "score")
    
    def get_progress_percentage(self, stats: Dict[str, Any]) -> float:
        """Получает процент прогресса"""
        stat_name = self._get_stat_name()
        current_value = stats.get(stat_name, 0)
        
        if self.target <= 0:
            return 100.0 if current_value >= self.target else 0.0
        
        return min(100.0, (current_value / self.target) * 100)
    
    def to_dict(self) -> dict:
        """Сериализует испытание в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'tier': self.tier.value,
            'target': self.target,
            'bonus_target': self.bonus_target,
            'reward_xp': self.reward_xp,
            'reward_coins': self.reward_coins,
            'bonus_reward_xp': self.bonus_reward_xp,
            'bonus_reward_coins': self.bonus_reward_coins,
            'seed': self.seed,
            'completed': self.completed,
            'bonus_completed': self.bonus_completed,
            'progress': self.progress
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Challenge':
        """Создаёт испытание из словаря"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            type=ChallengeType(data['type']),
            tier=ChallengeTier(data['tier']),
            target=data['target'],
            bonus_target=data.get('bonus_target'),
            reward_xp=data.get('reward_xp', 100),
            reward_coins=data.get('reward_coins', 50),
            bonus_reward_xp=data.get('bonus_reward_xp', 50),
            bonus_reward_coins=data.get('bonus_reward_coins', 25),
            seed=data.get('seed', 0),
            completed=data.get('completed', False),
            bonus_completed=data.get('bonus_completed', False),
            progress=data.get('progress', 0)
        )


@dataclass
class DailyChallengeSet:
    """Набор испытаний на день"""
    date: str  # YYYY-MM-DD
    challenges: List[Challenge] = field(default_factory=list)
    completed_count: int = 0
    total_xp_earned: int = 0
    total_coins_earned: int = 0
    
    def to_dict(self) -> dict:
        return {
            'date': self.date,
            'challenges': [c.to_dict() for c in self.challenges],
            'completed_count': self.completed_count,
            'total_xp_earned': self.total_xp_earned,
            'total_coins_earned': self.total_coins_earned
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DailyChallengeSet':
        return cls(
            date=data['date'],
            challenges=[Challenge.from_dict(c) for c in data.get('challenges', [])],
            completed_count=data.get('completed_count', 0),
            total_xp_earned=data.get('total_xp_earned', 0),
            total_coins_earned=data.get('total_coins_earned', 0)
        )


class ChallengeGenerator:
    """Генератор ежедневных испытаний"""
    
    # Шаблоны испытаний
    CHALLENGE_TEMPLATES = {
        ChallengeType.LINES: [
            {"name": "Линии: Новичок", "description": "Очистите {target} линий", "tier": ChallengeTier.EASY, "target_range": (10, 30)},
            {"name": "Линии: Любитель", "description": "Очистите {target} линий", "tier": ChallengeTier.MEDIUM, "target_range": (30, 60)},
            {"name": "Линии: Эксперт", "description": "Очистите {target} линий", "tier": ChallengeTier.HARD, "target_range": (60, 100)},
            {"name": "Линии: Мастер", "description": "Очистите {target} линий", "tier": ChallengeTier.EXPERT, "target_range": (100, 150)},
            {"name": "Линии: Легенда", "description": "Очистите {target} линий", "tier": ChallengeTier.MASTER, "target_range": (150, 200)},
        ],
        ChallengeType.SCORE: [
            {"name": "Очки: Новичок", "description": "Наберите {target:,} очков", "tier": ChallengeTier.EASY, "target_range": (5000, 10000)},
            {"name": "Очки: Любитель", "description": "Наберите {target:,} очков", "tier": ChallengeTier.MEDIUM, "target_range": (10000, 25000)},
            {"name": "Очки: Эксперт", "description": "Наберите {target:,} очков", "tier": ChallengeTier.HARD, "target_range": (25000, 50000)},
            {"name": "Очки: Мастер", "description": "Наберите {target:,} очков", "tier": ChallengeTier.EXPERT, "target_range": (50000, 100000)},
            {"name": "Очки: Легенда", "description": "Наберите {target:,} очков", "tier": ChallengeTier.MASTER, "target_range": (100000, 200000)},
        ],
        ChallengeType.LEVEL: [
            {"name": "Уровень: Новичок", "description": "Достигните уровня {target}", "tier": ChallengeTier.EASY, "target_range": (3, 5)},
            {"name": "Уровень: Любитель", "description": "Достигните уровня {target}", "tier": ChallengeTier.MEDIUM, "target_range": (5, 8)},
            {"name": "Уровень: Эксперт", "description": "Достигните уровня {target}", "tier": ChallengeTier.HARD, "target_range": (8, 12)},
            {"name": "Уровень: Мастер", "description": "Достигните уровня {target}", "tier": ChallengeTier.EXPERT, "target_range": (12, 15)},
            {"name": "Уровень: Легенда", "description": "Достигните уровня {target}", "tier": ChallengeTier.MASTER, "target_range": (15, 20)},
        ],
        ChallengeType.TETRIS: [
            {"name": "Тетрис: Новичок", "description": "Сделайте {target} тетриса(ов)", "tier": ChallengeTier.EASY, "target_range": (1, 3)},
            {"name": "Тетрис: Любитель", "description": "Сделайте {target} тетриса(ов)", "tier": ChallengeTier.MEDIUM, "target_range": (3, 6)},
            {"name": "Тетрис: Эксперт", "description": "Сделайте {target} тетриса(ов)", "tier": ChallengeTier.HARD, "target_range": (6, 10)},
            {"name": "Тетрис: Мастер", "description": "Сделайте {target} тетриса(ов)", "tier": ChallengeTier.EXPERT, "target_range": (10, 15)},
            {"name": "Тетрис: Легенда", "description": "Сделайте {target} тетриса(ов)", "tier": ChallengeTier.MASTER, "target_range": (15, 25)},
        ],
        ChallengeType.COMBO: [
            {"name": "Комбо: Новичок", "description": "Сделайте комбо x{target}", "tier": ChallengeTier.EASY, "target_range": (2, 3)},
            {"name": "Комбо: Любитель", "description": "Сделайте комбо x{target}", "tier": ChallengeTier.MEDIUM, "target_range": (3, 5)},
            {"name": "Комбо: Эксперт", "description": "Сделайте комбо x{target}", "tier": ChallengeTier.HARD, "target_range": (5, 8)},
            {"name": "Комбо: Мастер", "description": "Сделайте комбо x{target}", "tier": ChallengeTier.EXPERT, "target_range": (8, 12)},
            {"name": "Комбо: Легенда", "description": "Сделайте комбо x{target}", "tier": ChallengeTier.MASTER, "target_range": (12, 20)},
        ],
        ChallengeType.SURVIVAL: [
            {"name": "Выживание: Новичок", "description": "Продержитесь {target} секунд", "tier": ChallengeTier.EASY, "target_range": (60, 120)},
            {"name": "Выживание: Любитель", "description": "Продержитесь {target} секунд", "tier": ChallengeTier.MEDIUM, "target_range": (120, 180)},
            {"name": "Выживание: Эксперт", "description": "Продержитесь {target} секунд", "tier": ChallengeTier.HARD, "target_range": (180, 300)},
            {"name": "Выживание: Мастер", "description": "Продержитесь {target} секунд", "tier": ChallengeTier.EXPERT, "target_range": (300, 450)},
            {"name": "Выживание: Легенда", "description": "Продержитесь {target} секунд", "tier": ChallengeTier.MASTER, "target_range": (450, 600)},
        ],
        ChallengeType.DROPS: [
            {"name": "Падения: Новичок", "description": "Сделайте {target} жестких падений", "tier": ChallengeTier.EASY, "target_range": (10, 20)},
            {"name": "Падения: Любитель", "description": "Сделайте {target} жестких падений", "tier": ChallengeTier.MEDIUM, "target_range": (20, 40)},
            {"name": "Падения: Эксперт", "description": "Сделайте {target} жестких падений", "tier": ChallengeTier.HARD, "target_range": (40, 70)},
            {"name": "Падения: Мастер", "description": "Сделайте {target} жестких падений", "tier": ChallengeTier.EXPERT, "target_range": (70, 100)},
            {"name": "Падения: Легенда", "description": "Сделайте {target} жестких падений", "tier": ChallengeTier.MASTER, "target_range": (100, 150)},
        ],
        ChallengeType.ROTATIONS: [
            {"name": "Вращения: Новичок", "description": "Сделайте {target} поворотов", "tier": ChallengeTier.EASY, "target_range": (50, 100)},
            {"name": "Вращения: Любитель", "description": "Сделайте {target} поворотов", "tier": ChallengeTier.MEDIUM, "target_range": (100, 200)},
            {"name": "Вращения: Эксперт", "description": "Сделайте {target} поворотов", "tier": ChallengeTier.HARD, "target_range": (200, 350)},
            {"name": "Вращения: Мастер", "description": "Сделайте {target} поворотов", "tier": ChallengeTier.EXPERT, "target_range": (350, 500)},
            {"name": "Вращения: Легенда", "description": "Сделайте {target} поворотов", "tier": ChallengeTier.MASTER, "target_range": (500, 750)},
        ],
        ChallengeType.SPEED: [
            {"name": "Скорость: Новичок", "description": "Очистите {target} линий за первые 2 минуты", "tier": ChallengeTier.EASY, "target_range": (5, 10), "bonus": True},
            {"name": "Скорость: Любитель", "description": "Очистите {target} линий за первые 2 минуты", "tier": ChallengeTier.MEDIUM, "target_range": (10, 20), "bonus": True},
            {"name": "Скорость: Эксперт", "description": "Очистите {target} линий за первые 2 минуты", "tier": ChallengeTier.HARD, "target_range": (20, 35), "bonus": True},
            {"name": "Скорость: Мастер", "description": "Очистите {target} линий за первые 2 минуты", "tier": ChallengeTier.EXPERT, "target_range": (35, 50), "bonus": True},
            {"name": "Скорость: Легенда", "description": "Очистите {target} линий за первые 2 минуты", "tier": ChallengeTier.MASTER, "target_range": (50, 70), "bonus": True},
        ],
    }
    
    @staticmethod
    def get_today_seed() -> int:
        """Получает seed для сегодняшнего дня"""
        today = datetime.now().strftime("%Y%m%d")
        return int(today)
    
    @staticmethod
    def get_date_string() -> str:
        """Получает строку даты в формате YYYY-MM-DD"""
        return datetime.now().strftime("%Y-%m-%d")
    
    @classmethod
    def generate_daily_challenge(cls, challenge_type: ChallengeType, seed: int) -> Challenge:
        """Генерирует испытание на день"""
        random.seed(seed + hash(challenge_type.value))
        
        templates = cls.CHALLENGE_TEMPLATES.get(challenge_type, [])
        if not templates:
            # Возвращаем испытание по умолчанию
            return Challenge(
                id=f"default_{challenge_type.value}",
                name="Стандартное испытание",
                description="Выполните базовое задание",
                type=challenge_type,
                tier=ChallengeTier.EASY,
                target=10
            )
        
        # Выбираем шаблон на основе seed
        template_index = random.randint(0, len(templates) - 1)
        template = templates[template_index]
        
        # Генерируем целевое значение
        min_target, max_target = template["target_range"]
        target = random.randint(min_target, max_target)
        
        # Бонусная цель для некоторых типов
        bonus_target = None
        bonus_reward_xp = 50
        bonus_reward_coins = 25
        
        if template.get("bonus"):
            bonus_target = int(target * 1.5)
            bonus_reward_xp = 75
            bonus_reward_coins = 40
        
        # Форматируем описание
        description = template["description"].format(target=target)
        if bonus_target:
            description += f" (бонус: {bonus_target})"
        
        return Challenge(
            id=f"daily_{challenge_type.value}_{seed}",
            name=template["name"],
            description=description,
            type=challenge_type,
            tier=template["tier"],
            target=target,
            bonus_target=bonus_target,
            bonus_reward_xp=bonus_reward_xp,
            bonus_reward_coins=bonus_reward_coins,
            seed=seed
        )
    
    @classmethod
    def generate_daily_set(cls, seed: Optional[int] = None) -> DailyChallengeSet:
        """Генерирует набор испытаний на день"""
        if seed is None:
            seed = cls.get_today_seed()
        
        date_str = cls.get_date_string()
        
        # Выбираем 3-5 случайных типов испытаний
        available_types = list(ChallengeType)
        random.seed(seed)
        
        num_challenges = random.randint(3, 5)
        selected_types = random.sample(available_types, min(num_challenges, len(available_types)))
        
        challenges = []
        for challenge_type in selected_types:
            challenge = cls.generate_daily_challenge(challenge_type, seed)
            challenges.append(challenge)
        
        return DailyChallengeSet(
            date=date_str,
            challenges=challenges
        )


class DailyChallengesManager:
    """
    Менеджер ежедневных испытаний
    
    Features:
    - Generate daily challenges
    - Track progress
    - Award rewards
    - Persistent storage
    """
    
    def __init__(self, save_path: str = "daily_challenges_save.json"):
        self.save_path = save_path
        self.current_set: Optional[DailyChallengeSet] = None
        self.history: List[DailyChallengeSet] = []
        self.player_xp: int = 0
        self.player_coins: int = 0
        self.total_completed: int = 0
        self.streak_days: int = 0
        self.last_played_date: Optional[str] = None
        
        self.generator = ChallengeGenerator()
        
        # Callbacks
        self.on_challenge_completed: Optional[callable] = None
        self.on_reward_earned: Optional[callable] = None
        
        self.load()
        self._check_daily_reset()
    
    def _check_daily_reset(self):
        """Проверяет необходимость сброса ежедневных испытаний"""
        today = self.generator.get_date_string()
        
        if self.current_set is None:
            self._generate_new_set()
        elif self.current_set.date != today:
            # Сохраняем историю
            if self.current_set.challenges:
                self.history.append(self.current_set)
                # Храним только последние 30 дней
                if len(self.history) > 30:
                    self.history = self.history[-30:]
            
            # Проверяем streak
            if self.last_played_date:
                last_date = datetime.strptime(self.last_played_date, "%Y-%m-%d")
                today_date = datetime.strptime(today, "%Y-%m-%d")
                diff = (today_date - last_date).days
                
                if diff == 1:
                    self.streak_days += 1
                elif diff > 1:
                    self.streak_days = 0
            
            self._generate_new_set()
    
    def _generate_new_set(self):
        """Генерирует новый набор испытаний"""
        self.current_set = self.generator.generate_daily_set()
        self.last_played_date = self.current_set.date
        logger.info(f"Generated new daily challenges for {self.current_set.date}")
    
    def update_progress(self, stats: Dict[str, Any]):
        """Обновляет прогресс испытаний"""
        if not self.current_set:
            return
        
        completed_before = self.current_set.completed_count
        
        for challenge in self.current_set.challenges:
            if challenge.completed:
                continue
            
            completed, bonus_completed = challenge.check_completion(stats)
            old_progress = challenge.progress
            challenge.progress = int(challenge.get_progress_percentage(stats))
            
            # Проверяем завершение
            if completed and not challenge.completed:
                challenge.completed = True
                self._complete_challenge(challenge)
            
            if bonus_completed and not challenge.bonus_completed:
                challenge.bonus_completed = True
                self._complete_challenge_bonus(challenge)
        
        # Обновляем счётчик
        self.current_set.completed_count = sum(
            1 for c in self.current_set.challenges if c.completed
        )
        
        # Проверяем завершение всех испытаний
        if self.current_set.completed_count > completed_before:
            self._check_all_completed()
    
    def _complete_challenge(self, challenge: Challenge):
        """Завершает испытание"""
        self.player_xp += challenge.reward_xp
        self.player_coins += challenge.reward_coins
        self.current_set.total_xp_earned += challenge.reward_xp
        self.current_set.total_coins_earned += challenge.reward_coins
        self.total_completed += 1
        
        logger.info(f"Daily challenge completed: {challenge.name}")
        logger.info(f"Reward: +{challenge.reward_xp} XP, +{challenge.reward_coins} coins")
        
        if self.on_challenge_completed:
            self.on_challenge_completed(challenge, False)
        
        if self.on_reward_earned:
            self.on_reward_earned(challenge.reward_xp, challenge.reward_coins, False)
    
    def _complete_challenge_bonus(self, challenge: Challenge):
        """Завершает бонусную цель испытания"""
        self.player_xp += challenge.bonus_reward_xp
        self.player_coins += challenge.bonus_reward_coins
        self.current_set.total_xp_earned += challenge.bonus_reward_xp
        self.current_set.total_coins_earned += challenge.bonus_reward_coins
        
        logger.info(f"Daily challenge bonus completed: {challenge.name}")
        logger.info(f"Bonus reward: +{challenge.bonus_reward_xp} XP, +{challenge.bonus_reward_coins} coins")
        
        if self.on_challenge_completed:
            self.on_challenge_completed(challenge, True)
        
        if self.on_reward_earned:
            self.on_reward_earned(challenge.bonus_reward_xp, challenge.bonus_reward_coins, True)
    
    def _check_all_completed(self):
        """Проверяет завершение всех испытаний за день"""
        if not self.current_set:
            return
        
        all_completed = all(c.completed for c in self.current_set.challenges)
        if all_completed:
            # Бонус за завершение всех испытаний
            streak_bonus = min(self.streak_days, 7) * 10  # Максимум 70 XP бонуса
            self.player_xp += 100 + streak_bonus
            self.player_coins += 50
            
            logger.info(f"All daily challenges completed! Bonus: +{100 + streak_bonus} XP, +50 coins")
            logger.info(f"Current streak: {self.streak_days} days")
    
    def get_current_challenges(self) -> List[Challenge]:
        """Возвращает текущие испытания"""
        if not self.current_set:
            return []
        return self.current_set.challenges
    
    def get_completion_percentage(self) -> float:
        """Возвращает процент выполнения сегодняшних испытаний"""
        if not self.current_set or not self.current_set.challenges:
            return 0.0
        
        completed = sum(1 for c in self.current_set.challenges if c.completed)
        return (completed / len(self.current_set.challenges)) * 100
    
    def get_total_progress_percentage(self) -> float:
        """Возвращает общий процент выполнения с учётом бонусов"""
        if not self.current_set or not self.current_set.challenges:
            return 0.0
        
        total_progress = sum(c.progress for c in self.current_set.challenges)
        max_progress = len(self.current_set.challenges) * 100
        return (total_progress / max_progress) * 100
    
    def get_streak_info(self) -> Tuple[int, int]:
        """Возвращает информацию о серии"""
        max_streak = 7  # Максимальный бонус за серию
        return self.streak_days, max_streak
    
    def get_rewards_summary(self) -> Dict[str, int]:
        """Возвращает сводку наград"""
        return {
            'xp': self.player_xp,
            'coins': self.player_coins,
            'total_completed': self.total_completed,
            'streak_days': self.streak_days
        }
    
    def save(self):
        """Сохраняет прогресс"""
        try:
            data = {
                'current_set': self.current_set.to_dict() if self.current_set else None,
                'history': [hs.to_dict() for hs in self.history[-30:]],
                'player_xp': self.player_xp,
                'player_coins': self.player_coins,
                'total_completed': self.total_completed,
                'streak_days': self.streak_days,
                'last_played_date': self.last_played_date,
                'version': '1.0'
            }
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Daily challenges saved to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save daily challenges: {e}")
    
    def load(self):
        """Загружает прогресс"""
        if not os.path.exists(self.save_path):
            logger.info("No daily challenges save file found")
            return
        
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Загружаем текущий набор
            if data.get('current_set'):
                self.current_set = DailyChallengeSet.from_dict(data['current_set'])
            
            # Загружаем историю
            for hs_data in data.get('history', []):
                self.history.append(DailyChallengeSet.from_dict(hs_data))
            
            # Загружаем статистику игрока
            self.player_xp = data.get('player_xp', 0)
            self.player_coins = data.get('player_coins', 0)
            self.total_completed = data.get('total_completed', 0)
            self.streak_days = data.get('streak_days', 0)
            self.last_played_date = data.get('last_played_date')
            
            logger.info(f"Daily challenges loaded from {self.save_path}")
            if self.current_set:
                logger.info(f"Current set date: {self.current_set.date}")
                logger.info(f"Challenges: {len(self.current_set.challenges)}")
            
        except Exception as e:
            logger.error(f"Failed to load daily challenges: {e}")
    
    def reset_progress(self):
        """Сбрасывает прогресс"""
        self.current_set = None
        self.history.clear()
        self.player_xp = 0
        self.player_coins = 0
        self.total_completed = 0
        self.streak_days = 0
        self.last_played_date = None
        
        logger.info("Daily challenges progress reset")


# Глобальный экземпляр
_daily_challenges_manager: Optional[DailyChallengesManager] = None


def get_daily_challenges_manager() -> DailyChallengesManager:
    """Возвращает глобальный менеджер ежедневных испытаний"""
    global _daily_challenges_manager
    if _daily_challenges_manager is None:
        _daily_challenges_manager = DailyChallengesManager()
    return _daily_challenges_manager


def init_daily_challenges_manager(save_path: str = "daily_challenges_save.json") -> DailyChallengesManager:
    """Инициализирует менеджер ежедневных испытаний"""
    global _daily_challenges_manager
    _daily_challenges_manager = DailyChallengesManager(save_path=save_path)
    return _daily_challenges_manager
