#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance monitoring and optimization utilities for Tetris Enhanced
"""

import time
import psutil
import os
from typing import Dict, List, Optional, Any, Callable, TypeVar, ParamSpec
from dataclasses import dataclass, field
from collections import deque
from functools import wraps
import threading

P = ParamSpec('P')
R = TypeVar('R')


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    fps: float = 0.0
    frame_time_ms: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    update_time_ms: float = 0.0
    render_time_ms: float = 0.0
    
    # Статистика за последние N кадров
    fps_history: deque = field(default_factory=lambda: deque(maxlen=60))
    frame_time_history: deque = field(default_factory=lambda: deque(maxlen=60))
    
    def update(self, fps: float, frame_time_ms: float):
        """Обновляет метрики"""
        self.fps = fps
        self.frame_time_ms = frame_time_ms
        self.fps_history.append(fps)
        self.frame_time_history.append(frame_time_ms)
        
        # Обновляем системные метрики
        try:
            self.cpu_percent = psutil.Process().cpu_percent()
            self.memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        except Exception:
            pass
    
    def get_average_fps(self) -> float:
        """Возвращает средний FPS за последние 60 кадров"""
        if not self.fps_history:
            return self.fps
        return sum(self.fps_history) / len(self.fps_history)
    
    def get_average_frame_time(self) -> float:
        """Возвращает среднее время кадра"""
        if not self.frame_time_history:
            return self.frame_time_ms
        return sum(self.frame_time_history) / len(self.frame_time_history)
    
    def to_dict(self) -> dict:
        """Возвращает метрики как словарь"""
        return {
            'fps': self.fps,
            'avg_fps': self.get_average_fps(),
            'frame_time_ms': self.frame_time_ms,
            'avg_frame_time_ms': self.get_average_frame_time(),
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'update_time_ms': self.update_time_ms,
            'render_time_ms': self.render_time_ms
        }


class PerformanceMonitor:
    """
    Монитор производительности для:
    - Отслеживания FPS
    - Профилирования времени выполнения
    - Обнаружения проблем производительности
    """

    def __init__(self, history_size: int = 60):
        self.metrics = PerformanceMetrics()
        self.history_size = history_size
        
        # Временные метки
        self._frame_start = 0.0
        self._last_fps_update = 0.0
        self._frame_count = 0
        
        # Профилировщик
        self._profiling_data: Dict[str, List[float]] = {}
        
        # Пороги предупреждений
        self.fps_warning_threshold = 30
        self.frame_time_warning_threshold = 50  # мс
        self.cpu_warning_threshold = 80  # процент
        self.memory_warning_threshold = 500  # MB
        
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()

    def start_frame(self):
        """Начинает измерение кадра"""
        self._frame_start = time.perf_counter()

    def end_frame(self):
        """Завершает измерение кадра и обновляет метрики"""
        frame_time = (time.perf_counter() - self._frame_start) * 1000  # мс
        self._frame_count += 1
        
        # Обновляем FPS каждые 0.5 секунды
        current_time = time.time()
        if current_time - self._last_fps_update >= 0.5:
            elapsed = current_time - self._last_fps_update
            fps = self._frame_count / elapsed if elapsed > 0 else 0
            self.metrics.update(fps, frame_time)
            self._frame_count = 0
            self._last_fps_update = current_time

    def start_profile(self, category: str):
        """Начинает профилирование категории"""
        if category not in self._profiling_data:
            self._profiling_data[category] = []
        self._profiling_data[category].append(time.perf_counter())

    def end_profile(self, category: str) -> float:
        """
        Завершает профилирование и возвращает время выполнения
        
        Returns:
            Время выполнения в миллисекундах
        """
        if category not in self._profiling_data or not self._profiling_data[category]:
            return 0.0
        
        start_time = self._profiling_data[category].pop()
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Сохраняем в метрики
        if category == 'update':
            self.metrics.update_time_ms = elapsed_ms
        elif category == 'render':
            self.metrics.render_time_ms = elapsed_ms
        
        return elapsed_ms

    def get_profile_stats(self) -> Dict[str, Dict[str, float]]:
        """Возвращает статистику профилирования"""
        stats = {}
        for category, times in self._profiling_data.items():
            if times:
                stats[category] = {
                    'current_ms': (time.perf_counter() - times[-1]) * 1000 if times else 0,
                    'avg_ms': sum(times) / len(times) * 1000 if times else 0,
                    'max_ms': max(times) * 1000 if times else 0,
                    'min_ms': min(times) * 1000 if times else 0,
                    'count': len(times)
                }
        return stats

    def check_warnings(self) -> List[str]:
        """Проверяет метрики на наличие проблем"""
        warnings = []
        
        m = self.metrics
        
        if m.fps < self.fps_warning_threshold:
            warnings.append(f"Низкий FPS: {m.fps:.1f} (порог: {self.fps_warning_threshold})")
        
        if m.frame_time_ms > self.frame_time_warning_threshold:
            warnings.append(f"Высокое время кадра: {m.frame_time_ms:.2f}мс (порог: {self.frame_time_warning_threshold}мс)")
        
        if m.cpu_percent > self.cpu_warning_threshold:
            warnings.append(f"Высокое использование CPU: {m.cpu_percent:.1f}%")
        
        if m.memory_mb > self.memory_warning_threshold:
            warnings.append(f"Высокое использование памяти: {m.memory_mb:.1f}MB")
        
        return warnings

    def reset(self):
        """Сбрасывает все метрики"""
        self.metrics = PerformanceMetrics()
        self._frame_count = 0
        self._profiling_data.clear()


class LRUCache:
    """
    LRU (Least Recently Used) кэш с ограниченным размером
    Оптимизирован для хранения поверхностей, шрифтов и других ресурсов
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: Dict[Any, Any] = {}
        self._access_order: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        
        # Статистика
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: Any) -> Optional[Any]:
        """Получает значение из кэша"""
        with self._lock:
            if key in self._cache:
                # Перемещаем в конец (свежий доступ)
                self._access_order.remove(key)
                self._access_order.append(key)
                self.hits += 1
                return self._cache[key]
            
            self.misses += 1
            return None

    def put(self, key: Any, value: Any):
        """Добавляет значение в кэш"""
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
            elif len(self._cache) >= self.max_size:
                # Удаляем наименее используемый элемент
                oldest_key = self._access_order.popleft()
                del self._cache[oldest_key]
                self.evictions += 1
            
            self._cache[key] = value
            self._access_order.append(key)

    def remove(self, key: Any):
        """Удаляет значение из кэша"""
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
                del self._cache[key]

    def clear(self):
        """Очищает кэш"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def get_stats(self) -> dict:
        """Возвращает статистику кэша"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate_percent': round(hit_rate, 2)
        }

    def __contains__(self, key: Any) -> bool:
        with self._lock:
            return key in self._cache

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)


