#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced UI components with effects and animations for Tetris Enhanced
"""

import pygame
import math
from typing import Tuple, List, Optional, Callable, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger("TetrisEnhanced.UI")


class UIColor:
    """Расширенная палитра цветов"""
    # Основные цвета
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    LIGHT_GRAY = (192, 192, 192)
    
    # Цвета темы
    PRIMARY = (70, 130, 180)      # Steel Blue
    PRIMARY_LIGHT = (100, 149, 237)  # Cornflower Blue
    PRIMARY_DARK = (65, 105, 225)    # Royal Blue
    
    SECONDARY = (147, 112, 219)   # Purple
    ACCENT = (255, 105, 180)      # Hot Pink
    
    # Цвета состояний
    SUCCESS = (0, 255, 127)       # Spring Green
    WARNING = (255, 215, 0)       # Gold
    ERROR = (255, 69, 0)          # Red Orange
    INFO = (0, 191, 255)          # Deep Sky Blue
    
    # Цвета для игрового поля
    GRID_BG = (20, 20, 20)
    GRID_BORDER = (100, 100, 100)
    
    # Цвета тетромино
    TETROMINO_COLORS = {
        'I': (0, 255, 255),    # Cyan
        'O': (255, 255, 0),    # Yellow
        'T': (128, 0, 128),    # Purple
        'S': (0, 255, 0),      # Green
        'Z': (255, 0, 0),      # Red
        'J': (0, 0, 255),      # Blue
        'L': (255, 165, 0),    # Orange
    }
    
    # Градиенты
    BG_GRADIENT_TOP = (30, 30, 50)
    BG_GRADIENT_BOTTOM = (10, 10, 20)
    
    @staticmethod
    def lerp(color1: Tuple[int, int, int], color2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        """Линейная интерполяция между цветами"""
        return (
            int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t)
        )
    
    @staticmethod
    def lighten(color: Tuple[int, int, int], factor: float = 0.2) -> Tuple[int, int, int]:
        """Осветляет цвет"""
        return (
            min(255, int(color[0] * (1 + factor))),
            min(255, int(color[1] * (1 + factor))),
            min(255, int(color[2] * (1 + factor)))
        )
    
    @staticmethod
    def darken(color: Tuple[int, int, int], factor: float = 0.2) -> Tuple[int, int, int]:
        """Затемняет цвет"""
        return (
            max(0, int(color[0] * (1 - factor))),
            max(0, int(color[1] * (1 - factor))),
            max(0, int(color[2] * (1 - factor)))
        )


class AnimationState(Enum):
    """Состояния анимации"""
    IDLE = "idle"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"
    ANIMATING = "animating"


class EasingFunctions:
    """Функции плавности для анимаций"""
    
    @staticmethod
    def linear(t: float) -> float:
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        return t * (2 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return t * t if t < 0.5 else -1 + (4 - 2 * t) * t
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 + (t - 1) ** 3
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            return n1 * (t - 1.5 / d1) ** 2 + 0.75
        elif t < 2.5 / d1:
            return n1 * (t - 2.25 / d1) ** 2 + 0.9375
        else:
            return n1 * (t - 2.625 / d1) ** 2 + 0.984375
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        if t == 0:
            return 0
        if t == 1:
            return 1
        c4 = (2 * math.pi) / 3
        return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


class AnimatedButton:
    """
    Улучшенная кнопка с анимациями и эффектами
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        font: pygame.font.Font,
        callback: Optional[Callable] = None,
        enabled: bool = True,
        colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
        border_radius: int = 8,
        animation_speed: float = 0.15,
        icon: Optional[pygame.Surface] = None
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.enabled = enabled
        self.border_radius = border_radius
        self.icon = icon
        
        # Цвета
        self.colors = colors or {
            'normal': UIColor.PRIMARY,
            'hover': UIColor.PRIMARY_LIGHT,
            'pressed': UIColor.PRIMARY_DARK,
            'disabled': UIColor.DARK_GRAY,
            'text': UIColor.WHITE,
            'text_disabled': UIColor.GRAY,
            'border': UIColor.WHITE
        }
        
        # Состояния
        self.animation_state = AnimationState.IDLE
        self.hovered = False
        self.pressed = False
        self.animation_progress = 0.0
        self.animation_speed = animation_speed
        
        # Эффекты
        self.scale_factor = 1.0
        self.target_scale_factor = 1.0
        self.glow_intensity = 0.0
        self.particle_system: Optional['ButtonParticles'] = None
        
        # Позиционирование текста
        self._update_text_surface()
        
        # Тень текста
        self.text_shadow_offset = (2, 2)
        self.enable_text_shadow = True

    def _update_text_surface(self):
        """Обновляет поверхность текста"""
        color = self.colors['text'] if self.enabled else self.colors['text_disabled']
        self.text_surface = self.font.render(self.text, True, color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Обрабатывает события"""
        if not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.hovered
            self.hovered = self.rect.collidepoint(event.pos)
            
            if self.hovered and not was_hovered:
                self.animation_state = AnimationState.HOVER
                self.particle_system = ButtonParticles(self.rect.center, color=self.colors['hover'])
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                self.pressed = True
                self.animation_state = AnimationState.PRESSED
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.pressed and self.hovered and self.callback:
                    self.callback()
                self.pressed = False
                self.animation_state = AnimationState.HOVER if self.hovered else AnimationState.IDLE
                return self.hovered
        
        return False

    def update(self, dt: float):
        """Обновляет анимации"""
        # Анимация перехода состояний
        if self.animation_state == AnimationState.HOVER:
            self.target_scale_factor = 1.05
            self.animation_progress = min(1.0, self.animation_progress + self.animation_speed * dt * 60)
            self.glow_intensity = 0.3 + 0.2 * math.sin(pygame.time.get_ticks() * 0.01)
        elif self.animation_state == AnimationState.PRESSED:
            self.target_scale_factor = 0.95
            self.animation_progress = 1.0
            self.glow_intensity = 0.5
        else:
            self.target_scale_factor = 1.0
            self.animation_progress = max(0.0, self.animation_progress - self.animation_speed * dt * 60)
            self.glow_intensity = max(0.0, self.glow_intensity - 0.05 * dt * 60)
        
        # Плавное масштабирование
        self.scale_factor += (self.target_scale_factor - self.scale_factor) * 0.3
        
        # Обновляем частицы
        if self.particle_system:
            self.particle_system.update(dt)
            if self.particle_system.is_dead():
                self.particle_system = None

    def draw(self, surface: pygame.Surface):
        """Рисует кнопку"""
        # Сохраняем исходную позицию
        original_center = self.rect.center
        
        # Применяем масштабирование
        if self.scale_factor != 1.0:
            new_width = int(self.rect.width * self.scale_factor)
            new_height = int(self.rect.height * self.scale_factor)
            self.rect = pygame.Rect(
                original_center[0] - new_width // 2,
                original_center[1] - new_height // 2,
                new_width,
                new_height
            )
        
        # Определяем цвет
        if not self.enabled:
            color = self.colors['disabled']
        elif self.pressed:
            color = self.colors['pressed']
        elif self.hovered:
            # Интерполяция между normal и hover
            t = EasingFunctions.ease_out_quad(self.animation_progress)
            color = UIColor.lerp(self.colors['normal'], self.colors['hover'], t)
        else:
            color = self.colors['normal']
        
        # Рисуем эффект свечения
        if self.glow_intensity > 0.01:
            glow_rect = self.rect.inflate(10, 10)
            glow_color = (*color[:3], int(50 * self.glow_intensity))
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*color, int(50 * self.glow_intensity)), 
                           glow_surface.get_rect(), border_radius=self.border_radius + 5)
            surface.blit(glow_surface, glow_rect.topleft)
        
        # Рисуем фон кнопки
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        
        # Рисуем границу
        pygame.draw.rect(surface, self.colors['border'], self.rect, 2, border_radius=self.border_radius)
        
        # Рисуем иконку если есть
        if self.icon:
            icon_rect = self.icon.get_rect(midleft=(self.rect.x + 15, self.rect.centery))
            surface.blit(self.icon, icon_rect)
            text_offset = self.icon.get_width() + 10
        else:
            text_offset = 0
        
        # Рисуем тень текста
        if self.enable_text_shadow:
            shadow_surface = self.font.render(self.text, True, UIColor.BLACK)
            surface.blit(shadow_surface, 
                        (self.text_rect.x + self.text_shadow_offset[0] + text_offset // 2,
                         self.text_rect.y + self.text_shadow_offset[1]))
        
        # Рисуем текст
        text_color = self.colors['text'] if self.enabled else self.colors['text_disabled']
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        text_rect.x += text_offset // 2
        surface.blit(text_surface, text_rect)
        
        # Рисуем частицы
        if self.particle_system:
            self.particle_system.draw(surface)
        
        # Восстанавливаем исходную позицию
        self.rect.center = original_center

    def set_enabled(self, enabled: bool):
        """Устанавливает состояние доступности"""
        self.enabled = enabled
        self.animation_state = AnimationState.DISABLED if not enabled else AnimationState.IDLE
        self._update_text_surface()


class ButtonParticles:
    """Система частиц для кнопок"""
    
    def __init__(self, center: Tuple[int, int], color: Tuple[int, int, int], count: int = 8):
        self.center = center
        self.color = color
        self.particles = []
        self.lifetime = 0.5  # секунды
        self.age = 0.0
        
        # Создаём частицы
        for i in range(count):
            angle = (360 / count) * i * math.pi / 180
            speed = 50 + 30 * (i % 3)
            self.particles.append({
                'x': center[0],
                'y': center[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': 3 + 2 * (i % 3),
                'alpha': 255
            })
    
    def update(self, dt: float):
        """Обновляет частицы"""
        self.age += dt
        
        for particle in self.particles:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vy'] += 200 * dt  # Гравитация
            particle['alpha'] = max(0, 255 * (1 - self.age / self.lifetime))
    
    def draw(self, surface: pygame.Surface):
        """Рисует частицы"""
        for particle in self.particles:
            if particle['alpha'] <= 0:
                continue
            
            color = (*self.color[:3], int(particle['alpha']))
            pygame.draw.circle(surface, color, 
                             (int(particle['x']), int(particle['y'])), 
                             int(particle['size']))
    
    def is_dead(self) -> bool:
        """Проверяет, закончились ли частицы"""
        return self.age >= self.lifetime


class ToggleButton(AnimatedButton):
    """Кнопка-переключатель"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_toggled = False
        self.toggled_colors = {
            'normal': UIColor.SUCCESS,
            'hover': UIColor.lerp(UIColor.SUCCESS, UIColor.WHITE, 0.2),
            'pressed': UIColor.lerp(UIColor.SUCCESS, UIColor.BLACK, 0.2)
        }
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Обрабатывает события"""
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.hovered:
                self.is_toggled = not self.is_toggled
                if self.callback:
                    self.callback(self.is_toggled)
                return True
        return super().handle_event(event)
    
    def draw(self, surface: pygame.Surface):
        """Рисует переключатель"""
        if self.is_toggled:
            original_colors = self.colors.copy()
            self.colors.update(self.toggled_colors)
            super().draw(surface)
            self.colors.update(original_colors)
        else:
            super().draw(surface)


class IconButton(AnimatedButton):
    """Кнопка с иконкой"""
    
    def __init__(self, *args, icon_path: Optional[str] = None, icon_size: Tuple[int, int] = (24, 24), **kwargs):
        super().__init__(*args, **kwargs)
        self.icon_size = icon_size
        
        if icon_path:
            try:
                self.icon = pygame.image.load(icon_path)
                self.icon = pygame.transform.smoothscale(self.icon, icon_size)
            except Exception as e:
                logger.warning(f"Failed to load icon {icon_path}: {e}")
                self.icon = None
        else:
            self.icon = None


class ProgressBar:
    """Улучшенный прогресс-бар с анимациями"""
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        min_value: float = 0.0,
        max_value: float = 1.0,
        initial_value: float = 0.0,
        colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
        show_text: bool = True,
        font: Optional[pygame.font.Font] = None,
        border_radius: int = 4
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.animated_value = initial_value
        self.border_radius = border_radius
        self.show_text = show_text
        self.font = font
        
        self.colors = colors or {
            'background': UIColor.DARK_GRAY,
            'foreground': UIColor.PRIMARY,
            'border': UIColor.WHITE,
            'text': UIColor.WHITE
        }
        
        # Анимация
        self.animation_speed = 0.1
        self.pulse_intensity = 0.0
        self.pulse_direction = 1

    def set_value(self, value: float, animate: bool = True):
        """Устанавливает значение"""
        self.value = max(self.min_value, min(self.max_value, value))
        if not animate:
            self.animated_value = self.value

    def get_percentage(self) -> float:
        """Возвращает процент"""
        if self.max_value == self.min_value:
            return 0.0
        return (self.value - self.min_value) / (self.max_value - self.min_value)

    def update(self, dt: float):
        """Обновляет анимацию"""
        # Плавная анимация значения
        self.animated_value += (self.value - self.animated_value) * self.animation_speed * dt * 60
        
        # Пульсация при заполнении
        if self.get_percentage() >= 1.0:
            self.pulse_intensity += 0.02 * self.pulse_direction
            if self.pulse_intensity > 0.3 or self.pulse_intensity < 0:
                self.pulse_direction *= -1

    def draw(self, surface: pygame.Surface):
        """Рисует прогресс-бар"""
        # Фон
        pygame.draw.rect(surface, self.colors['background'], self.rect, border_radius=self.border_radius)
        
        # Прогресс
        progress_width = int(self.rect.width * self.get_percentage())
        if progress_width > 0:
            progress_rect = pygame.Rect(
                self.rect.x,
                self.rect.y,
                progress_width,
                self.rect.height
            )
            
            # Цвет с пульсацией
            color = self.colors['foreground']
            if self.pulse_intensity > 0:
                color = UIColor.lerp(color, UIColor.WHITE, self.pulse_intensity)
            
            pygame.draw.rect(surface, color, progress_rect, border_radius=self.border_radius)
        
        # Граница
        pygame.draw.rect(surface, self.colors['border'], self.rect, 2, border_radius=self.border_radius)
        
        # Текст
        if self.show_text and self.font:
            percentage_text = f"{self.get_percentage() * 100:.1f}%"
            text_surface = self.font.render(percentage_text, True, self.colors['text'])
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)


class LoadingSpinner:
    """Анимированный индикатор загрузки"""
    
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 40,
        color: Tuple[int, int, int] = UIColor.PRIMARY,
        line_width: int = 4
    ):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.line_width = line_width
        self.rotation = 0
        self.speed = 180  # градусов в секунду

    def update(self, dt: float):
        """Обновляет вращение"""
        self.rotation = (self.rotation + self.speed * dt) % 360

    def draw(self, surface: pygame.Surface):
        """Рисует спиннер"""
        center = (self.x, self.y)
        radius = self.size // 2
        
        for i in range(12):
            angle = self.rotation + i * 30
            alpha = int(255 * (0.3 + 0.7 * ((i + 1) / 12)))
            
            # Вычисляем точки линии
            start_angle = angle * math.pi / 180
            end_angle = (angle + 20) * math.pi / 180
            
            start_pos = (
                center[0] + int(radius * 0.5 * math.cos(start_angle)),
                center[1] - int(radius * 0.5 * math.sin(start_angle))
            )
            end_pos = (
                center[0] + int(radius * math.cos(end_angle)),
                center[1] - int(radius * math.sin(end_angle))
            )
            
            color_with_alpha = (*self.color[:3], alpha)
            pygame.draw.line(surface, color_with_alpha, start_pos, end_pos, self.line_width)


class Tooltip:
    """Всплывающая подсказка"""
    
    def __init__(
        self,
        text: str,
        font: Optional[pygame.font.Font] = None,
        delay: float = 0.5,
        colors: Optional[Dict[str, Tuple[int, int, int]]] = None
    ):
        self.text = text
        self.font = font or pygame.font.Font(None, 24)
        self.delay = delay
        self.visible = False
        self.hover_time = 0.0
        self.position = (0, 0)
        
        self.colors = colors or {
            'background': (40, 40, 40),
            'text': (255, 255, 255),
            'border': (100, 100, 100)
        }
        
        self.padding = 8
        self.border_radius = 4

    def update(self, dt: float, mouse_pos: Tuple[int, int], is_hovered: bool):
        """Обновляет подсказку"""
        if is_hovered:
            self.hover_time += dt
            if self.hover_time >= self.delay:
                self.visible = True
                self.position = (mouse_pos[0] + 15, mouse_pos[1] + 15)
        else:
            self.hover_time = 0
            self.visible = False

    def draw(self, surface: pygame.Surface):
        """Рисует подсказку"""
        if not self.visible:
            return
        
        text_surface = self.font.render(self.text, True, self.colors['text'])
        text_rect = text_surface.get_rect()
        
        # Фон
        bg_rect = pygame.Rect(
            self.position[0] - self.padding,
            self.position[1] - self.padding,
            text_rect.width + self.padding * 2,
            text_rect.height + self.padding * 2
        )
        
        pygame.draw.rect(surface, self.colors['background'], bg_rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.colors['border'], bg_rect, 1, border_radius=self.border_radius)
        
        # Текст
        surface.blit(text_surface, (self.position[0], self.position[1]))


class Dropdown:
    """Выпадающий список"""
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        options: List[str],
        font: pygame.font.Font,
        initial_index: int = 0,
        on_change: Optional[Callable[[int], None]] = None
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.font = font
        self.on_change = on_change
        self.selected_index = initial_index
        
        self.is_expanded = False
        self.hovered = False
        
        self.colors = {
            'normal': UIColor.PRIMARY,
            'hover': UIColor.PRIMARY_LIGHT,
            'expanded': UIColor.PRIMARY_DARK,
            'text': UIColor.WHITE,
            'border': UIColor.WHITE
        }
        
        self.option_height = height
        self.max_visible_options = 6

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Обрабатывает события"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.is_expanded = not self.is_expanded
                    return True
                elif self.is_expanded:
                    # Проверка клика по опциям
                    for i in range(len(self.options)):
                        option_rect = pygame.Rect(
                            self.rect.x,
                            self.rect.y + (i + 1) * self.option_height,
                            self.rect.width,
                            self.option_height
                        )
                        if option_rect.collidepoint(event.pos):
                            self.selected_index = i
                            self.is_expanded = False
                            if self.on_change:
                                self.on_change(i)
                            return True
                    # Клик вне dropdown
                    self.is_expanded = False
        
        return False

    def draw(self, surface: pygame.Surface):
        """Рисует dropdown"""
        # Основная кнопка
        color = self.colors['expanded'] if self.is_expanded else (
            self.colors['hover'] if self.hovered else self.colors['normal']
        )
        
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, self.colors['border'], self.rect, 2, border_radius=4)
        
        # Текст
        text_surface = self.font.render(self.options[self.selected_index], True, self.colors['text'])
        text_rect = text_surface.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surface, text_rect)
        
        # Стрелка
        arrow_y = self.rect.centery
        if self.is_expanded:
            pygame.draw.polygon(surface, self.colors['text'], [
                (self.rect.right - 25, arrow_y - 5),
                (self.rect.right - 15, arrow_y - 5),
                (self.rect.right - 20, arrow_y)
            ])
        else:
            pygame.draw.polygon(surface, self.colors['text'], [
                (self.rect.right - 25, arrow_y),
                (self.rect.right - 15, arrow_y),
                (self.rect.right - 20, arrow_y + 5)
            ])
        
        # Выпадающие опции
        if self.is_expanded:
            visible_options = min(len(self.options), self.max_visible_options)
            for i in range(visible_options):
                option_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + (i + 1) * self.option_height,
                    self.rect.width,
                    self.option_height
                )
                
                option_color = self.colors['hover'] if option_rect.collidepoint(pygame.mouse.get_pos()) else self.colors['normal']
                pygame.draw.rect(surface, option_color, option_rect, border_radius=4)
                pygame.draw.rect(surface, self.colors['border'], option_rect, 1, border_radius=4)
                
                option_text = self.font.render(self.options[i], True, self.colors['text'])
                option_text_rect = option_text.get_rect(midleft=(option_rect.x + 10, option_rect.centery))
                surface.blit(option_text, option_text_rect)
