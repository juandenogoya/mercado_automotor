"""
Web scrapers module.
"""
from .base_scraper import BaseScraper
from .acara_scraper import AcaraScraper
from .adefa_scraper import AdefaScraper

__all__ = [
    "BaseScraper",
    "AcaraScraper",
    "AdefaScraper",
]
