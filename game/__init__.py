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

from .daily_challenges import (
    ChallengeType,
    ChallengeTier,
    Challenge,
    DailyChallengeSet,
    ChallengeGenerator,
    DailyChallengesManager,
    get_daily_challenges_manager,
    init_daily_challenges_manager
)

from .state_manager import (
    GameStateType,
    GameState,
    StateManager,
    MenuState,
    PlayingState,
    PausedState,
    GameOverState,
    get_state_manager,
    init_state_manager
)

from .integration import (
    GameIntegration,
    get_integration,
    init_integration
)

from .player_stats import (
    PieceStatistics,
    SessionStatistics,
    CareerStatistics,
    PlayerStatisticsManager,
    get_player_statistics_manager,
    init_player_statistics_manager
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

    # Daily Challenges
    'ChallengeType',
    'ChallengeTier',
    'Challenge',
    'DailyChallengeSet',
    'ChallengeGenerator',
    'DailyChallengesManager',
    'get_daily_challenges_manager',
    'init_daily_challenges_manager',

    # State Manager
    'GameStateType',
    'GameState',
    'StateManager',
    'MenuState',
    'PlayingState',
    'PausedState',
    'GameOverState',
    'get_state_manager',
    'init_state_manager',

    # Integration
    'GameIntegration',
    'get_integration',
    'init_integration',

    # Player Statistics
    'PieceStatistics',
    'SessionStatistics',
    'CareerStatistics',
    'PlayerStatisticsManager',
    'get_player_statistics_manager',
    'init_player_statistics_manager'
]
