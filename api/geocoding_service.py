
"""
Serwis geokodowania z cache'owaniem
"""

from typing import Optional, Tuple
import logging
from geopy.geocoders import ArcGIS
from api.database import LocationCache

logger = logging.getLogger(__name__)

class GeocodingService:
    """Serwis geokodowania z cache"""
    
    def __init__(self, cache_db: str = "locations_cache.db", timeout: int = 10):
        self.cache = LocationCache(cache_db)
        self.timeout = timeout
        self.geocoder = ArcGIS(timeout=timeout)
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geokoduj adres (z cache)
        
        Args:
            address: Adres do geokodowania
            
        Returns:
            Tuple (latitude, longitude) lub None
        """
        if not address or address == "Brak adresu":
            return None
        
        
        cached = self.cache.get(address)
        if cached:
            logger.info(f"Cache hit: {address}")
            return cached
        
        
        try:
            full_address = f"{address}, Warszawa, Polska"
            location = self.geocoder.geocode(full_address)
            
            if location:
                coords = (location.latitude, location.longitude)
                self.cache.save(address, location.latitude, location.longitude)
                logger.info(f"Geokodowano: {address} -> {coords}")
                return coords
        except Exception as e:
            logger.error(f"Błąd geokodowania '{address}': {e}")
        
        return None