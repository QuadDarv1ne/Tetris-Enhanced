"""
TETRIS ENHANCED — итоговый файл проекта (на русском)
Описание:
    Улучшенная одностраничная реализация игры Tetris на Python с использованием pygame.
    Включает:
      - проигрывание фоновой музыки из папки music/ (mp3/ogg/wav);
      - звуковые эффекты из папки sounds/ (rotate.wav, drop.wav, line.wav);
      - стартовое меню выбора уровня и трека;
      - меню паузы с кнопками Продолжить / Сохранить / Загрузить / Следующая / Предыдущая / Выйти;
      - сохранение и загрузка состояния в JSON-файл (tetris_save.json);
      - механика Hold, ghost-piece, комбо и back-to-back, базовая обработка T-Spin;
      - настраиваемые контролы: стрелки, Z/X/A/S, Space, C/Shift, P, R, Esc/Q.

Установка и запуск:
    1) Убедитесь, что установлен Python 3.7+.
    2) Установите pygame:
         pip install pygame
    3) Создайте папки рядом со скриптом:
         music/   - поместите mp3/ogg/wav треки
         sounds/  - поместите wav-файлы эффектов: rotate.wav, drop.wav, line.wav
    4) Запустите:
         python tetris_enhanced.py

Формат сохранения:
    Состояние игры сохраняется в JSON и содержит простые типы (grid, next_queue, bag, current, hold, score, level и т.д.).
    Это позволяет при необходимости вручную редактировать или переносить файл.

Авторство и лицензия:
    Дуплей Максим Игоревич (17.07.1999)
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Tetris (single-file) — pygame

Улучшения по запросу пользователя:
 - Фоновая музыка (сканируется папка music/ для mp3/ogg/wav)
 - Простые звуковые эффекты (если есть файлы в ./sounds/)
 - Сохранение/загрузка игры в JSON (tetris_save.json)
 - Стартовое меню выбора уровня и музыкального трека
 - Меню паузы с кнопками: Продолжить, Сохранить, Загрузить, Следующая музыка, Предыдущая, Выйти

Положите свои mp3 (перечисленные вами) в папку ./music/
и wav-эффекты в ./sounds/ (rotate.wav, drop.wav, line.wav)

Запуск:
    pip install pygame
    python tetris_enhanced.py
"""
import os
import sys
import json
import random
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

try:
    import pygame
except Exception:
    print("This script requires pygame. Install with: pip install pygame")
    raise

# -------------------- Config --------------------
WIDTH, HEIGHT = 1024, 768
PLAY_COLS, PLAY_ROWS = 10, 20
BLOCK = 32
PLAY_W, PLAY_H = PLAY_COLS * BLOCK, PLAY_ROWS * BLOCK
MARGIN = 20
PANEL_W = WIDTH - PLAY_W - MARGIN * 3
FPS = 60

