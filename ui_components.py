#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI components module for Tetris Enhanced
"""

import pygame
import logging
from typing import Tuple, Optional, Callable

logger = logging.getLogger("TetrisEnhanced.UI")

classUIColor:
    """Color constants for the UI"""
    # Основные цвета
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    LIGHT_GRAY = (192, 192, 192)
    
    # Цвета для кнопок
    BUTTON_NORMAL = (70, 130, 180)  # Steel Blue
    BUTTON_HOVER = (100, 149, 237)  # Cornflower Blue
    BUTTON_PRESSED = (65, 105, 225)  # Royal Blue
    BUTTON_TEXT = (255, 255, 255)
    BUTTON_TEXT_DISABLED = (169, 169, 169)
    
    # Цвета для игрового поля
    GRID_BG = (20, 20, 20)
    GRID_BORDER = (100, 100, 100)
    
    # Цвета для тетромино
    I_COLOR = (0, 255, 255)    # Cyan
    O_COLOR = (255, 255, 0)    # Yellow
    T_COLOR = (128, 0, 128)    # Purple
    S_COLOR = (0, 255, 0)      # Green
    Z_COLOR = (255, 0, 0)      # Red
    J_COLOR = (0, 0, 255)      # Blue
    L_COLOR = (255, 165, 0)    # Orange

class Button:
    """A customizable button UI component"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 font: pygame.font.Font, callback: Optional[Callable] = None,
                 enabled: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.enabled = enabled
        self.hovered = False
        self.pressed = False
        self.animation_progress = 0.0
        self.animation_speed = 0.1
        
        # Calculate text positioning
        self._update_text_surface()
    
    def _update_text_surface(self):
        """Update the text surface and its position."""
        if self.enabled:
            self.text_color = UIColor.BUTTON_TEXT
        else:
            self.text_color = UIColor.BUTTON_TEXT_DISABLED
            
        self.text_surface = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events for this button."""
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:  # Left mouse button
                self.pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                if self.pressed and self.hovered and self.callback:
                    self.callback()
                self.pressed = False
                return self.hovered
                
        return False
    
    def update(self, dt: float):
        """Update button animations."""
        if self.hovered and not self.pressed:
            self.animation_progress = min(1.0, self.animation_progress + self.animation_speed * dt * 60)
        else:
            self.animation_progress = max(0.0, self.animation_progress - self.animation_speed * dt * 60)
    
    def draw(self, surface: pygame.Surface):
        """Draw the button on the given surface."""
        # Determine button color based on state
        if not self.enabled:
            color = UIColor.DARK_GRAY
        elif self.pressed:
            color = UIColor.BUTTON_PRESSED
        elif self.hovered:
            # Interpolate between normal and hover colors
            normal_color = UIColor.BUTTON_NORMAL
            hover_color = UIColor.BUTTON_HOVER
            progress = self.animation_progress
            color = (
                int(normal_color[0] + (hover_color[0] - normal_color[0]) * progress),
                int(normal_color[1] + (hover_color[1] - normal_color[1]) * progress),
                int(normal_color[2] + (hover_color[2] - normal_color[2]) * progress)
            )
        else:
            color = UIColor.BUTTON_NORMAL
        
        # Draw button background
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        
        # Draw button border
        pygame.draw.rect(surface, UIColor.WHITE, self.rect, 2, border_radius=8)
        
        # Draw text
        surface.blit(self.text_surface, self.text_rect)

class TextBlock:
    """A text block UI component that supports word wrapping"""
    
    def __init__(self, x: int, y: int, width: int, text: str, 
                 font: pygame.font.Font, color: Tuple[int, int, int] = UIColor.WHITE,
                 line_spacing: int = 5):
        self.x = x
        self.y = y
        self.width = width
        self.text = text
        self.font = font
        self.color = color
        self.line_spacing = line_spacing
        self.lines = []
        
        self._wrap_text()
    
    def _wrap_text(self):
        """Wrap text to fit within the specified width."""
        self.lines = []
        words = self.text.split(' ')
        current_line = ""
        
        for word in words:
            # Test if adding this word would exceed the width
            test_line = current_line + ' ' + word if current_line else word
            text_width, _ = self.font.size(test_line)
            
            if text_width <= self.width:
                current_line = test_line
            else:
                # If we have a current line, add it and start a new one
                if current_line:
                    self.lines.append(current_line)
                    current_line = word
                else:
                    # Word is longer than the width, we need to break it
                    # This is a simplified approach - in a real implementation,
                    # you might want to break the word at character boundaries
                    self.lines.append(word)
                    current_line = ""
        
        # Add the last line if there is one
        if current_line:
            self.lines.append(current_line)
    
    def draw(self, surface: pygame.Surface):
        """Draw the text block on the given surface."""
        for i, line in enumerate(self.lines):
            text_surface = self.font.render(line, True, self.color)
            surface.blit(text_surface, (self.x, self.y + i * (self.font.get_height() + self.line_spacing)))

class ProgressBar:
    """A progress bar UI component"""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 min_value: float = 0.0, max_value: float = 1.0,
                 initial_value: float = 0.0, color: Tuple[int, int, int] = (0, 255, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.color = color
        self.bg_color = UIColor.DARK_GRAY
        self.border_color = UIColor.WHITE
    
    def set_value(self, value: float):
        """Set the progress bar value."""
        self.value = max(self.min_value, min(self.max_value, value))
    
    def get_percentage(self) -> float:
        """Get the progress as a percentage (0.0 to 1.0)."""
        if self.max_value == self.min_value:
            return 0.0
        return (self.value - self.min_value) / (self.max_value - self.min_value)
    
    def draw(self, surface: pygame.Surface):
        """Draw the progress bar on the given surface."""
        # Draw background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        
        # Draw progress
        progress_width = int(self.rect.width * self.get_percentage())
        if progress_width > 0:
            progress_rect = pygame.Rect(self.rect.x, self.rect.y, progress_width, self.rect.height)
            pygame.draw.rect(surface, self.color, progress_rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, 2)

def draw_block(surface: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int],
               with_border: bool = True, border_color: Tuple[int, int, int] = UIColor.WHITE):
    """Draw a single game block with optional border."""
    # Draw the main block
    pygame.draw.rect(surface, color, (x, y, size, size))
    
    # Draw highlight
    highlight_color = tuple(min(255, c + 60) for c in color)
    pygame.draw.line(surface, highlight_color, (x, y), (x + size - 1, y))
    pygame.draw.line(surface, highlight_color, (x, y), (x, y + size - 1))
    
    # Draw shadow
    shadow_color = tuple(max(0, c - 60) for c in color)
    pygame.draw.line(surface, shadow_color, (x, y + size - 1), (x + size - 1, y + size - 1))
    pygame.draw.line(surface, shadow_color, (x + size - 1, y), (x + size - 1, y + size - 1))
    
    # Draw border if requested
    if with_border:
        pygame.draw.rect(surface, border_color, (x, y, size, size), 1)

def draw_text_with_shadow(surface: pygame.Surface, text: str, font: pygame.font.Font,
                         x: int, y: int, text_color: Tuple[int, int, int] = UIColor.WHITE,
                         shadow_color: Tuple[int, int, int] = UIColor.BLACK,
                         shadow_offset: Tuple[int, int] = (2, 2)):
    """Draw text with a shadow effect."""
    # Draw shadow
    shadow_surface = font.render(text, True, shadow_color)
    surface.blit(shadow_surface, (x + shadow_offset[0], y + shadow_offset[1]))
    
    # Draw main text
    text_surface = font.render(text, True, text_color)
    surface.blit(text_surface, (x, y))