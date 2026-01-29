# /home/makse/projects/geo-app/api/database.py
"""
Cache bazy danych dla adresów i współrzędnych
"""

import sqlite3
from datetime import datetime
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LocationCache:
    """Zarządzanie cache'em lokalizacji w SQLite"""
    
    def __init__(self, db_path: str = "locations_cache.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicjalizacja bazy danych"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY,
                    address TEXT UNIQUE NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info(f"Baza danych zainicjowana: {self.db_path}")
    
    def get(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Pobierz współrzędne z cache'u
        
        Args:
            address: Adres do wyszukania
            
        Returns:
            Tuple (latitude, longitude) lub None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT latitude, longitude FROM locations WHERE address = ?",
                    (address,)
                )
                row = cursor.fetchone()
                if row:
                    logger.debug(f"Cache hit: {address}")
                    return (row[0], row[1])
        except Exception as e:
            logger.error(f"Błąd odczytu cache'u: {e}")
        
        return None
    
    def save(self, address: str, latitude: float, longitude: float) -> bool:
        """
        Zapisz współrzędne w cache'u
        
        Args:
            address: Adres
            latitude: Szerokość geograficzna
            longitude: Długość geograficzna
            
        Returns:
            True jeśli sukces
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO locations (address, latitude, longitude) VALUES (?, ?, ?)",
                    (address, latitude, longitude)
                )
                conn.commit()
                logger.debug(f"Zapisano w cache: {address}")
                return True
        except Exception as e:
            logger.error(f"Błąd zapisu cache'u: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Pobierz statystyki cache'u"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM locations")
                count = cursor.fetchone()[0]
                return {"cached_locations": count}
        except Exception as e:
            logger.error(f"Błąd statystyk: {e}")
            return {"cached_locations": 0}