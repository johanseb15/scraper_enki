"""
Módulo de exportación de scrapers.
Asegura compatibilidad tanto si el módulo base se llama 'base' como 'base_scraper'.
"""

try:
    from .base import BaseScraper
except ImportError:
    from .base_scraper import BaseScraper

__all__ = ["BaseScraper"]