# Origin of playfield (centered vertically)
ORIGIN_X = MARGIN
ORIGIN_Y = max(MARGIN, MARGIN + (HEIGHT - 2*MARGIN - PLAY_H) // 2)

# Music directory scanning
MUSIC_DIR = "music"
MUSIC_FILES = []
if os.path.isdir(MUSIC_DIR):
    for fname in sorted(os.listdir(MUSIC_DIR)):
        if fname.lower().endswith(('.mp3', '.ogg', '.wav')):
            MUSIC_FILES.append(os.path.join(MUSIC_DIR, fname))
else:
    # fallback to explicit list (kept for compatibility)
    MUSIC_FILES = [
        "Tetris - Коробейники(FamilyJules7X).mp3",
        "Маридат47 - Музыка из тетриса (коробейники).mp3",
        "Коробейники - Тетрис Техно Ремикс.mp3",
        "Тетрис - Коробейники.mp3",
        "Владимир Зеленцов - Коробейники (Tetris Theme).mp3",
    ]

# Sound effects (optional). Put wav files into ./sounds/ named: rotate.wav, drop.wav, line.wav
SOUNDS_DIR = "sounds"

# Colors
BLACK = (18, 18, 20)
BG = (24, 24, 28)
GRID = (40, 40, 48)
WHITE = (240, 240, 250)
DIM = (180, 180, 200)
GHOST = (120, 120, 140)
BUTTON_BG = (40, 40, 45)
BUTTON_BORDER = (10, 10, 12)

# Tetromino colors (I, O, T, S, Z, J, L)
COLORS = {
    'I': (0, 186, 255),
    'O': (255, 214, 0),
    'T': (175, 96, 234),
    'S': (0, 200, 120),
    'Z': (230, 30, 80),
    'J': (0, 120, 255),
    'L': (255, 140, 0),
}

# Shapes are 4x4 matrices
SHAPES = {
    'I': [
        ["....",
         "IIII",
         "....",
         "...."],
    ],
    'O': [
        ["....",
         ".OO.",
         ".OO.",
         "...."],
    ],
    'T': [
        ["....",
         ".TTT",
         "..T.",
         "...."],
    ],
    'S': [
        ["....",
         "..SS",
         ".SS.",
         "...."],
    ],
    'Z': [
        ["....",
         ".ZZ.",
         "..ZZ",
         "...."],
    ],
    'J': [
        ["....",
         ".JJJ",
         ".J..",
         "...."],
    ],
    'L': [
        ["....",
         ".LLL",
         ".L..",
         "...."],
    ],
}

ROTATIONS = {'I': 2, 'O': 1, 'T': 4, 'S': 2, 'Z': 2, 'J': 4, 'L': 4}

# Kicks (simplified SRS-ish)
KICKS = {
    'JLTSZ': {
        (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, +2), (-1, +2)],
        (1, 0): [(0, 0), (+1, 0), (+1, +1), (0, -2), (+1, -2)],
        (1, 2): [(0, 0), (+1, 0), (+1, -1), (0, +2), (+1, +2)],
        (2, 1): [(0, 0), (-1, 0), (-1, +1), (0, -2), (-1, -2)],
        (2, 3): [(0, 0), (+1, 0), (+1, +1), (0, -2), (+1, -2)],
        (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, +2), (-1, +2)],
        (3, 0): [(0, 0), (-1, 0), (-1, +1), (0, -2), (-1, -2)],
        (0, 3): [(0, 0), (+1, 0), (+1, -1), (0, +2), (+1, +2)],
    },
    'I': {
        (0, 1): [(0, 0), (-2, 0), (+1, 0), (-2, -1), (+1, +2)],
        (1, 0): [(0, 0), (+2, 0), (-1, 0), (+2, +1), (-1, -2)],
        (1, 2): [(0, 0), (-1, 0), (+2, 0), (-1, +2), (+2, -1)],
        (2, 1): [(0, 0), (+1, 0), (-2, 0), (+1, -2), (-2, +1)],
        (2, 3): [(0, 0), (+2, 0), (-1, 0), (+2, +1), (-1, -2)],
        (3, 2): [(0, 0), (-2, 0), (+1, 0), (-2, -1), (+1, +2)],
        (3, 0): [(0, 0), (+1, 0), (-2, 0), (+1, -2), (-2, +1)],
        (0, 3): [(0, 0), (-1, 0), (+2, 0), (-1, +2), (+2, -1)],
    }
}

# -------------------- Utility --------------------
def rotate_shape(grid: List[str]) -> List[str]:
    return [''.join([grid[3 - c][r] for c in range(4)]) for r in range(4)]

def build_rotations(kind: str) -> List[List[str]]:
    base = SHAPES[kind][0]
    rots = [base]
    for _ in range(3):
        rots.append(rotate_shape(rots[-1]))
    unique = []
    seen = set()
    for r in rots:
        key = tuple(r)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    count = ROTATIONS[kind]
    return unique[:count]

ROTATED = {k: build_rotations(k) for k in SHAPES.keys()}

@dataclass
class Piece:
    kind: str
    x: int
    y: int
    r: int = 0

    @property
    def grid(self) -> List[str]:
        return ROTATED[self.kind][self.r % len(ROTATED[self.kind])]

    def cells(self) -> List[Tuple[int, int]]:
        cells = []
        g = self.grid
        for j in range(4):
            for i in range(4):
                if g[j][i] != '.':
                    cells.append((self.x + i, self.y + j))
        return cells

