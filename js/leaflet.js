// ============================================
// INICJALIZACJA MAPY I WARSTW
// ============================================

var map = L.map('map_container',
    {loadingControl: true}
).setView([52.2298, 21.0118], 13);

// Lokalizacja użytkownika
L.control.locate({
    position: 'topleft',
    strings: {
        title: "Pokaż moją lokalizację"
    },
    locateOptions: {
        maxZoom: 16,
        enableHighAccuracy: true
    },
    flyTo: true,
    keepCurrentZoomLevel: false,
    circleStyle: {
        color: '#4266f4ff',
        fillColor: '#4285F4',
        fillOpacity: 0.15,
        weight: 2
    },
    markerStyle: {
        color: '#4285F4',
        fillColor: '#4285F4',
        fillOpacity: 0.8,
        weight: 2
    }
}).addTo(map);


// Warstwy bazowe
const basic_layer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
});

const dark_layer = L.tileLayer('http://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL '
});

const esri_standard_layer = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles © Esri Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012 '
});

const esri_imagery_layer = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: '© Esri Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community '
});

// Geoportal warstwy (można później dodać)
// const geoportal_high_res_layer = L.tileLayer('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution/{y}/{x}', {
//     maxZoom: 19,
//     attribution: 'Główny Urząd Geodezji i Kartografii'
// });

var baseMaps = {
    "OpenStreetMap": basic_layer,
    "Dark Map": dark_layer,
    "Esri Standard Map": esri_standard_layer,
    "Esri Imagery Map": esri_imagery_layer
};

// Domyślna mapa
esri_standard_layer.addTo(map);
var layerControl = L.control.layers(baseMaps).addTo(map);

// ============================================
// KONFIGURACJA APLIKACJI
// ============================================

const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://geo-app-6cmk.onrender.com'; 

// Mapowanie kategorii na kolory
const categoryColors = {
    // Kultura i sztuka
    'kultura': '#E91E63',
    'sztuka': '#3F51B5',
    'teatr': '#673AB7',
    'film': '#2196F3',
    'literatura': '#795548',
    'fotografia': '#607D8B',
    
    // Muzyka i taniec
    'muzyka': '#9C27B0',
    'taniec': '#F06292',
    'koncert': '#AB47BC',
    'jazz': '#BA68C8',
    
    // Edukacja
    'nauka': '#FF9800',
    'edukacja': '#FFC107',
    'warsztaty': '#FF5722',
    'wykład': '#FFB300',
    'szkolenie': '#FB8C00',
    
    // Dla dzieci
    'dziecko': '#FFEB3B',
    'dla dzieci': '#FFEB3B',
    'rodzina': '#FDD835',
    
    // Sport i rekreacja
    'sport': '#4CAF50',
    'fitness': '#66BB6A',
    'joga': '#81C784',
    'bieganie': '#388E3C',
    
    // Przyroda i ekologia
    'przyroda': '#8BC34A',
    'ekologia': '#9CCC65',
    'ogród': '#AED581',
    
    // Festiwale i wydarzenia
    'festiwal': '#00BCD4',
    'koncert': '#26C6DA',
    'piknik': '#4DD0E1',
    
    // Historia i dziedzictwo
    'historia': '#9E9E9E',
    'zabytki': '#BDBDBD',
    'muzeum': '#757575',
    
    // Społeczność
    'wolontariat': '#03A9F4',
    'spotkanie': '#29B6F6',
    'debata': '#4FC3F7',
    
    // Biznes
    'biznes': '#FF5722',
    'networking': '#FF7043',
    'targi': '#FF8A65',
    
    // Technologia
    'technologia': '#00BCD4',
    'it': '#00ACC1',
    
    // Jedzenie i kulinaria
    'kulinaria': '#FF6F00',
    'degustacja': '#FF8F00',
    'kuchnia': '#FFA000',
    
    // Języki
    'po angielsku': '#5C6BC0',
    'po niemiecku': '#7E57C2',
    'po francusku': '#9575CD',
    'po hiszpańsku': '#B39DDB',
    'po polsku': '#7986CB',
    
    // Lokalizacje/konteksty
    'w plenerze': '#689F38',
    'na świeżym powietrzu': '#7CB342',
    'online': '#42A5F5',
    'wirtualne': '#64B5F6',
    'dla seniorów':'#9575CD',
    'impreza':'#2d0c65ff',
    'stand up':'#b32facff',
    'slajdowisko':'#639fa9ff',

    
    // Inne
    'inne': '#585a5bff',
    'różne': '#353b3eff'
};

// ============================================
// ZMIENNE GLOBALNE
// ============================================

