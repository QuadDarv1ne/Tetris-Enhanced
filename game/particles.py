#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Particle system for game effects in Tetris Enhanced

Features:
- Line clear effects
- Block drop effects
- Rotation effects
- Combo/Tetris celebrations
- Configurable particle emitters
"""

import pygame
import math
import random
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("TetrisEnhanced.Particles")


class ParticleType(Enum):
    """Типы частиц"""
    SPARK = "spark"           # Искра
    GLOW = "glow"             # Свечение
    SQUARE = "square"         # Квадрат
    CIRCLE = "circle"         # Круг
    STAR = "star"             # Звезда
    CONFETTI = "confetti"     # Конфетти
    SMOKE = "smoke"           # Дым
    FIRE = "fire"             # Огонь


class EmitterShape(Enum):
    """Формы эмиттеров"""
    POINT = "point"
    LINE = "line"
    RECT = "rect"
    CIRCLE = "circle"
    RING = "ring"


@dataclass
class Particle:
    """Частица"""
    x: float
    y: float
    vx: float  # Скорость по X
    vy: float  # Скорость по Y
    size: float
    color: Tuple[int, int, int]
    alpha: int = 255
    lifetime: float = 1.0  # секунды
    age: float = 0.0
    particle_type: ParticleType = ParticleType.SPARK
    rotation: float = 0.0
    rotation_speed: float = 0.0
    gravity: float = 0.0
    drag: float = 0.98
    shrink: bool = True
    
    def update(self, dt: float) -> bool:
        """
        Обновляет частицу
        
        Returns:
            True если частица ещё активна
        """
        self.age += dt
        
        if self.age >= self.lifetime:
            return False
        
        # Физика
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        self.vy += self.gravity * dt  # Гравитация
        self.vx *= self.drag  # Сопротивление воздуха
        self.vy *= self.drag
        
        # Вращение
        self.rotation += self.rotation_speed * dt
        
        # Альфа и размер
        life_ratio = 1.0 - (self.age / self.lifetime)
        
        if self.shrink:
            self.size = max(0, self.size * (0.95 ** (dt * 60)))
        
        # Плавное исчезновение
        if life_ratio < 0.3:
            self.alpha = int(255 * (life_ratio / 0.3))
        
        return self.size > 0.5 and self.alpha > 0
    
    def draw(self, surface: pygame.Surface):
        """Рисует частицу"""
        if self.alpha <= 0 or self.size <= 0:
            return
        
        color = (*self.color[:3], self.alpha)
        
        if self.particle_type == ParticleType.SPARK:
            # Рисуем линию (искру)
            end_x = self.x + self.vx * 0.5
            end_y = self.y + self.vy * 0.5
            pygame.draw.line(surface, color, 
                           (int(self.x), int(self.y)),
                           (int(end_x), int(end_y)),
                           int(max(1, self.size)))
        
        elif self.particle_type == ParticleType.CIRCLE:
            pygame.draw.circle(surface, color,
                             (int(self.x), int(self.y)),
                             int(self.size))
        
        elif self.particle_type == ParticleType.SQUARE:
            rect = pygame.Rect(0, 0, int(self.size * 2), int(self.size * 2))
            rect.center = (self.x, self.y)
            
            # Создаём поверхность для вращения
            particle_surface = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
            pygame.draw.rect(particle_surface, color, particle_surface.get_rect())
            
            # Вращаем
            rotated = pygame.transform.rotate(particle_surface, self.rotation)
            surface.blit(rotated, rotated.get_rect(center=(self.x, self.y)))
        
        elif self.particle_type == ParticleType.STAR:
            self._draw_star(surface, color)
        
        elif self.particle_type == ParticleType.CONFETTI:
            self._draw_confetti(surface, color)
        
        elif self.particle_type == ParticleType.GLOW:
            # Рисуем светящийся круг с градиентом
            for i in range(3, 0, -1):
                alpha = self.alpha // (i * 2)
                glow_color = (*self.color[:3], alpha)
                glow_size = int(self.size * i)
                if glow_size > 0:
                    pygame.draw.circle(surface, glow_color,
                                     (int(self.x), int(self.y)),
                                     glow_size)
        
        else:
            # По умолчанию рисуем круг
            pygame.draw.circle(surface, color,
                             (int(self.x), int(self.y)),
                             int(self.size))
    
    def _draw_star(self, surface: pygame.Surface, color: Tuple[int, int, int, int]):
        """Рисует звезду"""
        points = []
        outer_radius = self.size
        inner_radius = self.size * 0.5
        
        for i in range(10):
            angle = math.radians(self.rotation + i * 36)
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = self.x + radius * math.cos(angle)
            y = self.y - radius * math.sin(angle)
            points.append((x, y))
        
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)
    
    def _draw_confetti(self, surface: pygame.Surface, color: Tuple[int, int, int, int]):
        """Рисует конфетти"""
        # Конфетти вращается и меняет форму
        width = self.size * 2
        height = self.size * 0.5
        
        rect = pygame.Rect(0, 0, int(width), int(height))
        rect.center = (self.x, self.y)
        
        particle_surface = pygame.Surface((int(width * 2), int(height * 2)), pygame.SRCALPHA)
        pygame.draw.rect(particle_surface, color, particle_surface.get_rect())
        
        rotated = pygame.transform.rotate(particle_surface, self.rotation)
        surface.blit(rotated, rotated.get_rect(center=(self.x, self.y)))


@dataclass
class ParticleEffect:
    """Конфигурация эффекта частиц"""
    name: str
    particle_type: ParticleType
    count: int
    color: Tuple[int, int, int]
    color_variance: float = 0.2  # Вариация цвета
    speed_min: float = 50
    speed_max: float = 150
    speed_variance: float = 0.3
    size_min: float = 3
    size_max: float = 8
    lifetime_min: float = 0.3
    lifetime_max: float = 1.0
    gravity: float = 100
    drag: float = 0.98
    spread_angle: float = 360  # Угол разброса в градусах
    emitter_shape: EmitterShape = EmitterShape.POINT
    emitter_size: Tuple[float, float] = (0, 0)


class ParticleEmitter:
    """Эмиттер частиц"""
    
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        effect: Optional[ParticleEffect] = None,
        active: bool = True,
        looping: bool = False,
        loop_interval: float = 0.1
    ):
        self.x = x
        self.y = y
        self.effect = effect
        self.active = active
        self.looping = looping
        self.loop_interval = loop_interval
        self.loop_timer = 0.0
        
        self.particles: List[Particle] = []
        self._emit_queue: List[ParticleEffect] = []
    
    def emit(self, effect: Optional[ParticleEffect] = None, count: Optional[int] = None):
        """Добавляет эффект в очередь"""
        if effect:
            self._emit_queue.append(effect)
        elif self.effect:
            if count:
                # Создаём копию эффекта с изменённым количеством
                modified = ParticleEffect(
                    name=self.effect.name,
                    particle_type=self.effect.particle_type,
                    count=count,
                    color=self.effect.color,
                    color_variance=self.effect.color_variance,
                    speed_min=self.effect.speed_min,
                    speed_max=self.effect.speed_max,
                    speed_variance=self.effect.speed_variance,
                    size_min=self.effect.size_min,
                    size_max=self.effect.size_max,
                    lifetime_min=self.effect.lifetime_min,
                    lifetime_max=self.effect.lifetime_max,
                    gravity=self.effect.gravity,
                    drag=self.effect.drag,
                    spread_angle=self.effect.spread_angle,
                    emitter_shape=self.effect.emitter_shape,
                    emitter_size=self.effect.emitter_size
                )
                self._emit_queue.append(modified)
            else:
                self._emit_queue.append(self.effect)
    
    def _spawn_particle(self, effect: ParticleEffect) -> Particle:
        """Создаёт частицу"""
        # Позиция эмиттера
        x, y = self._get_emitter_position(effect)
        
        # Угол и скорость
        base_angle = random.uniform(0, 360) if effect.spread_angle >= 360 else \
                    random.uniform(-effect.spread_angle / 2, effect.spread_angle / 2)
        
        speed = random.uniform(effect.speed_min, effect.speed_max)
        angle_rad = math.radians(base_angle)
        
        vx = math.cos(angle_rad) * speed
        vy = math.sin(angle_rad) * speed
        
        # Размер
        size = random.uniform(effect.size_min, effect.size_max)
        
        # Цвет с вариацией
        color = self._vary_color(effect.color, effect.color_variance)
        
        # Время жизни
        lifetime = random.uniform(effect.lifetime_min, effect.lifetime_max)
        
        return Particle(
            x=x, y=y,
            vx=vx, vy=vy,
            size=size,
            color=color,
            alpha=255,
            lifetime=lifetime,
            age=0.0,
            particle_type=effect.particle_type,
            rotation=random.uniform(0, 360),
            rotation_speed=random.uniform(-180, 180),
            gravity=effect.gravity,
            drag=effect.drag,
            shrink=True
        )
    
    def _get_emitter_position(self, effect: ParticleEffect) -> Tuple[float, float]:
        """Получает позицию спавна частицы"""
        if effect.emitter_shape == EmitterShape.POINT:
            return self.x, self.y
        
        elif effect.emitter_shape == EmitterShape.LINE:
            t = random.uniform(0, 1)
            return (self.x + t * effect.emitter_size[0],
                   self.y + t * effect.emitter_size[1])
        
        elif effect.emitter_shape == EmitterShape.RECT:
            return (self.x + random.uniform(-effect.emitter_size[0] / 2, effect.emitter_size[0] / 2),
                   self.y + random.uniform(-effect.emitter_size[1] / 2, effect.emitter_size[1] / 2))
        
        elif effect.emitter_shape == EmitterShape.CIRCLE:
            angle = random.uniform(0, 360)
            radius = random.uniform(0, effect.emitter_size[0])
            return (self.x + radius * math.cos(math.radians(angle)),
                   self.y - radius * math.sin(math.radians(angle)))
        
        elif effect.emitter_shape == EmitterShape.RING:
            angle = random.uniform(0, 360)
            radius = effect.emitter_size[0]
            return (self.x + radius * math.cos(math.radians(angle)),
                   self.y - radius * math.sin(math.radians(angle)))
        
        return self.x, self.y
    
    def _vary_color(self, color: Tuple[int, int, int], variance: float) -> Tuple[int, int, int]:
        """Вариация цвета"""
        if variance <= 0:
            return color
        
        factor = 1.0 + random.uniform(-variance, variance)
        return (
            max(0, min(255, int(color[0] * factor))),
            max(0, min(255, int(color[1] * factor))),
            max(0, min(255, int(color[2] * factor)))
        )
    
    def update(self, dt: float):
        """Обновляет эмиттер"""
        if not self.active:
            return
        
        # Обработка очереди эффектов
        while self._emit_queue:
            effect = self._emit_queue.pop(0)
            for _ in range(effect.count):
                self.particles.append(self._spawn_particle(effect))
        
        # Looping
        if self.looping and self.effect:
            self.loop_timer += dt
            if self.loop_timer >= self.loop_interval:
                self.loop_timer = 0
                self.emit()
        
        # Обновление частиц
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self, surface: pygame.Surface):
        """Рисует все частицы"""
        for particle in self.particles:
            particle.draw(surface)
    
    def is_alive(self) -> bool:
        """Проверяет, есть ли активные частицы"""
        return len(self.particles) > 0 or len(self._emit_queue) > 0
    
    def clear(self):
        """Очищает все частицы"""
        self.particles.clear()
        self._emit_queue.clear()


class ParticleSystem:
    """
    Система частиц для управления всеми эффектами
    
    Usage:
        particles = ParticleSystem()
        
        # Добавить эффект
        particles.emit_at(x, y, LINE_CLEAR_EFFECT)
        
        # В игровом цикле
        particles.update(dt)
        particles.draw(screen)
    """
    
    # Предустановленные эффекты
    EFFECTS = {
        'line_clear': ParticleEffect(
            name='line_clear',
            particle_type=ParticleType.SPARK,
            count=30,
            color=(255, 215, 0),  # Gold
            speed_min=100,
            speed_max=300,
            size_min=4,
            size_max=10,
            lifetime_min=0.4,
            lifetime_max=0.8,
            gravity=200,
            spread_angle=180
        ),
        
        'tetris': ParticleEffect(
            name='tetris',
            particle_type=ParticleType.STAR,
            count=100,
            color=(0, 255, 255),  # Cyan
            color_variance=0.3,
            speed_min=150,
            speed_max=400,
            size_min=6,
            size_max=15,
            lifetime_min=0.8,
            lifetime_max=1.5,
            gravity=150,
            spread_angle=360
        ),
        
        'combo': ParticleEffect(
            name='combo',
            particle_type=ParticleType.CONFETTI,
            count=50,
            color=(255, 105, 180),  # Hot Pink
            color_variance=0.5,
            speed_min=80,
            speed_max=200,
            size_min=5,
            size_max=12,
            lifetime_min=0.6,
            lifetime_max=1.2,
            gravity=100,
            spread_angle=360
        ),
        
        'drop': ParticleEffect(
            name='drop',
            particle_type=ParticleType.GLOW,
            count=15,
            color=(200, 200, 255),
            speed_min=50,
            speed_max=100,
            size_min=3,
            size_max=6,
            lifetime_min=0.2,
            lifetime_max=0.4,
            gravity=0,
            spread_angle=90
        ),
        
        'rotate': ParticleEffect(
            name='rotate',
            particle_type=ParticleType.CIRCLE,
            count=8,
            color=(255, 255, 255),
            speed_min=30,
            speed_max=80,
            size_min=2,
            size_max=4,
            lifetime_min=0.15,
            lifetime_max=0.3,
            gravity=0,
            spread_angle=360
        ),
        
        't_spin': ParticleEffect(
            name='t_spin',
            particle_type=ParticleType.FIRE,
            count=60,
            color=(255, 69, 0),  # Red Orange
            color_variance=0.4,
            speed_min=100,
            speed_max=250,
            size_min=5,
            size_max=12,
            lifetime_min=0.5,
            lifetime_max=1.0,
            gravity=-50,  # Вверх
            spread_angle=360
        ),
        
        'level_up': ParticleEffect(
            name='level_up',
            particle_type=ParticleType.STAR,
            count=80,
            color=(255, 215, 0),  # Gold
            color_variance=0.3,
            speed_min=120,
            speed_max=300,
            size_min=8,
            size_max=20,
            lifetime_min=1.0,
            lifetime_max=2.0,
            gravity=80,
            spread_angle=360
        ),
        
        'game_over': ParticleEffect(
            name='game_over',
            particle_type=ParticleType.SMOKE,
            count=40,
            color=(100, 100, 100),
            color_variance=0.2,
            speed_min=30,
            speed_max=80,
            size_min=10,
            size_max=30,
            lifetime_min=1.0,
            lifetime_max=2.0,
            gravity=-30,
            spread_angle=360
        ),
    }
    
    def __init__(self, max_particles: int = 2000):
        self.max_particles = max_particles
        self.emitters: Dict[str, ParticleEmitter] = {}
        self.global_particles: List[Particle] = []
        
        # Статистика
        self.total_emitted = 0
        self.total_updated = 0
    
    def create_emitter(
        self,
        name: str,
        x: float = 0,
        y: float = 0,
        effect: Optional[ParticleEffect] = None,
        looping: bool = False,
        loop_interval: float = 0.1
    ) -> ParticleEmitter:
        """Создаёт эмиттер"""
        emitter = ParticleEmitter(
            x=x, y=y,
            effect=effect,
            looping=looping,
            loop_interval=loop_interval
        )
        self.emitters[name] = emitter
        return emitter
    
    def remove_emitter(self, name: str):
        """Удаляет эмиттер"""
        if name in self.emitters:
            self.emitters[name].clear()
            del self.emitters[name]
    
    def emit_at(
        self,
        x: float,
        y: float,
        effect_name: str,
        count: Optional[int] = None
    ):
        """Создаёт эффект в указанной позиции"""
        if effect_name not in self.EFFECTS:
            logger.warning(f"Unknown effect: {effect_name}")
            return
        
        effect = self.EFFECTS[effect_name]
        
        # Создаём временный эмиттер
        emitter = ParticleEmitter(x=x, y=y, effect=effect)
        emitter.emit(count=count)
        
        # Сразу обновляем и добавляем частицы в глобальный список
        emitter.update(0)
        self.global_particles.extend(emitter.particles)
        
        self.total_emitted += len(emitter.particles)
    
    def emit_line_clear(self, x: int, y: int, width: int, lines: int = 1):
        """Эффект очистки линии"""
        effect = self.EFFECTS['line_clear']
        
        for i in range(lines):
            line_y = y - (i * 30)
            
            # Создаём эмиттер линии
            emitter = ParticleEmitter(
                x=x, y=line_y,
                effect=effect,
                emitter_shape=EmitterShape.LINE,
                emitter_size=(width, 0)
            )
            emitter.emit()
            emitter.update(0)
            self.global_particles.extend(emitter.particles)
    
    def update(self, dt: float):
        """Обновляет все частицы"""
        # Обновляем эмиттеры
        for emitter in list(self.emitters.values()):
            emitter.update(dt)
            if not emitter.is_alive() and not emitter.looping:
                # Удаляем неактивные эмиттеры
                pass  # Оставляем для возможного повторного использования
        
        # Обновляем глобальные частицы
        self.global_particles = [p for p in self.global_particles if p.update(dt)]
        self.total_updated += len(self.global_particles)
        
        # Ограничиваем количество частиц
        if len(self.global_particles) > self.max_particles:
            # Удаляем старые частицы
            self.global_particles = self.global_particles[-self.max_particles:]
    
    def draw(self, surface: pygame.Surface):
        """Рисует все частицы"""
        # Рисуем частицы из эмиттеров
        for emitter in self.emitters.values():
            emitter.draw(surface)
        
        # Рисуем глобальные частицы
        for particle in self.global_particles:
            particle.draw(surface)
    
    def clear(self):
        """Очищает все частицы"""
        for emitter in self.emitters.values():
            emitter.clear()
        self.global_particles.clear()
    
    def get_stats(self) -> dict:
        """Возвращает статистику"""
        return {
            'active_emitters': len([e for e in self.emitters.values() if e.is_alive()]),
            'total_emitters': len(self.emitters),
            'active_particles': len(self.global_particles) + \
                               sum(len(e.particles) for e in self.emitters.values()),
            'total_emitted': self.total_emitted,
            'total_updated': self.total_updated
        }


# Глобальный экземпляр
_particle_system: Optional[ParticleSystem] = None


def get_particle_system() -> ParticleSystem:
    """Возвращает глобальную систему частиц"""
    global _particle_system
    if _particle_system is None:
        _particle_system = ParticleSystem()
    return _particle_system


def init_particle_system(max_particles: int = 2000) -> ParticleSystem:
    """Инициализирует систему частиц"""
    global _particle_system
    _particle_system = ParticleSystem(max_particles=max_particles)
    return _particle_system
