document.addEventListener('DOMContentLoaded', function initMap(token) {
    mapboxgl.accessToken = token;

    var map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [15.056533668324306, 50.76717120027155], // výchozí pozice
        zoom: 10
    });

    // Přidání bodu na mapu
    var marker = new mapboxgl.Marker().setLngLat([15.085348864337016, 50.77048642703595]).addTo(map);

    // Odstranění bodu z mapy po 3 sekundách
    setTimeout(function () {
        marker.remove();
    }, 5000);
});
