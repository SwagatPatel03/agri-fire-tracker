import { useRef, useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// MapTiler dark theme
const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY || 'JbpZoqzQJYnBrk9PEvYY';
const MAP_STYLE = `https://api.maptiler.com/maps/dataviz-dark/style.json?key=${MAPTILER_KEY}`;

export default function FireMap({ fires, plumes }) {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const popupRef = useRef(null);
  const [styleLoaded, setStyleLoaded] = useState(false);

  // Initialize map
  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [82, 22],   // Center of India
      zoom: 4.5,
      minZoom: 3,
      maxZoom: 15,
      attributionControl: true,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('error', (e) => {
      console.error('Map error:', e.error?.message || e.message || e);
    });

    map.on('load', () => {
      // Fire points source (empty initially)
      map.addSource('fires', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      // Plume polygons source
      map.addSource('plumes', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      // ── Plume layer (render below fires) ───────────────
      map.addLayer({
        id: 'plume-fill',
        type: 'fill',
        source: 'plumes',
        paint: {
          'fill-color': '#f59e0b',
          'fill-opacity': 0.08,
        }
      });

      map.addLayer({
        id: 'plume-outline',
        type: 'line',
        source: 'plumes',
        paint: {
          'line-color': '#f59e0b',
          'line-width': 1,
          'line-opacity': 0.25,
          'line-dasharray': [3, 2],
        }
      });

      // ── Fire glow layer (heatmap-like) ─────────────────
      map.addLayer({
        id: 'fire-glow',
        type: 'circle',
        source: 'fires',
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['get', 'magnitude'],
            0, 12,
            50, 24,
            200, 40
          ],
          'circle-color': '#f97316',
          'circle-opacity': 0.15,
          'circle-blur': 1,
        }
      });

      // ── Fire point layer ───────────────────────────────
      map.addLayer({
        id: 'fire-points',
        type: 'circle',
        source: 'fires',
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['get', 'magnitude'],
            0, 4,
            50, 7,
            200, 12
          ],
          'circle-color': [
            'interpolate', ['linear'], ['get', 'magnitude'],
            0, '#fb923c',
            50, '#f97316',
            100, '#ea580c',
            200, '#dc2626'
          ],
          'circle-stroke-color': '#fff',
          'circle-stroke-width': 0.8,
          'circle-stroke-opacity': 0.5,
        }
      });

      // ── Popup on click ─────────────────────────────────
      map.on('click', 'fire-points', (e) => {
        const f = e.features[0];
        const props = f.properties;
        const coords = e.lngLat;

        const html = `
          <div class="fire-popup-title">Fire Detection</div>
          <div class="fire-popup-row"><span>FRP</span><span>${props.magnitude} MW</span></div>
          <div class="fire-popup-row"><span>Confidence</span><span>${props.confidence || 'N/A'}</span></div>
          <div class="fire-popup-row"><span>Wind</span><span>${Number(props.wind_speed || 0).toFixed(1)} km/h</span></div>
          <div class="fire-popup-row"><span>Direction</span><span>${Number(props.wind_direction || 0).toFixed(0)}°</span></div>
          <div class="fire-popup-row"><span>District</span><span>${props.district_name || 'Unknown'}</span></div>
          <div class="fire-popup-row"><span>Detected</span><span>${new Date(props.detected_at).toLocaleString()}</span></div>
        `;

        if (popupRef.current) popupRef.current.remove();
        popupRef.current = new maplibregl.Popup({ closeButton: true, maxWidth: '260px' })
          .setLngLat(coords)
          .setHTML(html)
          .addTo(map);
      });

      // Cursor
      map.on('mouseenter', 'fire-points', () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'fire-points', () => { map.getCanvas().style.cursor = ''; });

      // Mark style as loaded so data effects can run
      setStyleLoaded(true);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update fire data — only after style is loaded
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !fires || !styleLoaded) return;

    const source = map.getSource('fires');
    if (source) source.setData(fires);
  }, [fires, styleLoaded]);

  // Update plume data — only after style is loaded
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !plumes || !styleLoaded) return;

    const source = map.getSource('plumes');
    if (source) source.setData(plumes);
  }, [plumes, styleLoaded]);

  return (
    <div className="map-container" ref={mapContainer}>
      <div className="map-legend">
        <h4>Legend</h4>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#fb923c' }} />
          <span>Low FRP (&lt;50 MW)</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#f97316' }} />
          <span>Medium FRP (50-100)</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: '#dc2626' }} />
          <span>High FRP (&gt;100 MW)</span>
        </div>
        <div className="legend-item">
          <div className="legend-swatch" style={{ background: '#f59e0b' }} />
          <span>Smoke Plume</span>
        </div>
      </div>
    </div>
  );
}
