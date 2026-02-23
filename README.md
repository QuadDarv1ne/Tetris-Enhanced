# Tetris Enhanced — Инструкция

[![DOI](https://zenodo.org/badge/1042618379.svg)](https://doi.org/10.5281/zenodo.17264455)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0007--7605--539X-green?logo=orcid&logoColor=white)](https://orcid.org/0009-0007-7605-539X)
[![Version](https://img.shields.io/badge/version-2.1.0-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENCE)

## Описание

Этот репозиторий содержит улучшенную версию игры Tetris на Python (один файл): `tetris_enhanced.py`.
Игра реализована с использованием библиотеки `pygame` и поддерживает фоновые мелодии, звуковые эффекты,
сохранение/загрузку состояния и интерактивные меню (стартовое меню выбора уровня и меню паузы).

### ✨ Что нового в версии 2.1.0?

- **🎯 Ежедневные испытания** — новые задания каждый день с наградами
- **📊 Статистика игрока** — детальная карьерная статистика и история игр
- **🏆 Таблица лидеров** — локальные рекорды по режимам игры
- **🎨 Визуальные эффекты** — система частиц для ярких эффектов
- **👻 Ghost Piece** — призрачная фигура для точного позиционирования
- **🎮 Интеграция систем** — единый интерфейс для всех систем игры

### ✨ Что нового в версии 2.0.0?

- **🏆 Система достижений** — 19 достижений с визуальными уведомлениями
- **🎨 Улучшенные UI компоненты** — анимированные кнопки, прогресс-бары, подсказки
- **⚡ Монитор производительности** — отслеживание FPS, CPU, памяти
- **🛠️ Улучшенное логирование** — автоматические отчёты об ошибках
- **🧪 Тестовый фреймворк** — комплексное тестирование всех систем

## Содержимое

### Основные файлы
- `tetris_enhanced.py` — основной исполняемый файл игры.
- `tetris_enhanced_fixed.py` — альтернативная стабильная версия.
- `game_config.py` — модуль конфигурации игры.
- `config_manager.py` — менеджер управления конфигурацией.
- `ui_components.py` — базовые UI компоненты.
- `config.json` — файл конфигурации.

### Новые модули (v2.1.0)
- `game/achievements.py` — система достижений.
- `game/daily_challenges.py` — ежедневные испытания.
- `game/player_stats.py` — статистика игрока.
- `game/leaderboard.py` — таблица лидеров.
- `game/integration.py` — интеграция всех систем.
- `game/particles.py` — система частиц.
- `game/state_manager.py` — менеджер состояний игры.
- `ui/advanced_components.py` — продвинутые UI компоненты.
- `utils/logger.py` — улучшенная система логирования.
- `utils/performance.py` — монитор производительности и кэширование.

### Тесты
- `tests/test_framework.py` — основной тестовый фреймворк.
- `tests/quick_adaptive_test.py` — быстрая проверка адаптивности.
- `tests/test_responsive_design.py` — тесты адаптивного дизайна.

### Директории
- `music/` — фоновая музыка (mp3/ogg/wav).
- `sounds/` — звуковые эффекты (wav): `rotate.wav`, `drop.wav`, `line.wav`.
- `saves/` — сохранения игр.
- `logs/` — логи игры (создаётся автоматически).
- `error_reports/` — отчёты об ошибках (создаётся автоматически).
- `img/` — изображения.
- `archive/` — архив версий.

## Требования

- Python 3.8+ (рекомендуется 3.10+)
- pygame >= 2.5.0
- numpy >= 1.24.0
- pillow >= 10.0.0
- psutil >= 5.9.0

## Установка

### Быстрая установка

```bash
# Клонируйте репозиторий или скачайте файлы
# Установите зависимости
pip install -r requirements.txt

# Запустите игру
python tetris_enhanced.py
```

### Пошаговая установка

1. **Установите Python** (если не установлен)
   - Скачайте с [python.org](https://www.python.org/downloads/)
   - Версия 3.8 или новее

2. **Установите зависимости**
   ```bash
   pip install pygame numpy pillow psutil
   ```

3. **Настройте игру**
   - Создайте папку `music/` и поместите туда mp3-файлы
   - Создайте папку `sounds/` и поместите туда wav-файлы:
     - `rotate.wav` — звук поворота
     - `drop.wav` — звук падения
     - `line.wav` — звук очистки линий

4. **Запустите игру**
   ```bash
   python tetris_enhanced.py
   ```

## Запуск тестов

```bash
# Запустить все тесты
python run_tests.py

# Запустить тесты по категории
python run_tests.py --category unit
python run_tests.py --category performance
python run_tests.py --category ui

# Тихий режим
python run_tests.py -q
```

## Управление

- ← / → — перемещение фигуры влево/вправо
- ↓ — мягкое падение
- Space — жёсткое падение
- Z или ↑ — поворот по часовой
- X — поворот против часовой
- A / S — поворот на 180°
- C или Shift — удержание (hold)
- P — открыть меню паузы
- R — перезапуск
- Esc / Q — выход

## Меню и функциональность

- Стартовое меню: выбор начального уровня (стрелки ← →) и музыки (↑ ↓), Enter — старт.
- Меню паузы (P): кнопки Продолжить, Сохранить, Загрузить, Следующая музыка, Предыдущая, Выйти.
- Сохранение/загрузка: используется JSON-файл `tetris_save.json`. Кнопка "Сохранить" экспортирует
  текущее состояние, "Загрузить" — попытается восстановить игру из файла.
- Музыка: поддерживается плейлист mp3; при окончании трека автоматически переключается следующий.
- Звуковые эффекты: если есть wav-файлы в `sounds/`, будут проигрываться при повороте, падении и очистке линий.

## Формат сохранения

- Состояние сериализуется в JSON и хранит:
  * сетку игрового поля (grid)
  * мешок и очередь следующих фигур (bag, next_queue)
  * текущую фигуру (kind, x, y, rotation)
  * hold, очки, уровень, линии, combo, back_to_back
- Файл: `tetris_save.json` (можно редактировать вручную, но соблюдать структуру)

## Советы по настройке и отладке

### Настройка производительности

Если игра работает медленно, отредактируйте `config.json`:

```json
{
  "enable_animations": false,
  "enable_shadows": false,
  "render_quality": "low",
  "fps_target": 30
}
```

### Логирование

Игра автоматически создаёт логи в папке `logs/` и отчёты об ошибках в `error_reports/`.

Для включения подробного логирования в коде:

```python
from utils import init_logger

logger = init_logger(
    log_level=logging.DEBUG,
    console_output=True,
    file_output=True
)
```

### Мониторинг производительности

```python
from utils import get_performance_monitor

monitor = get_performance_monitor()

# В игровом цикле
monitor.start_frame()
# ... игровой код ...
monitor.end_frame()

# Получить метрики
metrics = monitor.metrics
print(f"FPS: {metrics.fps}, CPU: {metrics.cpu_percent}%, Memory: {metrics.memory_mb}MB")
```

### Система достижений

```python
from game import get_achievements_manager

achievements = get_achievements_manager()

# Обновление статистики
achievements.update_stats({
    'score': 5000,
    'lines_cleared': 50,
    'level': 10
})

# Получить прогресс
print(f"Разблокировано: {achievements.get_completion_percentage():.1f}%")

# Сохранение
achievements.save()
```

### Отладка UI компонентов

```python
from ui import AnimatedButton, ProgressBar, LoadingSpinner

# Создание кнопки с анимацией
button = AnimatedButton(
    x=100, y=100, width=200, height=50,
    text="Старт", font=font,
    callback=lambda: print("Clicked!")
)

# В игровом цикле
button.update(dt)
button.draw(screen)
```

## Идеи дальнейшего улучшения (можно реализовать)

- Эффекты частиц и анимация при очистке линий
- Таблица рекордов (несколько слотов сохранения, локальный лидерборд)
- Интеграция с `pygame_menu` для более выразительных меню и настроек
- Онлайновые таблицы рекордов (через простой REST API)
- Поддержка горячих клавиш для смены громкости и включения/выключения музыки
- Система ежедневных испытаний
- Режим марафона (150 линий)
- Спектр-режим (анализ ошибок)

## Структура проекта

```
Tetris Enhanced/
├── game/                      # Игровые модули
│   ├── achievements.py        # Система достижений
│   ├── daily_challenges.py    # Ежедневные испытания
│   ├── player_stats.py        # Статистика игрока
│   ├── leaderboard.py         # Таблица лидеров
│   ├── integration.py         # Интеграция систем
│   ├── particles.py           # Система частиц
│   ├── state_manager.py       # Менеджер состояний
│   └── __init__.py
├── ui/                        # UI компоненты
│   ├── advanced_components.py # Продвинутые виджеты
│   └── __init__.py
├── utils/                     # Утилиты
│   ├── logger.py             # Логирование
│   ├── performance.py        # Производительность
│   └── __init__.py
├── tests/                     # Тесты
│   ├── test_framework.py
│   ├── quick_adaptive_test.py
│   └── test_responsive_design.py
├── logs/                      # Логи (авто)
├── error_reports/             # Отчёты (авто)
├── music/                     # Музыка
├── sounds/                    # Звуки
├── saves/                     # Сохранения (авто)
├── img/                       # Изображения
├── archive/                   # Архив
├── tetris_enhanced.py         # Основная игра
├── game_config.py             # Конфигурация
├── config.json                # Настройки
├── requirements.txt           # Зависимости
├── run_tests.py               # Запуск тестов
├── README.md                  # Документация
├── CHANGELOG.md               # История изменений
└── LICENCE                    # Лицензия
```

## Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENCE](LICENCE) для деталей.

---

## Авторы

| Роль | Имя | Контакты |
|------|-----|----------|
| **Автор и разработчик** | Дуплей Максим Игоревич | [Telegram 1](https://t.me/quadd4rv1n7), [Telegram 2](https://t.me/dupley_maxim_1999) |
| **Email** | | maksimqwe42@mail.ru |
| **ORCID** | | [0009-0007-7605-539X](https://orcid.org/0009-0007-7605-539X) |
| **DOI** | | [10.5281/zenodo.17264455](https://doi.org/10.5281/zenodo.17264455) |

---

**Дата выпуска версии 2.1:** 23 февраля 2026 г.

**Версия:** 2.1.0

[![Star History Chart](https://api.star-history.com/svg?repos=QuadDarv1ne/Tetris-Enhanced&type=Date)](https://star-history.com/#QuadDarv1ne/Tetris-Enhanced&Date)