class ResourcePool:
    """
    Пул ресурсов для повторного использования объектов
    Полезно для часто создаваемых/уничтожаемых объектов
    """

    def __init__(self, factory: Callable[[], Any], max_size: int = 50):
        """
        Args:
            factory: Функция для создания новых объектов
            max_size: Максимальный размер пула
        """
        self.factory = factory
        self.max_size = max_size
        self._available: List[Any] = []
        self._in_use: set = set()
        self._lock = threading.Lock()
        
        # Статистика
        self.created_count = 0
        self.reused_count = 0

    def acquire(self) -> Any:
        """Получает объект из пула"""
        with self._lock:
            if self._available:
                obj = self._available.pop()
                self._in_use.add(id(obj))
                self.reused_count += 1
                return obj
            
            # Создаём новый объект
            obj = self.factory()
            self._in_use.add(id(obj))
            self.created_count += 1
            return obj

    def release(self, obj: Any):
        """Возвращает объект в пул"""
        with self._lock:
            obj_id = id(obj)
            if obj_id in self._in_use:
                self._in_use.discard(obj_id)
                
                if len(self._available) < self.max_size:
                    # Сбрасываем состояние объекта если нужно
                    if hasattr(obj, 'reset'):
                        obj.reset()
                    self._available.append(obj)

    def get_stats(self) -> dict:
        """Возвращает статистику пула"""
        return {
            'available': len(self._available),
            'in_use': len(self._in_use),
            'created': self.created_count,
            'reused': self.reused_count,
            'reuse_rate': self.reused_count / (self.created_count + self.reused_count) * 100
            if (self.created_count + self.reused_count) > 0 else 0
        }


def profile_function(
    monitor: Optional[PerformanceMonitor] = None,
    category: str = "default"
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор для профилирования функции
    
    Usage:
        @profile_function(monitor, category="render")
        def render_game():
            ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if monitor:
                monitor.start_profile(category)
            
            try:
                return func(*args, **kwargs)
            finally:
                if monitor:
                    monitor.end_profile(category)
        
        return wrapper
    return decorator


def limit_fps(max_fps: int = 60) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор для ограничения FPS функции
    
    Usage:
        @limit_fps(60)
        def game_loop():
            ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            frame_time = 1.0 / max_fps
            start = time.perf_counter()
            
            result = func(*args, **kwargs)
            
            elapsed = time.perf_counter() - start
            sleep_time = frame_time - elapsed
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            return result
        
        return wrapper
    return decorator


# Глобальный монитор производительности
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Возвращает глобальный монитор производительности"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def init_performance_monitor(history_size: int = 60) -> PerformanceMonitor:
    """Инициализирует монитор производительности"""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(history_size=history_size)
    return _performance_monitor
