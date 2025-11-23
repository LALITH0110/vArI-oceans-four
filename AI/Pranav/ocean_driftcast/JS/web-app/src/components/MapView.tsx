/**
 * MapView Component
 *
 * MapLibre GL map with trajectory visualization and gyre heatmap.
 */

import React, { useRef, useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import type { Map as MapLibreMap } from 'maplibre-gl';
import { Trajectory } from '../particles';
import { CityData } from '../particles';

interface MapViewProps {
  trajectory: Trajectory | null;
  currentStep: number;
  selectedCity: CityData | null;
}

export const MapView: React.FC<MapViewProps> = ({ trajectory, currentStep, selectedCity }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Create MapLibre map with dark style using free OSM tiles
    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors'
          }
        },
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: {
              'background-color': '#0a1e2e'
            }
          },
          {
            id: 'osm',
            type: 'raster',
            source: 'osm-tiles',
            paint: {
              'raster-opacity': 0.4,
              'raster-brightness-min': 0.0,
              'raster-brightness-max': 0.3,
              'raster-saturation': -0.8,
              'raster-contrast': 0.2
            }
          }
        ]
      },
      center: [-40, 35],
      zoom: 2.5,
      minZoom: 2,
      maxZoom: 10
    });

    mapInstance.on('load', () => {
      console.log('✓ MAP READY');

      // Add gyre heatmap (static concentric bands)
      addGyreHeatmap(mapInstance);

      setMapReady(true);
    });

    map.current = mapInstance;

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Add gyre heatmap layer
  const addGyreHeatmap = (mapInstance: MapLibreMap) => {
    // Create concentric circles for subtropical gyre (30N, 40W)
    const gyreCenterLon = -40;
    const gyreCenterLat = 30;
    const gyreRadii = [5, 10, 15, 20, 25, 30];

    const features = gyreRadii.map(radius => {
      const points: [number, number][] = [];
      for (let angle = 0; angle <= 360; angle += 5) {
        const rad = (angle * Math.PI) / 180;
        const lat = gyreCenterLat + radius * Math.cos(rad);
        const lon = gyreCenterLon + radius * Math.sin(rad);
        points.push([lon, lat]);
      }

      return {
        type: 'Feature' as const,
        properties: { radius },
        geometry: {
          type: 'LineString' as const,
          coordinates: points
        }
      };
    });

    mapInstance.addSource('gyre-heatmap', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features
      }
    });

    mapInstance.addLayer({
      id: 'gyre-heatmap',
      type: 'line',
      source: 'gyre-heatmap',
      paint: {
        'line-color': '#00d9ff',
        'line-width': 1,
        'line-opacity': 0.1,
        'line-blur': 2
      }
    });
  };

  // Update trajectory layer
  useEffect(() => {
    if (!map.current || !mapReady || !trajectory) return;

    // Remove existing trajectory layers
    if (map.current.getLayer('trajectory-line')) {
      map.current.removeLayer('trajectory-line');
    }
    if (map.current.getLayer('trajectory-glow')) {
      map.current.removeLayer('trajectory-glow');
    }
    if (map.current.getSource('trajectory')) {
      map.current.removeSource('trajectory');
    }

    // Get trajectory up to current step
    const visibleLats = trajectory.lats.slice(0, currentStep + 1);
    const visibleLons = trajectory.lons.slice(0, currentStep + 1);

    if (visibleLats.length < 2) return;

    const coordinates: [number, number][] = visibleLats.map((lat, i) => [visibleLons[i], lat]);

    // Add trajectory source
    map.current.addSource('trajectory', {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates
        }
      }
    });

    // Add glow layer (wider, lower opacity)
    map.current.addLayer({
      id: 'trajectory-glow',
      type: 'line',
      source: 'trajectory',
      paint: {
        'line-color': '#00d9ff',
        'line-width': 6,
        'line-opacity': 0.3,
        'line-blur': 4
      }
    });

    // Add main line layer
    map.current.addLayer({
      id: 'trajectory-line',
      type: 'line',
      source: 'trajectory',
      paint: {
        'line-color': '#00d9ff',
        'line-width': 2,
        'line-opacity': 0.9
      }
    });

    // Add endpoint marker
    if (map.current.getLayer('trajectory-endpoint')) {
      map.current.removeLayer('trajectory-endpoint');
    }
    if (map.current.getSource('trajectory-endpoint')) {
      map.current.removeSource('trajectory-endpoint');
    }

    const endLat = visibleLats[visibleLats.length - 1];
    const endLon = visibleLons[visibleLons.length - 1];

    map.current.addSource('trajectory-endpoint', {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'Point',
          coordinates: [endLon, endLat]
        }
      }
    });

    map.current.addLayer({
      id: 'trajectory-endpoint',
      type: 'circle',
      source: 'trajectory-endpoint',
      paint: {
        'circle-color': '#00d9ff',
        'circle-radius': 5,
        'circle-blur': 0.5,
        'circle-opacity': 0.9
      }
    });

  }, [trajectory, currentStep, mapReady]);

  // Add release location marker
  useEffect(() => {
    if (!map.current || !mapReady || !selectedCity) return;

    // Remove existing marker
    if (map.current.getLayer('release-marker')) {
      map.current.removeLayer('release-marker');
    }
    if (map.current.getSource('release-marker')) {
      map.current.removeSource('release-marker');
    }

    const lat = selectedCity.type === 'inland' && selectedCity.outlet
      ? selectedCity.outlet.lat
      : selectedCity.lat;
    const lon = selectedCity.type === 'inland' && selectedCity.outlet
      ? selectedCity.outlet.lon
      : selectedCity.lon;

    map.current.addSource('release-marker', {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'Point',
          coordinates: [lon, lat]
        }
      }
    });

    map.current.addLayer({
      id: 'release-marker',
      type: 'circle',
      source: 'release-marker',
      paint: {
        'circle-color': '#ff6b6b',
        'circle-radius': 6,
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 2,
        'circle-opacity': 0.9
      }
    });

  }, [selectedCity, mapReady]);

  return (
    <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
  );
};
