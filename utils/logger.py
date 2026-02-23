#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced logging and error handling utilities for Tetris Enhanced
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Optional, Callable, Any, TypeVar, ParamSpec
from functools import wraps
from enum import Enum

# Type variables for decorator
P = ParamSpec('P')
R = TypeVar('R')


class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class EnhancedLogger:
    """
    Улучшенный класс логирования с поддержкой:
    - Контекстного логирования
    - Форматированного вывода
    - Автоматического создания отчётов об ошибках
    - Статистики ошибок
    """

    _instance: Optional['EnhancedLogger'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> 'EnhancedLogger':
        """Реализация паттерна Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        log_dir: str = "logs",
        log_level: int = logging.DEBUG,
        console_output: bool = True,
        file_output: bool = True,
        error_report_dir: str = "error_reports"
    ):
        if EnhancedLogger._initialized:
            return

        EnhancedLogger._initialized = True

        self.log_dir = log_dir
        self.error_report_dir = error_report_dir
        self.console_output = console_output
        self.file_output = file_output

        # Создаём директории
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(error_report_dir, exist_ok=True)

        # Настраиваем логгер
        self.logger = logging.getLogger("TetrisEnhanced")
        self.logger.setLevel(log_level)
        self.logger.handlers.clear()

        # Формат логов
        self.log_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Консольный обработчик
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(self.log_format)
            self.logger.addHandler(console_handler)

        # Файловый обработчик
        if file_output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"tetris_{timestamp}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self.log_format)
            self.logger.addHandler(file_handler)
            self.current_log_file = log_file

        # Статистика ошибок
        self.error_stats = {
            'total_errors': 0,
            'errors_by_type': {},
            'last_error': None,
            'last_error_time': None
        }

        self._log_system_info()

    def _log_system_info(self):
        """Логирует системную информацию"""
        import platform
        try:
            import pygame
            pygame_version = pygame.ver
        except ImportError:
            pygame_version = "not installed"

        self.info("=" * 60)
        self.info("TETRIS ENHANCED - Системная информация")
        self.info("=" * 60)
        self.info(f"Python version: {sys.version}")
        self.info(f"Platform: {platform.platform()}")
        self.info(f"Pygame version: {pygame_version}")
        self.info(f"Working directory: {os.getcwd()}")
        self.info("=" * 60)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)

    def error(
        self,
        message: str,
        exc_info: Optional[Exception] = None,
        log_stack_trace: bool = True,
        **kwargs
    ):
        """
        Log error with optional exception info

        Args:
            message: Error message
            exc_info: Exception object if available
            log_stack_trace: Whether to log full stack trace
        """
        self.logger.error(message, **kwargs)

        # Обновляем статистику
        self.error_stats['total_errors'] += 1
        self.error_stats['last_error'] = str(exc_info) if exc_info else message
        self.error_stats['last_error_time'] = datetime.now()

        error_type = type(exc_info).__name__ if exc_info else "Unknown"
        self.error_stats['errors_by_type'][error_type] = \
            self.error_stats['errors_by_type'].get(error_type, 0) + 1

        if exc_info and log_stack_trace:
            stack_trace = traceback.format_exc()
            self.logger.error(f"Stack trace:\n{stack_trace}")
            self._create_error_report(message, exc_info, stack_trace)

    def critical(
        self,
        message: str,
        exc_info: Optional[Exception] = None,
        **kwargs
    ):
        """Log critical error"""
        self.logger.critical(message, **kwargs)
        if exc_info:
            stack_trace = traceback.format_exc()
            self.logger.critical(f"Stack trace:\n{stack_trace}")
            self._create_error_report(message, exc_info, stack_trace, critical=True)

    def _create_error_report(
        self,
        message: str,
        exception: Optional[Exception],
        stack_trace: str,
        critical: bool = False
    ):
        """Создаёт отчёт об ошибке"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_type = "critical" if critical else "error"
        report_file = os.path.join(
            self.error_report_dir,
            f"{report_type}_{timestamp}.txt"
        )

        try:
            import platform

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"ОТЧЁТ ОБ ОШИБКЕ {'(КРИТИЧЕСКАЯ)' if critical else ''}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Сообщение: {message}\n\n")

                if exception:
                    f.write(f"Тип исключения: {type(exception).__name__}\n")
                    f.write(f"Исключение: {exception}\n\n")

                f.write("Стек вызовов:\n")
                f.write("-" * 60 + "\n")
                f.write(stack_trace)
                f.write("-" * 60 + "\n\n")

                # Системная информация
                f.write("Системная информация:\n")
                f.write(f"  Python: {sys.version}\n")
                f.write(f"  Platform: {platform.platform()}\n")
                f.write(f"  Working dir: {os.getcwd()}\n")

                try:
                    import pygame
                    f.write(f"  Pygame: {pygame.ver}\n")
                except ImportError:
                    f.write("  Pygame: not installed\n")

            self.info(f"Error report created: {report_file}")
        except Exception as e:
            self.error(f"Failed to create error report: {e}")

    def get_error_stats(self) -> dict:
        """Возвращает статистику ошибок"""
        return self.error_stats.copy()

    def log_context(self, context_name: str):
        """
        Возвращает контекстный менеджер для логирования блока кода

        Usage:
            with logger.log_context("Loading assets"):
                load_assets()
        """
        return LogContext(self, context_name)

    def get_error_summary(self) -> str:
        """Возвращает сводку по ошибкам"""
        stats = self.error_stats
        summary = [
            f"Всего ошибок: {stats['total_errors']}",
            f"Последняя ошибка: {stats['last_error']}",
            f"Время последней ошибки: {stats['last_error_time']}"
        ]

        if stats['errors_by_type']:
            summary.append("\nОшибки по типам:")
            for error_type, count in sorted(
                stats['errors_by_type'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                summary.append(f"  {error_type}: {count}")

        return "\n".join(summary)


class LogContext:
    """Контекстный менеджер для логирования блоков кода"""

    def __init__(self, logger: EnhancedLogger, context_name: str):
        self.logger = logger
        self.context_name = context_name
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"▶️  Начало: {self.context_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type is not None:
            self.logger.error(
                f"❌ Ошибка в блоке '{self.context_name}' "
                f"(длительность: {duration:.3f}s): {exc_val}",
                exc_info=exc_val
            )
        else:
            self.logger.debug(
                f"✅ Завершено: {self.context_name} "
                f"(длительность: {duration:.3f}s)"
            )

        return False  # Не подавляем исключения


def log_function_call(
    logger: Optional[EnhancedLogger] = None,
    log_level: str = "debug",
    log_args: bool = True,
    log_result: bool = False,
    log_errors: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор для логирования вызовов функций

    Args:
        logger: Экземпляр EnhancedLogger
        log_level: Уровень логирования (debug, info)
        log_args: Логировать ли аргументы
        log_result: Логировать ли результат
        log_errors: Логировать ли ошибки
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            log_func = getattr(logger, log_level) if logger else print

            # Формируем информацию об аргументах
            args_info = ""
            if log_args:
                args_str = ", ".join(repr(a) for a in args[:3])  # Первые 3 аргумента
                kwargs_str = ", ".join(f"{k}={v!r}" for k, v in list(kwargs.items())[:3])
                args_info = f"({args_str}{', ' if args_str and kwargs_str else ''}{kwargs_str})"

            log_func(f"🔹 Вызов: {func.__name__}{args_info}")

            try:
                result = func(*args, **kwargs)

                if log_result:
                    result_str = str(result)[:100]  # Ограничиваем длину
                    log_func(f"✅ Результат: {func.__name__} -> {result_str}")

                return result

            except Exception as e:
                if log_errors and logger:
                    logger.error(
                        f"❌ Ошибка в {func.__name__}: {e}",
                        exc_info=e
                    )
                raise

        return wrapper
    return decorator


def safe_call(
    default_return: Any = None,
    on_error: Optional[Callable[[Exception], Any]] = None,
    log_errors: bool = True
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор для безопасного вызова функций (подавляет исключения)

    Args:
        default_return: Значение по умолчанию при ошибке
        on_error: Функция-обработчик ошибки
        log_errors: Логировать ли ошибки
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger = EnhancedLogger()
                    logger.error(f"Safe call error in {func.__name__}: {e}", exc_info=e)

                if on_error:
                    return on_error(e)

                return default_return

        return wrapper
    return decorator


# Глобальный экземпляр логгера
_logger_instance: Optional[EnhancedLogger] = None


def get_logger() -> EnhancedLogger:
    """Возвращает глобальный экземпляр логгера"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EnhancedLogger()
    return _logger_instance


def init_logger(
    log_dir: str = "logs",
    log_level: int = logging.DEBUG,
    console_output: bool = True,
    file_output: bool = True
) -> EnhancedLogger:
    """Инициализирует и возвращает логгер"""
    global _logger_instance
    _logger_instance = EnhancedLogger(
        log_dir=log_dir,
        log_level=log_level,
        console_output=console_output,
        file_output=file_output
    )
    return _logger_instance


# Convenience functions
def log_debug(message: str, **kwargs):
    get_logger().debug(message, **kwargs)


def log_info(message: str, **kwargs):
    get_logger().info(message, **kwargs)


def log_warning(message: str, **kwargs):
    get_logger().warning(message, **kwargs)


def log_error(message: str, exc_info=None, **kwargs):
    get_logger().error(message, exc_info=exc_info, **kwargs)


def log_critical(message: str, exc_info=None, **kwargs):
    get_logger().critical(message, exc_info=exc_info, **kwargs)
