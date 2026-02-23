#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility modules for Tetris Enhanced

This package provides:
- logger: Enhanced logging and error handling
- performance: Performance monitoring and optimization
"""

from .logger import (
    EnhancedLogger,
    LogContext,
    LogLevel,
    log_function_call,
    safe_call,
    get_logger,
    init_logger,
    log_debug,
    log_info,
    log_warning,
    log_error,
    log_critical
)

from .performance import (
    PerformanceMonitor,
    PerformanceMetrics,
    LRUCache,
    ResourcePool,
    profile_function,
    limit_fps,
    get_performance_monitor,
    init_performance_monitor
)

__all__ = [
    # Logger
    'EnhancedLogger',
    'LogContext',
    'LogLevel',
    'log_function_call',
    'safe_call',
    'get_logger',
    'init_logger',
    'log_debug',
    'log_info',
    'log_warning',
    'log_error',
    'log_critical',
    
    # Performance
    'PerformanceMonitor',
    'PerformanceMetrics',
    'LRUCache',
    'ResourcePool',
    'profile_function',
    'limit_fps',
    'get_performance_monitor',
    'init_performance_monitor'
]