let eventsLayer;
let usedCategories = new Set();
let activeCategories = new Set();

// ============================================
// FUNKCJE POMOCNICZE
// ============================================

function normalizeCategoryName(name) {
    return (name || '').trim().toLowerCase();
}

// Pobieranie pierwszej istotnej kategorii (nie "Inne")
function getPrimaryCategory(categories) {
    if (!categories || categories.length === 0) return 'Inne';
    
    for (let cat of categories) {
        const normalized = cat.trim();
        if (normalized !== 'Inne' && normalized !== '') {
            return normalized;
        }
    }
    
    return categories[0] || 'Inne';
}

// Delegowany listener na kontener legendy
function setupCategoryFilter() {
    const legendContent = document.getElementById('legend-content');

    legendContent.addEventListener('change', (event) => {
        const target = event.target;
        if (!target || target.type !== 'checkbox' || !target.dataset.category) {
            return;
        }

        const category = target.dataset.category; // już znormalizowana
        if (target.checked) {
            activeCategories.add(category);
        } else {
            activeCategories.delete(category);
        }

        if (!eventsLayer) return;

        eventsLayer.eachLayer((layer) => {
            const categories = layer.feature?.properties?.category || [];
            const primary = normalizeCategoryName(getPrimaryCategory(categories));
            const isVisible = activeCategories.has(primary);

            if (typeof layer.setOpacity === 'function') {
                layer.setOpacity(isVisible ? 1 : 0);
            }
            if (typeof layer.setInteractive === 'function') {
                layer.setInteractive(isVisible);
            }
            if (!isVisible) {
                layer.closePopup?.();
            }
        });
    });
}

// Pobieranie koloru kategorii
function getCategoryColor(categories) {
    const primaryCat = getPrimaryCategory(categories);
    const normalized = normalizeCategoryName(primaryCat);
    return categoryColors[normalized] || categoryColors['inne'];
}

// Aktualizacja legendy
function updateLegend() {
    const legendContent = document.getElementById('legend-content');
    legendContent.innerHTML = '';
    
    const sortedCategories = Array.from(usedCategories).sort();
    
    sortedCategories.forEach(category => {
        const normalized = normalizeCategoryName(category);
        const color = categoryColors[normalized] || categoryColors['inne'];

        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = `
            <div class="legend-color" style="background-color: ${color}"></div>
            <input type="checkbox" class="category-toggle" data-category="${normalized}" checked>
            <span class="legend-label">${category}</span>
        `;
        legendContent.appendChild(item);
    });
    
    if (usedCategories.size === 0) {
        legendContent.innerHTML = '<div class="legend-label" style="color: #999;">Brak wydarzeń</div>';
    }
}

// Tworzenie kolorowej ikony markera
function createColoredIcon(color) {
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="background-color: ${color}; width: 100%; height: 100%; border-radius: 50%;"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
        popupAnchor: [0, -10]
    });
}

// Tworzenie zawartości popup
function createPopupContent(properties) {
    const cats = properties.category && properties.category.length > 0
        ? `<div class="event-popup-categories">
            ${properties.category.map(cat => `<span class="event-popup-category">${cat}</span>`).join('')}
           </div>`
        : '';
    
    return `
        <div class="event-popup">
            ${properties.image ? `<img src="${properties.image}" alt="${properties.title}" class="event-popup-image">` : ''}
            <div class="event-popup-content">
                <h4>${properties.title}</h4>
                ${properties.address ? `<div class="event-popup-info"><strong>📍</strong><span>${properties.address}</span></div>` : ''}
                ${properties.district ? `<div class="event-popup-info"><strong>🏙️</strong><span>${properties.district}</span></div>` : ''}
                ${properties.date || properties.start_date ? `<div class="event-popup-info"><strong>📅</strong><span>${properties.date || properties.start_date}</span></div>` : ''}
                ${properties.time ? `<div class="event-popup-info"><strong>🕐</strong><span>${properties.time}</span></div>` : ''}
                ${cats}
                <a href="${properties.link}" target="_blank" class="event-popup-link">Zobacz więcej →</a>
            </div>
        </div>
    `;
}

// Wyświetlanie statusu
function showStatus(message, type, autoHide = 0) {
    const statusBox = document.getElementById('status-box');
    statusBox.innerHTML = message;
    statusBox.className = 'show';
    
    statusBox.style.color = type === 'error' ? '#f44336' : 
                            type === 'success' ? '#4CAF50' : 
                            type === 'warning' ? '#ff9800' : '#666';
    
    if (autoHide > 0) {
        setTimeout(() => {
            statusBox.classList.remove('show');
        }, autoHide);
    }
}