@dataclass
class GameState:
    grid: List[List[Optional[str]]] = field(default_factory=lambda: [[None for _ in range(PLAY_COLS)] for _ in range(PLAY_ROWS)])
    bag: List[str] = field(default_factory=list)
    next_queue: List[str] = field(default_factory=list)
    hold: Optional[str] = None
    can_hold: bool = True
    current: Optional[Piece] = None
    score: int = 0
    lines: int = 0
    level: int = 1
    combo: int = -1
    back_to_back: bool = False
    game_over: bool = False
    paused: bool = False
    fall_interval: float = 1.0
    # hard-drop animation state
    hard_drop_anim: bool = False
    hard_drop_start_y: int = 0
    hard_drop_target_y: int = 0
    hard_drop_duration: float = 0.0
    hard_drop_start_time: float = 0.0

    def to_dict(self):
        return {
            'grid': [[cell if cell is not None else None for cell in row] for row in self.grid],
            'bag': list(self.bag),
            'next_queue': list(self.next_queue),
            'hold': self.hold,
            'can_hold': self.can_hold,
            'current': None if self.current is None else {'kind': self.current.kind, 'x': self.current.x, 'y': self.current.y, 'r': self.current.r},
            'score': self.score,
            'lines': self.lines,
            'level': self.level,
            'combo': self.combo,
            'back_to_back': self.back_to_back,
            'game_over': self.game_over,
        }

    @staticmethod
    def from_dict(d):
        s = GameState()
        s.grid = [[cell if cell is not None else None for cell in row] for row in d.get('grid', s.grid)]
        s.bag = d.get('bag', [])
        s.next_queue = d.get('next_queue', [])
        s.hold = d.get('hold', None)
        s.can_hold = d.get('can_hold', True)
        cur = d.get('current', None)
        if cur:
            s.current = Piece(cur['kind'], cur['x'], cur['y'], cur['r'])
        s.score = d.get('score', 0)
        s.lines = d.get('lines', 0)
        s.level = d.get('level', 1)
        s.combo = d.get('combo', -1)
        s.back_to_back = d.get('back_to_back', False)
        s.game_over = d.get('game_over', False)
        s.fall_interval = gravity_for_level(s.level)
        return s

# -------------------- Core game logic --------------------
def gravity_for_level(level: int) -> float:
    return max(0.05, 0.8 * (0.9 ** (level - 1)))

def spawn_x(kind: str) -> int:
    return 3 if kind != 'I' else 3

def collides(state: GameState, piece: Piece) -> bool:
    for x, y in piece.cells():
        if x < 0 or x >= PLAY_COLS or y >= PLAY_ROWS:
            return True
        if y >= 0 and state.grid[y][x] is not None:
            return True
    return False

def lock_piece(state: GameState):
    if state.current is None:
        return 0
    for x, y in state.current.cells():
        if y < 0:
            state.game_over = True
            return 0
        state.grid[y][x] = state.current.kind
    cleared = clear_lines(state)
    state.can_hold = True
    state.current = None
    spawn_next(state)
    return cleared

def is_t_spin(state: GameState, piece: Piece, kicked: bool) -> str:
    if piece.kind != 'T':
        return 'none'
    corners = [(piece.x, piece.y), (piece.x+2, piece.y), (piece.x, piece.y+2), (piece.x+2, piece.y+2)]
    occupied = 0
    for cx, cy in corners:
        if cy < 0 or cx < 0 or cx >= PLAY_COLS or cy >= PLAY_ROWS:
            occupied += 1
        elif state.grid[cy][cx] is not None:
            occupied += 1
    if occupied >= 3:
        return 'tspin'
    return 'none'

def score_lines(state: GameState, lines: int, tspin: str):
    pts = 0
    if tspin != 'none':
        if lines == 1:
            pts = 400
        elif lines == 2:
            pts = 700
        else:
            pts = 100
        b2b_candidate = True
    else:
        if lines == 1:
            pts = 100
        elif lines == 2:
            pts = 300
        elif lines == 3:
            pts = 500
        elif lines >= 4:
            pts = 800
        b2b_candidate = (lines >= 4)

    if lines > 0:
        state.combo += 1
        if state.combo > 0:
            pts += 50 * state.combo
        if b2b_candidate:
            if state.back_to_back:
                pts = int(pts * 1.5)
            state.back_to_back = True
        else:
            state.back_to_back = False
        state.lines += lines
        if state.lines // 10 + 1 > state.level:
            state.level = state.lines // 10 + 1
            state.fall_interval = gravity_for_level(state.level)
    else:
        state.combo = -1
        state.back_to_back = False

    state.score += pts

