"""
Parser wydarzeń z waw4free.pl
Pobiera i parsuje wydarzenia z Warszawy
"""

from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass, asdict
from typing import List, Optional, Union
from functools import lru_cache
from datetime import datetime, date
import logging
from urllib.parse import urljoin
import json
from geopy import geocoders, Location
from geopy.geocoders import ArcGIS

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stałe
BASE_URL = "https://waw4free.pl/"
DISTRICTS = [
    "Mokotów", "Praga-Południe", "Białołęka", "Wola", "Ursynów", 
    "Bielany", "Śródmieście", "Wawer", "Ochota", "Ursus", 
    "Praga-Północ", "Wesoła", "Żoliborz", "Wilanów", "Włochy", "Rembertów"
]

@dataclass
class EventBox:
    """Reprezentacja wydarzenia"""
    title: str
    image: str
    district: Optional[str]
    address: Optional[str]
    plink: str
    box_category: List[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    position: Optional[tuple[float, float]] = None # (lat, long)
    
    def to_dict(self):
        """Konwersja do słownika"""
        data = asdict(self)
        # Konwertuj position na listę dla JSON
        if data['position'] is not None:
            data['position'] = {'latitude': data['position'][0], 'longitude': data['position'][1]}
        return data
    
    def to_json(self):
        """Konwersja do JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

@dataclass
class OtherBox:
    """Reprezentacja innego typu wydarzenia"""
    title: str
    image: str
    info: str
    plink: str
    
    def to_dict(self):
        return asdict(self)


class Waw4FreeParser:
    """Główna klasa parsera wydarzeń"""
    
    def __init__(self, base_url: str = BASE_URL, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Waw4FreeParser/1.0)'
        })
        
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Pobiera i parsuje stronę z obsługą błędów
        
        Args:
            url: URL strony do pobrania
            
        Returns:
            BeautifulSoup object lub None w przypadku błędu
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Błąd podczas pobierania {url}: {e}")
            return None
    
    @lru_cache(maxsize=100)
    def _get_address(self, url: str) -> str:
        """
        Pobiera adres z dedykowanej strony wydarzenia (z cache)
        
        Args:
            url: URL strony wydarzenia
            
        Returns:
            Adres lub komunikat o braku adresu
        """
        soup = self._get_page(url)
        if not soup:
            return "Brak adresu (błąd pobierania)"
        
        try:
            location_elem = soup.find(attrs={"itemprop": 'location'})
            if not location_elem:
                return "Brak adresu"
            
            address = location_elem.text.strip()
            address = address.replace("Warszawa", "").strip()
            
            # Usuń dzielnicę z adresu
            for district in DISTRICTS:
                address = address.replace(district, "").strip()
            
            address = address.replace(",", "").strip()
            return address if address else "Brak adresu"
        except Exception as e:
            logger.error(f"Błąd parsowania adresu z {url}: {e}")
            return "Brak adresu"
    
    def _extract_district(self, text: str) -> Optional[str]:
        """Wyciąga nazwę dzielnicy z tekstu"""
        for district in DISTRICTS:
            if district in text:
                return district
        return None
    
    def geocode_addr(self,address: str) -> Optional[Location]:
            """ 
                Geokoding przy pomocy ArcGIS.
                
                Args:
                    address: Adres do geokodowania

                Returns:
                    Tuple (latitude, longitude) lub None jeśli nie udało się geokodować
            """
            if not address or address == "Brak adresu":
                return None
            
            try:
                geolocator = ArcGIS(timeout=self.timeout)
                full_address = f"{address}, Warszawa, Polska"
                location = geolocator.geocode(full_address)
                
                if location:
                    return (location.latitude, location.longitude)
                return None
            except Exception as e:
                logger.error(f"Błąd geokodowania adresu '{address}': {e}")
                return None


    def _parse_date_interval(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parsuje przedział dat (np. '12.01.2026 - 15.01.2026')
        
        Returns:
            Tuple (start_date, end_date)
        """
        words = text.split()
        try:
            separator_idx = words.index("-")
            start_date = words[separator_idx - 1].strip(",.;")
            end_date = words[separator_idx + 1].strip(",.;")
            return start_date, end_date
        except (ValueError, IndexError):
            return None, None
    
    def _parse_box_data(self, box) -> Optional[Union[EventBox, OtherBox]]:
        """
        Parsuje pojedynczy box wydarzenia
        
        Args:
            box: BeautifulSoup element box
            
        Returns:
            EventBox, OtherBox lub None w przypadku błędu
        """
        try:
            # Podstawowe dane
            a_tag = box.find("a")
            if not a_tag:
                return None
            
            title = a_tag.attrs.get('title', 'Brak tytułu')
            link = urljoin(self.base_url, a_tag.attrs.get('href', ''))
            
            # Obraz
            image_div = box.find('div', class_='box-image')
            image = ""
            if image_div and 'style' in image_div.attrs:
                style = image_div.attrs['style']
                image = style.replace("background-image: url('", "").replace("');", "")
                image = urljoin(self.base_url, image)
            
            # Data i lokalizacja
            date_div = box.find('div', class_='box-data')
            date_line = date_div.text.strip() if date_div else ""
            
            # Kategorie - ulepszone parsowanie
            category_div = box.find('div', class_='box-category')
            categories = []
            if category_div:
                # Usuń nadmiarowe białe znaki i zamień na spacje
                cat_text = category_div.text.replace("\n", " ").replace("\t", " ")
                # Podziel na słowa i usuń przecinki
                words = [w.strip().strip(',') for w in cat_text.split() if w.strip()]
                
                # Łącz przyimki z następnymi słowami
                prepositions = ['dla', 'po', 'w', 'na', 'z', 'bez', 'do', 'od']
                i = 0
                while i < len(words):
                    word = words[i].lower()
                    # Jeśli to przyimek i jest następne słowo
                    if word in prepositions and i + 1 < len(words):
                        # Połącz przyimek z następnym słowem
                        combined = f"{words[i]} {words[i + 1]}"
                        categories.append(combined)
                        i += 2  # Pomiń następne słowo
                    else:
                        categories.append(words[i])
                        i += 1
            
            # Parsowanie daty i dzielnicy
            district = self._extract_district(date_line)
            start_date, end_date = self._parse_date_interval(date_line)
            
            # Jeśli nie ma dzielnicy, traktuj jako OtherBox
            if not district:
                info = date_line.strip()
                return OtherBox(title=title, image=image, info=info, plink=link)
            
            # Parsowanie pojedynczej daty i czasu
            single_date = None
            single_time = None
            
            if not start_date and not end_date:
                # Próba wyciągnięcia daty i czasu
                parts = date_line.replace(district, "").strip().split()
                if len(parts) >= 2:
                    single_date = parts[0].strip(",.;")
                    single_time = parts[1].strip(",.;")
            
            # Adres (tylko jeśli potrzebny - można wyłączyć dla szybszego parsowania)
            address = self._get_address(link)  # Zakomentuj jeśli zbyt wolne
            # address = None  # Można pobrać później tylko dla wybranych eventów
            # to geocode address 
            geocoded_location = self.geocode_addr(address)
            return EventBox(
                title=title,
                image=image,
                district=district,
                address=address,
                plink=link,
                box_category=categories,
                start_date=start_date,
                end_date=end_date,
                date=single_date,
                time=single_time,
                position=geocoded_location
            )
            
        except Exception as e:
            logger.error(f"Błąd parsowania boxa: {e}")
            return None
    
    def get_events_from_date(self, day: int, month: int, year: int) -> List[Union[EventBox, OtherBox]]:
        """
        Pobiera wydarzenia z konkretnej daty
        
        Args:
            day: dzień (1-31)
            month: miesiąc (1-12)
            year: rok
            
        Returns:
            Lista obiektów EventBox/OtherBox
        """
        url = f"{self.base_url}warszawa-wydarzenia-{year}-{month}-{day}"
        soup = self._get_page(url)
        
        if not soup:
            logger.error(f"Nie udało się pobrać strony dla {day}-{month}-{year}")
            return []
        
        # Sprawdź czy są wydarzenia
        if soup.find(string="W tym dniu nie ma jeszcze żadnych wydarzeń."):
            logger.info(f"Brak wydarzeń na {day}-{month}-{year}")
            return []
        
        if soup.find(string="Strona, której szukasz nie istnieje."):
            logger.warning(f"Nieprawidłowa data: {day}-{month}-{year}")
            return []
        
        return self.parse_boxes(soup)
    
    def parse_boxes(self, soup: BeautifulSoup) -> List[Union[EventBox, OtherBox]]:
        """
        Parsuje wszystkie boxy ze strony
        
        Args:
            soup: Obiekt BeautifulSoup strony
            
        Returns:
            Lista wydarzeń
        """
        boxes = soup.find_all('div', class_="box")
        events = []
        
        for box in boxes:
            event = self._parse_box_data(box)
            if event:
                events.append(event)
        
        logger.info(f"Znaleziono {len(events)} wydarzeń")
        return events
    
    def get_recommended_events(self) -> List[Union[EventBox, OtherBox]]:
        """Pobiera polecane wydarzenia ze strony głównej"""
        soup = self._get_page(self.base_url)
        if not soup:
            return []
        return self.parse_boxes(soup)
    
    def get_events_range(self, start_date: date, end_date: date) -> List[Union[EventBox, OtherBox]]:
        """
        Pobiera wydarzenia z zakresu dat
        
        Args:
            start_date: data początkowa
            end_date: data końcowa
            
        Returns:
            Lista wszystkich wydarzeń z zakresu
        """
        all_events = []
        current = start_date
        
        while current <= end_date:
            events = self.get_events_from_date(current.day, current.month, current.year)
            all_events.extend(events)
            current = date.fromordinal(current.toordinal() + 1)
        
        return all_events
    
    def enrich_with_addresses(self, events: List[EventBox]) -> List[EventBox]:
        """
        Dodaje adresy i współrzędne do wydarzeń
        
        Args:
            events: Lista wydarzeń
            
        Returns:
            Lista wydarzeń z adresami i współrzędnymi
        """
        for event in events:
            if isinstance(event, EventBox):
                if not event.address:
                    event.address = self._get_address(event.plink)
                if not event.position and event.address:
                    event.position = self.geocode_addr(event.address)
        return events
    
    def export_to_geojson(self, events: List[EventBox], filename: str):
        """Eksportuje wydarzenia do pliku GeoJSON"""
        features = []
        
        for event in events:
            if isinstance(event, EventBox) and event.position:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [event.position[1], event.position[0]]  # GeoJSON: [lon, lat]
                    },
                    "properties": {
                        "title": event.title,
                        "address": event.address,
                        "district": event.district,
                        "date": event.date,
                        "start_date": event.start_date,
                        "end_date": event.end_date,
                        "time": event.time,
                        "category": event.box_category,
                        "image": event.image,
                        "link": event.plink
                    }
                }
                features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        logger.info(f"Wyeksportowano {len(features)} wydarzeń do {filename}")


# Przykład użycia
if __name__ == "__main__":
    parser = Waw4FreeParser()
    
    # # Przykład 1: Wydarzenia z konkretnej daty
    # events = parser.get_events_from_date(29, 1, 2026)
    # print(f"\nZnaleziono {len(events)} wydarzeń na 29.01.2026")
    
    # # # Przykład 2: Polecane wydarzenia
    # # recommended = parser.get_recommended_events()
    # # print(f"\nPolecane wydarzenia: {len(recommended)}")
    
    # # # Przykład 3: Wydarzenia z zakresu dat
    # # from datetime import date, timedelta
    # # today = date(2026, 1, 29)
    # # week_later = today + timedelta(days=7)
    # # weekly_events = parser.get_events_range(today, week_later)
    # # print(f"\nWydarzenia w ciągu tygodnia: {len(weekly_events)}")
    
    # # Przykład 4: Eksport do JSON
    # if events:
    #     parser.export_to_geojson(events, "wydarzenia_29_01_2026.geojson")
    
    # Przykład 5: Dodanie adresów (opcjonalne, wolne)
    # events_with_addresses = parser.enrich_with_addresses(events[:5])  # Tylko pierwsze 5