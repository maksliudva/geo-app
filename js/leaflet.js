var map = L.map('map_container').setView([52.2298, 21.0118], 13);

basic_layer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
});

// Cargo Dark (free) 
dark_layer = L.tileLayer('http://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL '
});

//ESRI ArcGIS Online Street Map (free or paid) 
esri_standard_layer = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles © Esri Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom, 2012 '
});

// ESRI ArcGIS Online Imagery (free or paid) 
esri_imagery_layer = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: '© Esri Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community '
});

// geoportal_high_res_layer = L.tileLayer('https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution/{y}/{x}', {
//     maxZoom: 19,
//     attribution: '© Esri Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community '
// });

var baseMaps = {
    "OpenStreetMap":basic_layer,
    "Dark Map": dark_layer,
    "Esri Standard Map":esri_standard_layer,
    "Esri Imagery Map":esri_imagery_layer
}

var layerControl = L.control.layers(baseMaps).addTo(map)