def clear_lines(state: GameState) -> int:
    new_grid = [row for row in state.grid if any(cell is None for cell in row)]
    cleared = PLAY_ROWS - len(new_grid)
    while len(new_grid) < PLAY_ROWS:
        new_grid.insert(0, [None for _ in range(PLAY_COLS)])
    state.grid = new_grid
    return cleared

def refill_bag(state: GameState):
    bag = list(SHAPES.keys())
    random.shuffle(bag)
    state.bag.extend(bag)

def spawn_next(state: GameState):
    while len(state.next_queue) < 5:
        if not state.bag:
            refill_bag(state)
        state.next_queue.append(state.bag.pop(0))
    kind = state.next_queue.pop(0)
    piece = Piece(kind, spawn_x(kind), -2, 0)
    if collides(state, piece):
        state.game_over = True
    state.current = piece

def try_move(state: GameState, dx: int, dy: int) -> bool:
    if state.current is None:
        return False
    p = Piece(state.current.kind, state.current.x + dx, state.current.y + dy, state.current.r)
    if not collides(state, p):
        state.current = p
        return True
    return False

def try_rotate(state: GameState, dr: int) -> Tuple[bool, str]:
    cur = state.current
    if cur is None:
        return False, 'none'
    from_r = cur.r % len(ROTATED[cur.kind])
    to_r = (cur.r + dr) % len(ROTATED[cur.kind])
    which = 'I' if cur.kind == 'I' else 'JLTSZ'
    kicks = KICKS.get(which, {}).get((from_r, to_r), [(0, 0)])
    for (dx, dy) in kicks:
        cand = Piece(cur.kind, cur.x + dx, cur.y + dy, to_r)
        if not collides(state, cand):
            state.current = cand
            return True, is_t_spin(state, cand, kicked=(dx != 0 or dy != 0))
    return False, 'none'

def hard_drop_distance(state: GameState) -> int:
    if state.current is None:
        return 0
    dist = 0
    p = state.current
    while True:
        q = Piece(p.kind, p.x, p.y + dist + 1, p.r)
        if collides(state, q):
            break
        dist += 1
    return dist

def ghost_position(state: GameState) -> Piece:
    d = hard_drop_distance(state)
    p = state.current
    return Piece(p.kind, p.x, p.y + d, p.r)

def hold_swap(state: GameState):
    if state.current is None or not state.can_hold:
        return
    cur_kind = state.current.kind
    if state.hold is None:
        state.hold = cur_kind
        spawn_next(state)
    else:
        state.current = Piece(state.hold, spawn_x(state.hold), -2, 0)
        state.hold = cur_kind
        if collides(state, state.current):
            state.game_over = True
    state.can_hold = False

# -------------------- Audio --------------------

MUSIC_END_EVENT = pygame.USEREVENT + 1

class AudioManager:
    def __init__(self):
        # initialize mixer safely
        try:
            pygame.mixer.init()
        except Exception:
            pass
        # build playlist from MUSIC_FILES (already scanned)
        self.playlist = [f for f in MUSIC_FILES if os.path.isfile(f)]
        # if paths are relative inside 'music', resolve them
        if not self.playlist and os.path.isdir(MUSIC_DIR):
            for fname in sorted(os.listdir(MUSIC_DIR)):
                path = os.path.join(MUSIC_DIR, fname)
                if path.lower().endswith(('.mp3', '.ogg', '.wav')) and os.path.isfile(path):
                    self.playlist.append(path)
        self.index = 0
        self.enabled = len(self.playlist) > 0
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        self.sounds = {}
        # load sfx if available
        if os.path.isdir(SOUNDS_DIR):
            for name in ['rotate', 'drop', 'line']:
                path = os.path.join(SOUNDS_DIR, f"{name}.wav")
                if os.path.isfile(path):
                    try:
                        self.sounds[name] = pygame.mixer.Sound(path)
                    except Exception:
                        self.sounds[name] = None
        # default volume
        try:
            pygame.mixer.music.set_volume(0.5)
        except Exception:
            pass

    def play_current(self):
        if not self.enabled:
            return
        path = self.playlist[self.index]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception as e:
            print('Failed to play', path, e)

    def next(self):
        if not self.enabled:
            return
        self.index = (self.index + 1) % len(self.playlist)
        self.play_current()

    def prev(self):
        if not self.enabled:
            return
        self.index = (self.index - 1) % len(self.playlist)
        self.play_current()

    def stop(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def play_sfx(self, name: str):
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

# -------------------- Drawing --------------------
def draw_block(surf, x, y, color, border=True, alpha=None):
    rect = pygame.Rect(x, y, BLOCK-1, BLOCK-1)
    if alpha is not None:
        block = pygame.Surface((BLOCK-1, BLOCK-1), pygame.SRCALPHA)
        c = (*color, alpha)
        pygame.draw.rect(block, c, block.get_rect(), border_radius=6)
        surf.blit(block, rect.topleft)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=6)
    if border:
        pygame.draw.rect(surf, (0,0,0), rect, 2, border_radius=6)

