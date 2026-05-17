#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game modules package for Tetris Enhanced
"""

from .achievements import (
    AchievementType,
    AchievementTier,
    Achievement,
    UnlockedAchievement,
    AchievementProgress,
    AchievementNotification,
    AchievementsManager,
    get_achievements_manager,
    init_achievements_manager
)

from .particles import (
    ParticleType,
    EmitterShape,
    Particle,
    ParticleEffect,
    ParticleEmitter,
    ParticleSystem,
    get_particle_system,
    init_particle_system
)

from .leaderboard import (
    GameMode,
    ScoreEntry,
    Leaderboard,
    PlayerStats,
    LeaderboardManager,
    get_leaderboard_manager,
    init_leaderboard_manager
)

from .state_manager import (
    GameStateType,
    StateTransition,
    StateConfig,
    GameState,
    MenuState,
    PlayingState,
    PausedState,
    GameOverState,
    SettingsState,
    LeaderboardState,
    AchievementsState,
    StateManager,
    get_state_manager,
    init_state_manager
)

__all__ = [
    # Achievements
    'AchievementType',
    'AchievementTier',
    'Achievement',
    'UnlockedAchievement',
    'AchievementProgress',
    'AchievementNotification',
    'AchievementsManager',
    'get_achievements_manager',
    'init_achievements_manager',

    # Particles
    'ParticleType',
    'EmitterShape',
    'Particle',
    'ParticleEffect',
    'ParticleEmitter',
    'ParticleSystem',
    'get_particle_system',
    'init_particle_system',

    # Leaderboard
    'GameMode',
    'ScoreEntry',
    'Leaderboard',
    'PlayerStats',
    'LeaderboardManager',
    'get_leaderboard_manager',
    'init_leaderboard_manager',

    # State Manager
    'GameStateType',
    'StateTransition',
    'StateConfig',
    'GameState',
    'MenuState',
    'PlayingState',
    'PausedState',
    'GameOverState',
    'SettingsState',
    'LeaderboardState',
    'AchievementsState',
    'StateManager',
    'get_state_manager',
    'init_state_manager'
]