// ============================================
// ŁADOWANIE WYDARZEŃ
// ============================================

// ...existing code...

function buildEventsLayer(geojsonData) {
    const nextUsedCategories = new Set();

    const nextLayer = L.geoJSON(geojsonData, {
        pointToLayer: function(feature, latlng) {
            const primaryCategory = getPrimaryCategory(feature.properties.category);
            nextUsedCategories.add(primaryCategory);

            const color = getCategoryColor(feature.properties.category);
            return L.marker(latlng, { icon: createColoredIcon(color) });
        },
        onEachFeature: function(feature, layer) {
            const popupContent = createPopupContent(feature.properties);
            layer.bindPopup(popupContent, {
                maxWidth: 320,
                className: 'custom-popup'
            });
        }
    });

    if (eventsLayer) {
        map.removeLayer(eventsLayer);
    }
    // wtyczka
    const clusterGroup = L.markerClusterGroup();
    clusterGroup.addLayer(nextLayer)
    eventsLayer = clusterGroup.addTo(map);

    usedCategories = nextUsedCategories;

    // ✅ aktywne = znormalizowane
    activeCategories = new Set(Array.from(usedCategories).map(normalizeCategoryName));

    updateLegend();

    const eventCount = geojsonData.features.length;
    if (eventCount > 0) {
        map.fitBounds(eventsLayer.getBounds(), { padding: [50, 50] });
        showStatus(`✅ Załadowano ${eventCount} wydarzeń`, 'success', 3000);
    } else {
        showStatus('⚠️ Brak wydarzeń w tym dniu', 'warning', 3000);
    }
}


async function loadEvents() {
    const selectedDate = datePicker.selectedDates[0];

    if (!selectedDate) {
        showStatus('❌ Wybierz datę!', 'error');
        return;
    }

    const day = selectedDate.getDate();
    const month = selectedDate.getMonth() + 1;
    const year = selectedDate.getFullYear();

    showStatus('<span class="spinner"></span> Ładowanie wydarzeń...', 'loading');

    try {
        const response = await fetch(
            `${API_URL}/api/events/geojson?day=${day}&month=${month}&year=${year}`
        );

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const geojsonData = await response.json();

        localStorage.setItem('eventsDate', `${year}-${month}-${day}`);
        localStorage.setItem('eventsGeojson', JSON.stringify(geojsonData));

        buildEventsLayer(geojsonData);
    } catch (error) {
        console.error('Błąd:', error);
        showStatus(`❌ Błąd: ${error.message}`, 'error', 5000);
    }
}


// ============================================
// INICJALIZACJA DATE PICKERA
// ============================================

const datePicker = flatpickr("#date-picker", {
    dateFormat: "Y-m-d",
    defaultDate: new Date(),
    maxDate: "2026-12-31",
    minDate: "2020-01-01",
    locale: {
        firstDayOfWeek: 1,
        weekdays: {
            shorthand: ['Nd', 'Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So'],
            longhand: ['Niedziela', 'Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota']
        },
        months: {
            shorthand: ['Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze', 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru'],
            longhand: ['Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec', 'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień']
        }
    },
    onChange: function(selectedDates, dateStr, instance) {
        if (selectedDates.length > 0) {
            loadEvents();
        }
    }
});

// Event listener dla ikony kalendarza
document.getElementById('calendar-icon').addEventListener('click', () => {
    datePicker.open();
});

// ============================================
// INICJALIZACJA PRZY STARCIE
// ============================================

updateLegend();
setupCategoryFilter();

window.addEventListener('load', () => {
    const saved = localStorage.getItem('eventsGeojson');
    if (saved) {
        const geojsonData = JSON.parse(saved);
        buildEventsLayer(geojsonData);
        return;
    }
    setTimeout(loadEvents, 500);
});

function toggleAllCategories(checked) {
    const boxes = document.querySelectorAll('.category-toggle');

    activeCategories.clear();

    boxes.forEach((box) => {
        box.checked = checked;
        if (checked) {
            activeCategories.add(box.dataset.category);
        }
    });

    if (!eventsLayer) return;

    eventsLayer.eachLayer((layer) => {
        const categories = layer.feature?.properties?.category || [];
        const primary = normalizeCategoryName(getPrimaryCategory(categories));
        const isVisible = activeCategories.has(primary);

        layer.setOpacity?.(isVisible ? 1 : 0);
        layer.setInteractive?.(isVisible);
        if (!isVisible) layer.closePopup?.();
    });
}

document.getElementById('category-toggle')?.addEventListener('change', (e) => {
    toggleAllCategories(e.target.checked);
});