def draw_grid(surf, origin_x, origin_y, state: GameState):
    pygame.draw.rect(surf, (32, 32, 38), (origin_x, origin_y, PLAY_W, PLAY_H), border_radius=12)
    for i in range(PLAY_COLS + 1):
        x = origin_x + i * BLOCK
        pygame.draw.line(surf, GRID, (x, origin_y), (x, origin_y + PLAY_H))
    for j in range(PLAY_ROWS + 1):
        y = origin_y + j * BLOCK
        pygame.draw.line(surf, GRID, (origin_x, y), (origin_x + PLAY_W, y))
    for y in range(PLAY_ROWS):
        for x in range(PLAY_COLS):
            kind = state.grid[y][x]
            if kind:
                color = COLORS[kind]
                draw_block(surf, origin_x + x*BLOCK, origin_y + y*BLOCK, color)

def draw_piece(surf, origin_x, origin_y, piece: Piece, ghost=False):
    if piece is None:
        return
    color = GHOST if ghost else COLORS[piece.kind]
    for x, y in piece.cells():
        if y >= 0:
            draw_block(surf, origin_x + x*BLOCK, origin_y + y*BLOCK, color, border=not ghost, alpha=120 if ghost else None)

def draw_panel(surf, origin_x, origin_y, state: GameState, font, small, audio: AudioManager):
    title = font.render("TETRIS", True, WHITE)
    surf.blit(title, (origin_x, origin_y))
    def label(y, text):
        t = small.render(text, True, DIM)
        surf.blit(t, (origin_x, y))
    y = origin_y + 50
    label(y, f"Score: {state.score}")
    label(y + 26, f"Lines: {state.lines}")
    label(y + 52, f"Level: {state.level}")
    if state.combo >= 1:
        label(y + 78, f"Combo: x{state.combo}")
    nxt = small.render("Next:", True, DIM)
    surf.blit(nxt, (origin_x, y + 120))
    ny = y + 150
    for i, kind in enumerate(state.next_queue[:5]):
        draw_mini(surf, origin_x, ny + i * 70, kind, small)
    hold_lbl = small.render("Hold:", True, DIM)
    surf.blit(hold_lbl, (origin_x, y + 120 + 5 * 70))
    draw_mini(surf, origin_x, y + 120 + 5 * 70 + 30, state.hold, small)
    help_y = HEIGHT - 160
    for i, line in enumerate([
        "← → : Move",
        "↓ : Soft drop",
        "Space : Hard drop",
        "Z / ↑ : Rotate",
        "X : Counter-rotate",
        "C/Shift : Hold",
        "P : Pause, R : Restart",
    ]):
        t = small.render(line, True, (150, 150, 165))
        surf.blit(t, (origin_x, help_y + i * 18))
    # music info
    if audio.enabled:
        txt = small.render(f"Music: {os.path.basename(audio.playlist[audio.index])}", True, DIM)
        surf.blit(txt, (origin_x, help_y - 26))

