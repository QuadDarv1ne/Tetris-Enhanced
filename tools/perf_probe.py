#!/usr/bin/env python3
"""Замеряет стоимость отрисовки фона и проверяет рост глобальных словарей."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
pygame.init()

import tetris_enhanced as g

print("=" * 60)
print("1. Стоимость отрисовки фона (вызывается каждый кадр)")
print("=" * 60)
print(f"Разрешение: {g.WIDTH}x{g.HEIGHT}, целевой FPS: {g.FPS}")

screen = pygame.display.set_mode((g.WIDTH, g.HEIGHT))

frames = 60
t0 = time.perf_counter()
for _ in range(frames):
    g.draw_enhanced_background(screen)
elapsed = time.perf_counter() - t0

per_frame = elapsed / frames
budget = 1.0 / g.FPS
print(f"Кадр: {per_frame*1000:.2f} мс на {frames} кадров")
print(f"Бюджет кадра при {g.FPS} FPS: {budget*1000:.2f} мс")
print(f"Фон съедает: {100*per_frame/budget:.1f}% бюджета кадра")
print(f"Это {int(g.HEIGHT)} вызовов draw.line за кадр, "
      f"{int(g.HEIGHT*g.FPS)} вызовов/сек")

# Проверим, даёт ли кэш выигрыш
cached = pygame.Surface((g.WIDTH, g.HEIGHT))
g.draw_enhanced_background(cached)
t0 = time.perf_counter()
for _ in range(frames):
    screen.blit(cached, (0, 0))
blit_time = (time.perf_counter() - t0) / frames
print(f"\nС предрендером (один blit): {blit_time*1000:.3f} мс/кадр")
if blit_time > 0:
    print(f"Ускорение отрисовки фона: в {per_frame/blit_time:.1f}x")

print()
print("=" * 60)
print("2. Рост глобальных словарей состояний кнопок")
print("=" * 60)
print(f"mouse_transition_states сейчас: {len(g.mouse_transition_states)}")
print(f"click_states сейчас:            {len(g.click_states)}")
print("Ключ = f'{x}_{y}_{w}_{h}' новой кнопки. При смене разрешения")
print("или перестройке UI старые ключи не удаляются -> медленная утечка.")

pygame.quit()
