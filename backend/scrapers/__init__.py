"""
Web scrapers module.
"""
from .base_scraper import BaseScraper
from .acara_scraper import AcaraScraper
from .adefa_scraper import AdefaScraper
from .dnrpa_scraper import DNRPAScraper

__all__ = [
    "BaseScraper",
    "AcaraScraper",
    "AdefaScraper",
    "DNRPAScraper",
]