def draw_mini(surf, origin_x, origin_y, kind: Optional[str], small):
    box = pygame.Rect(origin_x, origin_y, PANEL_W-10, 80)
    pygame.draw.rect(surf, (32, 32, 36), box, border_radius=10)
    pygame.draw.rect(surf, (0,0,0), box, 2, border_radius=10)
    if not kind:
        return
    grid = ROTATED[kind][0]
    cells = [(i, j) for j in range(4) for i in range(4) if grid[j][i] != '.']
    if not cells:
        return
    minx = min(i for i, _ in cells)
    maxx = max(i for i, _ in cells)
    miny = min(j for _, j in cells)
    maxy = max(j for _, j in cells)
    w = maxx - minx + 1
    h = maxy - miny + 1
    scale = 20
    offset_x = origin_x + 10 + (PANEL_W - 20 - w*scale) // 2
    offset_y = origin_y + 8 + (60 - 16 - h*scale) // 2
    for i, j in cells:
        x = (i - minx) * scale
        y = (j - miny) * scale
        rect = pygame.Rect(offset_x + x, offset_y + y, scale-1, scale-1)
        pygame.draw.rect(surf, COLORS[kind], rect, border_radius=4)
        pygame.draw.rect(surf, (0,0,0), rect, 1, border_radius=4)

# -------------------- Save / Load --------------------

SAVE_FILE = 'tetris_save.json'

def save_game(state: GameState, filename: str = SAVE_FILE):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        print('Game saved to', filename)
    except Exception as e:
        print('Failed to save:', e)

def load_game(filename: str = SAVE_FILE) -> Optional[GameState]:
    if not os.path.isfile(filename):
        print('Save file not found')
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            d = json.load(f)
        state = GameState.from_dict(d)
        print('Game loaded from', filename)
        return state
    except Exception as e:
        print('Failed to load:', e)
        return None

# -------------------- Menus --------------------
def button_rect(x, y, w, h):
    return pygame.Rect(x, y, w, h)

def draw_button(surface, rect: pygame.Rect, text: str, font, hover=False):
    color = (70, 70, 74) if hover else BUTTON_BG
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, BUTTON_BORDER, rect, 2, border_radius=8)
    txt = font.render(text, True, WHITE)
    surface.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2, rect.y + (rect.h - txt.get_height()) // 2))

