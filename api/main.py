# /home/makse/projects/geo-app/api/main.py
"""
FastAPI server dla geoportalu wydarzeń Warszawy
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, timedelta
from typing import List, Optional
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from logic.parser_update import Waw4FreeParser, EventBox
from api.geocoding_service import GeocodingService
# Inicjalizacja serwisów PRZED definicją app
parser = Waw4FreeParser()
geocoding_service = GeocodingService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup i shutdown events"""
    # Startup
    logger.info("Inicjalizacja cache'u...")
    geocoding_service.cache._init_db()
    
    yield
    
    # Shutdown
    logger.info("Zamykanie aplikacji...")


# Dodaj parent directory do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))



# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicjalizacja
app = FastAPI(
    title="Geoportal Warszawy",
    description="API do pobierania geokodowanych wydarzeń z Warszawy",
    version="1.0.0",
    lifespan=lifespan  # Dodaj to
)

WARSAW_BBOX = {
    'min_lat': 51.53,
    'max_lat': 52.45,
    'min_lon': 20.73,
    'max_lon': 21.36
}


def is_within_warsaw(lat: float, lon: float) -> bool:
    """Sprawdza czy koordynata jest w Warszawie + 10 km"""
    return (WARSAW_BBOX['min_lat'] <= lat <= WARSAW_BBOX['max_lat'] and
            WARSAW_BBOX['min_lon'] <= lon <= WARSAW_BBOX['max_lon'])


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Pydantic modele
from pydantic import BaseModel

class EventResponse(BaseModel):
    """Model odpowiedzi dla eventu"""
    title: str
    address: Optional[str]
    district: Optional[str]
    date: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    time: Optional[str]
    image: Optional[str]
    link: str
    category: Optional[List[str]]
    latitude: Optional[float]
    longitude: Optional[float]

class EventsResponse(BaseModel):
    """Model odpowiedzi dla listy eventów"""
    date: str
    total: int
    events: List[EventResponse]

class StatsResponse(BaseModel):
    """Model statystyk"""
    cached_locations: int

# Endpointy

@app.get("/api/events/geojson")
async def get_events_geojson(day: int, month: int, year: int):
    """
    Pobierz wydarzenia jako GeoJSON
    
    Query params:
    - day: dzień (1-31)
    - month: miesiąc (1-12)
    - year: rok
    
    Returns:
        GeoJSON FeatureCollection
    """
    try:
        # Walidacja daty
        try:
            event_date = date(year, month, day)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Nieprawidłowa data: {e}")
        
        # Pobierz eventy
        raw_events = parser.get_events_from_date(day, month, year)
        
        # Stwórz GeoJSON features
        features = []
        for event in raw_events:
            if isinstance(event, EventBox):
                # Geokoduj adres
                coords = geocoding_service.geocode(event.address) if event.address else None
                
                if coords and is_within_warsaw(coords[0], coords[1]):
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [coords[1], coords[0]]  # GeoJSON: [lon, lat]
                        },
                        "properties": {
                            "title": event.title,
                            "address": event.address,
                            "district": event.district,
                            "date": event.date,
                            "start_date": event.start_date,
                            "end_date": event.end_date,
                            "time": event.time,
                            "image": event.image,
                            "link": event.plink,
                            "category": event.box_category or []
                        }
                    }
                    features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return geojson
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events", response_model=EventsResponse)
async def get_events(day: int, month: int, year: int) -> EventsResponse:
    """
    Pobierz geokodowane wydarzenia dla daty
    
    Query params:
    - day: dzień (1-31)
    - month: miesiąc (1-12)
    - year: rok
    
    Returns:
        Lista eventów z współrzędnymi
    """
    try:
        # Walidacja daty
        try:
            event_date = date(year, month, day)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Nieprawidłowa data: {e}")
        
        # Pobierz eventy
        raw_events = parser.get_events_from_date(day, month, year)
        
        # Geokoduj i sformatuj
        events_response = []
        for event in raw_events:
            if isinstance(event, EventBox):
                # Geokoduj adres
                coords = geocoding_service.geocode(event.address) if event.address else None
                
                event_data = EventResponse(
                    title=event.title,
                    address=event.address,
                    district=event.district,
                    date=event.date,
                    start_date=event.start_date,
                    end_date=event.end_date,
                    time=event.time,
                    image=event.image,
                    link=event.plink,
                    category=event.box_category,
                    latitude=coords[0] if coords else None,
                    longitude=coords[1] if coords else None,
                )
                events_response.append(event_data)
        
        return EventsResponse(
            date=f"{day:02d}.{month:02d}.{year}",
            total=len(events_response),
            events=events_response
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events-range")
async def get_events_range(start_day: int, start_month: int, start_year: int,
                          end_day: int, end_month: int, end_year: int):
    """
    Pobierz eventy z zakresu dat
    """
    try:
        start = date(start_year, start_month, start_day)
        end = date(end_year, end_month, end_day)
        
        all_events = []
        current = start
        
        while current <= end:
            events = await get_events(current.day, current.month, current.year)
            all_events.extend(events.events)
            current += timedelta(days=1)
        
        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "total": len(all_events),
            "events": all_events
        }
    except Exception as e:
        logger.error(f"Błąd: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cache/stats", response_model=StatsResponse)
async def get_cache_stats():
    """Statystyki cache'u"""
    stats = geocoding_service.cache.get_stats()
    return StatsResponse(**stats)

@app.post("/api/cache/clear")
async def clear_cache():
    """Wyczyść cache"""
    try:
        import os
        if os.path.exists("locations_cache.db"):
            os.remove("locations_cache.db")
        geocoding_service.cache._init_db()
        return {"message": "Cache wyczyszczony"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Informacje o API"""
    return {
        "name": "Geoportal Warszawy - API",
        "version": "1.0.0",
        "endpoints": {
            "events": "/api/events?day=29&month=1&year=2026",
            "events_range": "/api/events-range?start_day=29&start_month=1&start_year=2026&end_day=5&end_month=2&end_year=2026",
            "cache_stats": "/api/cache/stats",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)