def start_menu(screen, clock, font, small, audio: AudioManager):
    selected_level = 1
    music_index = audio.index if audio.enabled else -1
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit(0)
                if ev.key == pygame.K_RETURN:
                    return selected_level, music_index
                if ev.key == pygame.K_RIGHT:
                    selected_level = min(10, selected_level + 1)
                if ev.key == pygame.K_LEFT:
                    selected_level = max(1, selected_level - 1)
                if ev.key == pygame.K_DOWN:
                    if audio.enabled:
                        music_index = (music_index + 1) % len(audio.playlist)
                if ev.key == pygame.K_UP:
                    if audio.enabled:
                        music_index = (music_index - 1) % len(audio.playlist)
        screen.fill(BG)
        title = font.render('TETRIS', True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))
        info = small.render('Выберите начальный уровень (← →) и музыку (↑ ↓). Enter=Старт', True, DIM)
        screen.blit(info, (WIDTH//2 - info.get_width()//2, 120))
        lvl_txt = font.render(f'Level {selected_level}', True, WHITE)
        screen.blit(lvl_txt, (WIDTH//2 - lvl_txt.get_width()//2, 200))
        if audio.enabled and music_index >= 0:
            music_txt = small.render(f'Music: {os.path.basename(audio.playlist[music_index])}', True, DIM)
        else:
            music_txt = small.render('Music: (none found)', True, DIM)
        screen.blit(music_txt, (WIDTH//2 - music_txt.get_width()//2, 260))
        start_hint = small.render('Press Enter to start', True, (200,200,200))
        screen.blit(start_hint, (WIDTH//2 - start_hint.get_width()//2, HEIGHT - 80))
        pygame.display.flip()
    return selected_level, music_index

def pause_menu(screen, clock, font, small, audio: AudioManager, state: GameState):
    # returns action: 'resume' or 'quit' or None
    w = 420; h = 360
    rx = ORIGIN_X + (PLAY_W - w)//2
    ry = ORIGIN_Y + (PLAY_H - h)//2
    bigfont = pygame.font.SysFont('consolas,monospace', 28, bold=True)
    buttons = [
        ('Продолжить', 'resume'),
        ('Сохранить', 'save'),
        ('Загрузить', 'load'),
        ('След. музыка', 'next'),
        ('Пред. музыка', 'prev'),
        ('Выйти', 'quit'),
    ]
    btn_rects = []
    for i, (t, a) in enumerate(buttons):
        bx = rx + 30
        by = ry + 40 + i * 50
        br = button_rect(bx, by, w-60, 40)
        btn_rects.append((br, a, t))
    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_p:
                    return 'resume'
                if ev.key == pygame.K_ESCAPE:
                    return 'quit'
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for rect, action, text in btn_rects:
                    if rect.collidepoint(mx, my):
                        if action == 'resume':
                            return 'resume'
                        if action == 'save':
                            save_game(state)
                        if action == 'load':
                            loaded = load_game()
                            if loaded:
                                return ('load', loaded)
                        if action == 'next':
                            audio.next();
                        if action == 'prev':
                            audio.prev();
                        if action == 'quit':
                            return 'quit'
        # draw overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((20, 20, 24, 220))
        screen.blit(overlay, (rx, ry))
        title = bigfont.render('ПАУЗА', True, WHITE)
        screen.blit(title, (rx + (w - title.get_width())//2, ry + 6))
        for rect, action, text in btn_rects:
            mx, my = pygame.mouse.get_pos()
            hover = rect.collidepoint(mx, my)
            draw_button(screen, rect, text, small, hover=hover)
        pygame.display.flip()

# -------------------- Game loop --------------------
def new_game(start_level=1) -> GameState:
    state = GameState()
    state.level = start_level
    state.fall_interval = gravity_for_level(state.level)
    refill_bag(state)
    spawn_next(state)
    return state

def run():
    pygame.init()
    pygame.display.set_caption('Tetris Enhanced')
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', 48, bold=True)
    small = pygame.font.SysFont('consolas,dejavusansmono,menlo,monospace', 20)

    audio = AudioManager()

    # start menu
    start_level = 1
    if True:
        start_level, music_choice = start_menu(screen, clock, font, small, audio)
        if audio.enabled and music_choice >= 0:
            audio.index = music_choice
            audio.play_current()
        elif audio.enabled:
            audio.play_current()

    state = new_game(start_level)

    fall_accum = 0.0
    left = right = down = False
    das = 0.12
    arr = 0.03
    last_lr = None
    lr_timer = 0.0

    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == MUSIC_END_EVENT:
                audio.next()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit(0)
                if ev.key == pygame.K_p:
                    # pause menu
                    action = pause_menu(screen, clock, font, small, audio, state)
                    if action == 'resume' or action == None:
                        pass
                    elif action == 'quit':
                        pygame.quit(); sys.exit(0)
                    elif isinstance(action, tuple) and action[0] == 'load':
                        # replace state with loaded
                        loaded = action[1]
                        state = loaded
                if ev.key == pygame.K_r:
                    state = new_game(start_level)
                if state.game_over or state.paused:
                    continue
                if ev.key == pygame.K_LEFT:
                    left = True; right = False; last_lr = 'L'; lr_timer = 0.0
                    if try_move(state, -1, 0):
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_RIGHT:
                    right = True; left = False; last_lr = 'R'; lr_timer = 0.0
                    if try_move(state, +1, 0):
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_DOWN:
                    down = True
                elif ev.key in (pygame.K_UP, pygame.K_z):
                    ok, tspin = try_rotate(state, +1)
                    if ok:
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_x:
                    ok, tspin = try_rotate(state, -1)
                    if ok:
                        audio.play_sfx('rotate')
                elif ev.key in (pygame.K_a, pygame.K_s):
                    ok, tspin = try_rotate(state, +2)
                    if ok:
                        audio.play_sfx('rotate')
                elif ev.key == pygame.K_SPACE:
                    if state.current is not None and not state.hard_drop_anim:
                        d = hard_drop_distance(state)
                        if d > 0:
                            # configure animation: duration depends on distance but capped
                            start_y = state.current.y
                            target_y = state.current.y + d
                            duration = min(0.5, 0.06 + 0.02 * d)  # tune: slower visual drop
                            state.hard_drop_anim = True
                            state.hard_drop_start_y = start_y
                            state.hard_drop_target_y = target_y
                            state.hard_drop_duration = duration
                            state.hard_drop_start_time = pygame.time.get_ticks() / 1000.0
                            # award score immediately (as before)
                            state.score += 2 * d
                            audio.play_sfx('drop')
                        else:
                            pass
                elif ev.key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                    hold_swap(state)
            elif ev.type == pygame.KEYUP:
                if ev.key == pygame.K_LEFT:
                    left = False
                elif ev.key == pygame.K_RIGHT:
                    right = False
                elif ev.key == pygame.K_DOWN:
                    down = False

        if state.game_over:
            screen.fill(BG)
            draw_grid(screen, ORIGIN_X, ORIGIN_Y, state)
            if state.current:
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, state.current)
            panel_x = ORIGIN_X + PLAY_W + MARGIN
            draw_panel(screen, panel_x, MARGIN, state, font, small, audio)
            go_txt = font.render('GAME OVER', True, (255, 80, 80))
            screen.blit(go_txt, (MARGIN + (PLAY_W - go_txt.get_width()) // 2, HEIGHT // 2 - 24))
            sub = small.render('Press R to Restart, Esc to Quit', True, DIM)
            screen.blit(sub, (MARGIN + (PLAY_W - sub.get_width()) // 2, HEIGHT // 2 + 10))
            pygame.display.flip()
            continue

        if state.paused:
            # shouldn't happen; we use explicit pause menu
            pygame.time.delay(100)
            continue


        # Hard-drop animation handling
        if state.hard_drop_anim and state.current is not None:
            now = pygame.time.get_ticks() / 1000.0
            elapsed = now - state.hard_drop_start_time
            t = min(1.0, elapsed / state.hard_drop_duration) if state.hard_drop_duration > 0 else 1.0
            # ease out for nicer feel
            ease = 1 - (1 - t) * (1 - t)
            draw_y = int(state.hard_drop_start_y + (state.hard_drop_target_y - state.hard_drop_start_y) * ease)
            # If animation finished, set position and lock
            if t >= 1.0:
                state.current.y = state.hard_drop_target_y
                # finalize lock
                lock_piece(state)
                state.hard_drop_anim = False
                fall_accum = 0.0
            else:
                # temporary draw position is stored for rendering
                state._anim_draw_y = draw_y
        # Auto shift left/right
        if last_lr == 'L' and left:
            lr_timer += dt
            if lr_timer >= das:
                while lr_timer >= das:
                    if not try_move(state, -1, 0):
                        break
                    lr_timer -= arr
        elif last_lr == 'R' and right:
            lr_timer += dt
            if lr_timer >= das:
                while lr_timer >= das:
                    if not try_move(state, +1, 0):
                        break
                    lr_timer -= arr
        else:
            lr_timer = 0.0

        if state.current is None:
            spawn_next(state)

        gravity = state.fall_interval
        if down:
            gravity = gravity / 20.0
        fall_accum += dt
        while fall_accum >= gravity:
            fall_accum -= gravity
            moved = try_move(state, 0, +1)
            if moved:
                if down:
                    state.score += 1
            else:
                # lock
                cleared = lock_piece(state)
                if cleared > 0:
                    audio.play_sfx('line')
                    score_lines(state, cleared, 'none')

        # Draw
        screen.fill(BG)
        draw_grid(screen, ORIGIN_X, ORIGIN_Y, state)
        if state.current:
            ghost = ghost_position(state)
            draw_piece(screen, ORIGIN_X, ORIGIN_Y, ghost, ghost=True)
            # if animating hard-drop, draw the current piece at intermediate y
            if getattr(state, 'hard_drop_anim', False) and hasattr(state, '_anim_draw_y'):
                temp_piece = Piece(state.current.kind, state.current.x, state._anim_draw_y, state.current.r)
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, temp_piece)
            else:
                draw_piece(screen, ORIGIN_X, ORIGIN_Y, state.current)

        panel_x = ORIGIN_X + PLAY_W + MARGIN
        draw_panel(screen, panel_x, MARGIN, state, font, small, audio)

        pygame.display.flip()

if __name__ == '__main__':
    run()
