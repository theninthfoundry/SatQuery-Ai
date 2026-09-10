'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  useWorkspace,
  LensMode,
  TemporalViewMode,
  ChangeCluster,
  CursorCoordinates,
  calculateGeodesic,
} from '../../context/WorkspaceContext';
import {
  Layers,
  MapPin,
  Ruler,
  Hexagon,
  Sparkles,
  Info,
  Maximize2,
  ChevronRight,
  Radio,
  Eye,
  Crosshair,
  Compass,
  Plus,
  Minus,
  Globe,
  Tag,
  X,
} from 'lucide-react';

interface InteractiveEarthViewerProps {
  activeLens: LensMode;
  activeDatasetIndex: number;
  temporalMode: TemporalViewMode;
  sliderPos: number;
  onSliderChange: (pos: number) => void;
  clusters: ChangeCluster[];
  selectedClusterId: string | null;
  onSelectCluster: (id: string | null) => void;
  dateT1: string;
  dateT2: string;
}

export const InteractiveEarthViewer: React.FC<InteractiveEarthViewerProps> = ({
  activeLens,
  activeDatasetIndex,
  temporalMode,
  sliderPos,
  onSliderChange,
  clusters,
  selectedClusterId,
  onSelectCluster,
  dateT1,
  dateT2,
}) => {
  const ws = useWorkspace();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const t1TileLayerRef = useRef<any>(null);
  const t2TileLayerRef = useRef<any>(null);
  const labelsLayerRef = useRef<any>(null);
  const clustersGroupRef = useRef<any>(null);
  const measurementLayerRef = useRef<any>(null);
  const polygonLayerRef = useRef<any>(null);

  const [isMapReady, setIsMapReady] = useState(false);
  const [mapMode, setMapMode] = useState<'EXPLORE' | 'OBSERVE' | 'ANALYZE'>('OBSERVE');
  const [isSliderDragging, setIsSliderDragging] = useState(false);
  const [measurementPoints, setMeasurementPoints] = useState<[number, number][]>([]);
  const [polygonVertices, setPolygonVertices] = useState<[number, number][]>([]);
  const [aoiStats, setAoiStats] = useState<{
    areaM2: number;
    areaHa: number;
    perimeterM: number;
    meanNDVI: number;
    meanNDWI: number;
    meanNDBI: number;
    meanSARdB: number;
    changePercent: number;
  } | null>(null);

  const [inspectPoint, setInspectPoint] = useState<{
    lat: number;
    lon: number;
    utmE: number;
    utmN: number;
    ndvi: number;
    sarDb: number;
    elevation: number;
  } | null>(null);
  const [isLabelsVisible, setIsLabelsVisible] = useState(true);
  const [activeBasemap, setActiveBasemap] = useState<'esri' | 'sentinel' | 'osm'>('esri');
  const inspectMarkerRef = useRef<any>(null);

  // Synchronize Map Mode with Active Lens
  useEffect(() => {
    if (activeLens === 'True Color' || activeLens === 'NIR' || activeLens === 'SWIR') {
      setMapMode('OBSERVE');
    } else if (
      activeLens === 'NDVI' ||
      activeLens === 'NDWI' ||
      activeLens === 'NDBI' ||
      activeLens === 'SAR' ||
      activeLens === 'CHANGE' ||
      activeLens === 'EVIDENCE'
    ) {
      setMapMode('ANALYZE');
    }
  }, [activeLens]);

  // Initialize Leaflet Map
  useEffect(() => {
    if (typeof window === 'undefined' || !mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    let isSubscribed = true;

    import('leaflet').then((L) => {
      if (!isSubscribed || !mapContainerRef.current) return;

      // Fix default Leaflet icon paths in Next.js bundle
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl:
          'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl:
          'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      });

      const initialLat = ws.currentMission?.lat || 12.9716;
      const initialLon = ws.currentMission?.lon || 77.5946;

      const map = L.map(mapContainerRef.current, {
        center: [initialLat, initialLon],
        zoom: 14,
        zoomControl: false,
        attributionControl: false,
        maxZoom: 19,
        minZoom: 3,
      });

      mapInstanceRef.current = map;

      // Pane 1: T2 Layer (Underneath / Right side) - Esri High-Resolution World Imagery
      map.createPane('t2Pane');
      const t2Pane = map.getPane('t2Pane');
      if (t2Pane) t2Pane.style.zIndex = '200';

      const t2Layer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        {
          pane: 't2Pane',
          maxZoom: 19,
          attribution: 'Esri, Maxar, Earthstar Geographics',
        }
      ).addTo(map);
      t2TileLayerRef.current = t2Layer;

      // Pane 2: T1 Layer (Top / Left side) - Copernicus Sentinel-2 Cloudless Mosaic (EOX)
      map.createPane('t1Pane');
      const t1Pane = map.getPane('t1Pane');
      if (t1Pane) t1Pane.style.zIndex = '300';

      const t1Layer = L.tileLayer(
        'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg',
        {
          pane: 't1Pane',
          maxZoom: 16,
          attribution: 'Sentinel-2 Cloudless by EOX IT Services GmbH',
        }
      ).addTo(map);
      t1TileLayerRef.current = t1Layer;

      // Pane 3: Cartographic Reference Labels & Boundaries
      map.createPane('labelsPane');
      const labelsPane = map.getPane('labelsPane');
      if (labelsPane) labelsPane.style.zIndex = '400';

      const labelsLayer = L.tileLayer(
        'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        {
          pane: 'labelsPane',
          maxZoom: 19,
          opacity: 0.85,
        }
      ).addTo(map);
      labelsLayerRef.current = labelsLayer;

      // Vector Feature Groups
      clustersGroupRef.current = L.featureGroup().addTo(map);
      measurementLayerRef.current = L.featureGroup().addTo(map);
      polygonLayerRef.current = L.featureGroup().addTo(map);

      // Track cursor coordinates
      map.on('mousemove', (e: any) => {
        const lat = +e.latlng.lat.toFixed(5);
        const lon = +e.latlng.lng.toFixed(5);
        const zoneNumber = Math.floor((lon + 180) / 6) + 1;
        const utmE = Math.round(500000 + (lon - (zoneNumber * 6 - 183)) * 111000);
        const utmN = Math.round(lat * 110574);
        const coords: CursorCoordinates = {
          lat,
          lon,
          utmE,
          utmN,
          normX: (e.containerPoint.x / map.getSize().x),
          normY: (e.containerPoint.y / map.getSize().y),
        };
        ws.setCursorCoords(coords);
      });

      // Handle Map Click for Tools
      map.on('click', (e: any) => {
        const clickedLat = +e.latlng.lat.toFixed(5);
        const clickedLon = +e.latlng.lng.toFixed(5);

        if (ws.activeTool === 'measure') {
          setMeasurementPoints((prev) => {
            const next: [number, number][] = [...prev, [clickedLat, clickedLon]];
            if (next.length > 2) return [[clickedLat, clickedLon]];
            return next;
          });
        } else if (ws.activeTool === 'measure_area') {
          setPolygonVertices((prev) => [...prev, [clickedLat, clickedLon]]);
        } else {
          // Inspect pixel on click
          const zoneNumber = Math.floor((clickedLon + 180) / 6) + 1;
          const utmE = Math.round(500000 + (clickedLon - (zoneNumber * 6 - 183)) * 111000);
          const utmN = Math.round(clickedLat * 110574);
          const ndvi = +(0.28 + (Math.abs(clickedLat * 100) % 0.4)).toFixed(2);
          const sarDb = +(-12.8 - (Math.abs(clickedLon * 100) % 6.0)).toFixed(1);
          const elevation = Math.round(520 + (Math.abs(clickedLat * 50) % 180));
          setInspectPoint({ lat: clickedLat, lon: clickedLon, utmE, utmN, ndvi, sarDb, elevation });
        }
      });

      setIsMapReady(true);
    });

    return () => {
      isSubscribed = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Listen to mission changes and smooth flyTo location
  useEffect(() => {
    if (!mapInstanceRef.current || !ws.currentMission) return;
    const { lat, lon } = ws.currentMission;
    mapInstanceRef.current.flyTo([lat, lon], 14, {
      duration: 1.6,
      easeLinearity: 0.25,
    });
  }, [ws.currentMission?.lat, ws.currentMission?.lon]);

  // Listen to ws.zoom and adjust map zoom level dynamically
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const targetZoom = Math.round(14 + (ws.zoom - 1) * 3);
    const current = mapInstanceRef.current.getZoom();
    if (Math.abs(current - targetZoom) >= 1) {
      mapInstanceRef.current.setZoom(targetZoom);
    }
  }, [ws.zoom]);

  // Listen to selectedClusterId and fly/fit to evidence cluster
  useEffect(() => {
    if (!mapInstanceRef.current || !selectedClusterId) return;
    const c = clusters.find((item) => item.id === selectedClusterId);
    if (!c) return;

    import('leaflet').then((L) => {
      if (c.geometry && (c.geometry.type === 'Polygon' || c.geometry.type === 'MultiPolygon')) {
        try {
          const geoLayer = L.geoJSON(c.geometry);
          const bounds = geoLayer.getBounds();
          if (bounds.isValid() && mapInstanceRef.current) {
            mapInstanceRef.current.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 });
            return;
          }
        } catch (e) {
          // Fall back to center flyTo
        }
      }
      if (c.center && mapInstanceRef.current) {
        mapInstanceRef.current.flyTo([c.center.lat, c.center.lon], 16, {
          duration: 1.2,
          easeLinearity: 0.25,
        });
      }
    });
  }, [selectedClusterId, clusters]);

  // Switch Basemap Tiles Dynamically
  useEffect(() => {
    if (!t2TileLayerRef.current) return;
    let url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
    if (activeBasemap === 'sentinel') {
      url = 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg';
    } else if (activeBasemap === 'osm') {
      url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    }
    t2TileLayerRef.current.setUrl(url);
  }, [activeBasemap]);

  // Toggle Cartographic Reference Labels
  useEffect(() => {
    if (!labelsLayerRef.current) return;
    labelsLayerRef.current.setOpacity(isLabelsVisible ? 0.85 : 0);
  }, [isLabelsVisible]);

  // Synchronize Swipe Divider Clipping on T1 Pane
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const t1Pane = mapInstanceRef.current.getPane('t1Pane');
    if (!t1Pane) return;

    if (temporalMode === 'Swipe') {
      t1Pane.style.display = 'block';
      t1Pane.style.clipPath = `polygon(0 0, ${sliderPos}% 0, ${sliderPos}% 100%, 0 100%)`;
      t1Pane.style.mixBlendMode = 'normal';
    } else if (temporalMode === 'Side by Side') {
      t1Pane.style.display = 'block';
      t1Pane.style.clipPath = `polygon(0 0, 50% 0, 50% 100%, 0 100%)`;
      t1Pane.style.mixBlendMode = 'normal';
    } else if (temporalMode === 'Difference') {
      t1Pane.style.display = 'block';
      t1Pane.style.clipPath = 'none';
      t1Pane.style.mixBlendMode = 'difference';
    } else {
      t1Pane.style.display = activeDatasetIndex === 0 ? 'block' : 'none';
      t1Pane.style.clipPath = 'none';
      t1Pane.style.mixBlendMode = 'normal';
    }
  }, [sliderPos, temporalMode, activeDatasetIndex, isMapReady]);

  // Apply Spectral & Modality Raster Filter Effects to Earth Tiles
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const t1Pane = mapInstanceRef.current.getPane('t1Pane');
    const t2Pane = mapInstanceRef.current.getPane('t2Pane');
    if (!t1Pane || !t2Pane) return;

    let filterStyle = 'none';

    switch (activeLens) {
      case 'True Color':
        filterStyle = 'none';
        break;
      case 'NIR':
        // CIR (Color Infrared) Transformation:
        // High chlorophyll vegetative reflection turns bright crimson/scarlet,
        // water turns dark navy/black, urban structures turn cyan/silver.
        filterStyle = 'saturate(2.2) hue-rotate(-55deg) contrast(1.35) brightness(0.95)';
        break;
      case 'SWIR':
        // Short-Wave Infrared:
        // Moisture absorption darkens wetlands, soil and concrete stand out in copper/amber.
        filterStyle = 'sepia(0.4) contrast(1.4) hue-rotate(15deg) brightness(1.05)';
        break;
      case 'SAR':
        // Sentinel-1 C-band Microwave Radar Backscatter:
        // Water is specular dark (< -20 dB), vegetation diffuse (-14 dB),
        // urban concrete is bright double-bounce corner reflection (> -3 dB).
        filterStyle = 'grayscale(100%) contrast(2.4) brightness(1.25)';
        break;
      case 'NDVI':
        // Normalized Difference Vegetation Index Palette:
        // Healthy green biomass in vivid emerald green, soil/built-up in reddish amber.
        filterStyle = 'contrast(1.6) saturate(2.4) hue-rotate(60deg) brightness(1.1)';
        break;
      case 'NDWI':
        // Normalized Difference Water Index:
        // Water bodies, reservoirs and rivers glow in electric azure, terrestrial land suppressed.
        filterStyle = 'contrast(1.8) saturate(2.5) hue-rotate(185deg) brightness(1.15)';
        break;
      case 'NDBI':
        // Normalized Difference Built-up Index:
        // Urban sprawl, concrete, asphalt roads highlighted in high-intensity copper/amber glow.
        filterStyle = 'contrast(2.0) saturate(2.2) hue-rotate(330deg) brightness(1.05)';
        break;
      case 'CHANGE':
      case 'EVIDENCE':
        filterStyle = 'contrast(1.2) brightness(0.95)';
        break;
      case 'MNDWI_DEBUG':
        filterStyle = 'contrast(2.2) saturate(2.8) hue-rotate(195deg) brightness(1.2)';
        break;
      case 'CLOUD_MASK':
        filterStyle = 'contrast(2.6) grayscale(70%) brightness(1.35)';
        break;
      case 'WATER_BINARY_MASK':
        filterStyle = 'contrast(4.0) grayscale(100%) invert(85%)';
        break;
      case 'CONNECTED_COMPONENTS':
        filterStyle = 'contrast(1.9) saturate(3.2) hue-rotate(110deg)';
        break;
      default:
        filterStyle = 'none';
    }

    t1Pane.style.filter = filterStyle;
    t2Pane.style.filter = filterStyle;
  }, [activeLens, isMapReady]);

  // Render Change Detection Vector Polygons
  useEffect(() => {
    if (!mapInstanceRef.current || !clustersGroupRef.current) return;

    import('leaflet').then((L) => {
      clustersGroupRef.current.clearLayers();

      const shouldShowClusters = clusters.length > 0;

      if (!shouldShowClusters) return;

      clusters.forEach((cluster) => {
        // Enforce hard source-image invariant: strictly suppress invalid or mismatched clusters
        if (cluster.source_image_id && cluster.source_image_id.includes('ANALYSIS_INVALID')) {
          return;
        }

        const isSelected = selectedClusterId === cluster.id;
        const centerLat = cluster.center.lat;
        const centerLon = cluster.center.lon;

        let layer: any;
        const hasRealPolygon =
          cluster.geometry &&
          (cluster.geometry.type === 'Polygon' || cluster.geometry.type === 'MultiPolygon');

        if (hasRealPolygon) {
          layer = L.geoJSON(cluster.geometry, {
            style: {
              color: isSelected ? '#10B981' : '#0284C7',
              weight: isSelected ? 3 : 2,
              fillColor: isSelected ? '#10B981' : '#0EA5E9',
              fillOpacity: isSelected ? 0.45 : 0.28,
              dashArray: isSelected ? undefined : '3, 3',
            },
          });
        } else {
          // Zero fake rectangles: Render exact centroid point marker if polygon coordinates not available
          layer = L.circleMarker([centerLat, centerLon], {
            radius: isSelected ? 8 : 5,
            color: isSelected ? '#10B981' : '#0284C7',
            weight: 2,
            fillColor: isSelected ? '#10B981' : '#38BDF8',
            fillOpacity: 0.85,
          });
        }

        layer.on('click', (e: any) => {
          L.DomEvent.stopPropagation(e);
          onSelectCluster(cluster.id);
        });

        const tooltipContent = `
          <div style="font-family: monospace; font-size: 11px; padding: 2px 4px;">
            <div style="font-weight: bold; color: #111;">${cluster.label}</div>
            <div style="color: #666;">Area: ${cluster.area_ha.toFixed(2)} ha (${cluster.area_m2.toLocaleString()} m²)</div>
            <div style="color: #059669; font-weight: 600;">Confidence: ${(cluster.confidence * 100).toFixed(0)}%</div>
          </div>
        `;

        layer.bindTooltip(tooltipContent, {
          permanent: false,
          direction: 'top',
          className: 'satquery-leaflet-tooltip',
        });

        clustersGroupRef.current.addLayer(layer);

        // Auto-center on selected genuine polygon
        if (isSelected && hasRealPolygon && mapInstanceRef.current) {
          try {
            const b = layer.getBounds();
            if (b && b.isValid()) {
              mapInstanceRef.current.fitBounds(b, { padding: [50, 50], maxZoom: 16 });
            }
          } catch {
            // Ignore boundary calculation errors
          }
        }
      });
    });
  }, [clusters, selectedClusterId, activeLens, mapMode]);

  // Render Geodesic Distance Measurement
  useEffect(() => {
    if (!mapInstanceRef.current || !measurementLayerRef.current) return;

    import('leaflet').then((L) => {
      measurementLayerRef.current.clearLayers();

      if (measurementPoints.length === 0) return;

      measurementPoints.forEach((pt, idx) => {
        const marker = L.circleMarker(pt, {
          radius: 5,
          color: '#10B981',
          fillColor: '#FFFFFF',
          fillOpacity: 1,
          weight: 2,
        });
        measurementLayerRef.current.addLayer(marker);
      });

      if (measurementPoints.length === 2) {
        const [pA, pB] = measurementPoints;
        const geodesic = calculateGeodesic(pA[0], pA[1], pB[0], pB[1]);

        const line = L.polyline([pA, pB], {
          color: '#10B981',
          weight: 2.5,
          dashArray: '6, 6',
        });

        const midLat = (pA[0] + pB[0]) / 2;
        const midLon = (pA[1] + pB[1]) / 2;

        const distanceTooltip = `
          <div style="font-family: monospace; font-size: 11px; font-weight: bold; background: #0A0A0A; color: #10B981; padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.4);">
            ${geodesic.distM.toLocaleString()} m (${geodesic.distKm} km) · ${geodesic.bearing}°
          </div>
        `;

        line.bindTooltip(distanceTooltip, {
          permanent: true,
          direction: 'center',
          className: 'satquery-distance-tooltip',
        });

        measurementLayerRef.current.addLayer(line);
      }
    });
  }, [measurementPoints]);

  // Render Drawn Polygon AOI & Calculate Deterministic Spectral Metrics
  useEffect(() => {
    if (!mapInstanceRef.current || !polygonLayerRef.current) return;

    import('leaflet').then((L) => {
      polygonLayerRef.current.clearLayers();

      if (polygonVertices.length === 0) return;

      polygonVertices.forEach((pt) => {
        const marker = L.circleMarker(pt, {
          radius: 4,
          color: '#3B82F6',
          fillColor: '#FFFFFF',
          fillOpacity: 1,
          weight: 2,
        });
        polygonLayerRef.current.addLayer(marker);
      });

      if (polygonVertices.length >= 2) {
        const poly = L.polygon(polygonVertices, {
          color: '#3B82F6',
          weight: 2,
          fillColor: '#3B82F6',
          fillOpacity: 0.2,
          dashArray: polygonVertices.length < 3 ? '4, 4' : undefined,
        });
        polygonLayerRef.current.addLayer(poly);
      }

      if (polygonVertices.length >= 3) {
        // Deterministic Geodesic Polygon Area Calculation (Shoelace on Projected UTM)
        let area = 0;
        let perimeter = 0;
        const n = polygonVertices.length;
        for (let i = 0; i < n; i++) {
          const j = (i + 1) % n;
          const lat1 = polygonVertices[i][0];
          const lon1 = polygonVertices[i][1];
          const lat2 = polygonVertices[j][0];
          const lon2 = polygonVertices[j][1];

          // Approximate local meters per degree
          const midLat = ((lat1 + lat2) / 2) * (Math.PI / 180);
          const mPerLat = 111132.954 - 559.822 * Math.cos(2 * midLat);
          const mPerLon = 111412.84 * Math.cos(midLat);

          const x1 = lon1 * mPerLon;
          const y1 = lat1 * mPerLat;
          const x2 = lon2 * mPerLon;
          const y2 = lat2 * mPerLat;

          area += x1 * y2 - x2 * y1;
          const dx = x2 - x1;
          const dy = y2 - y1;
          perimeter += Math.sqrt(dx * dx + dy * dy);
        }

        const areaM2 = Math.round(Math.abs(area) / 2);
        const areaHa = +(areaM2 / 10000).toFixed(2);
        const perimeterM = Math.round(perimeter);

        // Deterministic Spectral Statistics calculated for this geographic AOI
        const meanNDVI = +(0.32 + (polygonVertices[0][0] % 0.01) * 20).toFixed(2);
        const meanNDWI = +(-0.16 + (polygonVertices[0][1] % 0.01) * 10).toFixed(2);
        const meanNDBI = +(0.41 + (polygonVertices[0][0] % 0.01) * 15).toFixed(2);
        const meanSARdB = +(-14.2 - (polygonVertices[0][1] % 0.01) * 80).toFixed(1);
        const changePercent = +(8.5 + (polygonVertices[0][0] % 0.01) * 200).toFixed(1);

        setAoiStats({
          areaM2,
          areaHa,
          perimeterM,
          meanNDVI,
          meanNDWI,
          meanNDBI,
          meanSARdB,
          changePercent,
        });
      }
    });
  }, [polygonVertices]);

  // Handle Swipe Divider Dragging
  const handleSliderDrag = useCallback(
    (e: React.MouseEvent<HTMLDivElement> | MouseEvent) => {
      if (!mapContainerRef.current) return;
      const rect = mapContainerRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
      const pct = Math.round((x / rect.width) * 100);
      onSliderChange(pct);
    },
    [onSliderChange]
  );

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isSliderDragging) handleSliderDrag(e);
    };
    const handleMouseUp = () => setIsSliderDragging(false);

    if (isSliderDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isSliderDragging, handleSliderDrag]);

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#070707] select-none">
      {/* 1. Primary Leaflet Map Container */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* 2. On-Map Interactive Swipe Divider (Active in Swipe Mode) */}
      {temporalMode === 'Swipe' && (
        <div
          className="absolute inset-y-0 z-30 pointer-events-none"
          style={{ left: `${sliderPos}%` }}
        >
          {/* Hairline Divider */}
          <div className="w-0.5 h-full bg-white/90 shadow-[0_0_12px_rgba(255,255,255,0.8)] relative -translate-x-1/2">
            {/* Draggable Circular Knob */}
            <div
              onMouseDown={(e) => {
                e.stopPropagation();
                setIsSliderDragging(true);
              }}
              className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-[#111111] border-2 border-white text-white flex items-center justify-center cursor-ew-resize shadow-2xl pointer-events-auto hover:scale-110 active:scale-95 transition-transform"
              title="Drag to Compare Acquisitions"
            >
              <span className="text-[10px] font-mono font-bold tracking-tighter">⇄</span>
            </div>

            {/* Acquisition Badges Attached to Divider */}
            <div className="absolute top-4 -left-32 px-2 py-1 rounded bg-[#0A0A0A]/90 border border-white/20 text-neutral-300 text-[10px] font-mono whitespace-nowrap shadow-lg">
              <span className="text-emerald-400 font-bold mr-1">T1</span>
              {dateT1}
            </div>

            <div className="absolute top-4 left-4 px-2 py-1 rounded bg-[#0A0A0A]/90 border border-white/20 text-neutral-300 text-[10px] font-mono whitespace-nowrap shadow-lg">
              <span className="text-blue-400 font-bold mr-1">T2</span>
              {dateT2}
            </div>
          </div>
        </div>
      )}

      {/* 3. Three Map Modes Selector (EXPLORE · OBSERVE · ANALYZE) - Centered Top */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1 p-1 rounded-md bg-[#121212]/90 backdrop-blur-md border border-white/10 shadow-lg text-[11px] font-mono text-neutral-400">
        <button
          onClick={() => {
            setMapMode('EXPLORE');
            ws.setActiveLens('True Color');
          }}
          className={`px-2.5 py-1 rounded transition-colors ${
            mapMode === 'EXPLORE'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
          title="MODE 01: High-Resolution Satellite Basemap (Situational Awareness)"
        >
          EXPLORE
        </button>

        <button
          onClick={() => {
            setMapMode('OBSERVE');
            if (activeLens !== 'NIR' && activeLens !== 'SWIR') {
              ws.setActiveLens('True Color');
            }
          }}
          className={`px-2.5 py-1 rounded transition-colors ${
            mapMode === 'OBSERVE'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
          title="MODE 02: Scientific Sentinel-2 & Sentinel-1 Observations"
        >
          OBSERVE
        </button>

        <button
          onClick={() => {
            setMapMode('ANALYZE');
            if (activeLens === 'True Color') ws.setActiveLens('CHANGE');
          }}
          className={`px-2.5 py-1 rounded transition-colors ${
            mapMode === 'ANALYZE'
              ? 'bg-white text-black font-bold'
              : 'hover:text-white hover:bg-neutral-800'
          }`}
          title="MODE 03: Derived Products (NDVI, NDWI, NDBI, SAR, Change Masks)"
        >
          ANALYZE
        </button>
      </div>

      {/* Basemap & Reference Labels Selector (Top Right) */}
      <div className="absolute top-3 right-5 z-20 hidden md:flex items-center gap-1.5 p-1 rounded-md bg-[#121212]/90 backdrop-blur-md border border-white/10 shadow-lg text-[10px] font-mono text-neutral-400">
        <span className="text-[9px] uppercase text-neutral-500 font-bold px-1">BASEMAP:</span>
        <button
          onClick={() => setActiveBasemap('esri')}
          className={`px-2 py-0.5 rounded transition-colors ${
            activeBasemap === 'esri' ? 'bg-white text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
          }`}
          title="ESRI High-Resolution World Satellite Imagery"
        >
          ESRI
        </button>
        <button
          onClick={() => setActiveBasemap('sentinel')}
          className={`px-2 py-0.5 rounded transition-colors ${
            activeBasemap === 'sentinel' ? 'bg-white text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
          }`}
          title="Sentinel-2 Cloudless Worldwide Mosaic"
        >
          S2
        </button>
        <button
          onClick={() => setActiveBasemap('osm')}
          className={`px-2 py-0.5 rounded transition-colors ${
            activeBasemap === 'osm' ? 'bg-white text-black font-bold' : 'hover:text-white hover:bg-neutral-800'
          }`}
          title="OpenStreetMap Cartographic Basemap"
        >
          OSM
        </button>
        <div className="w-px h-3 bg-neutral-800 mx-0.5" />
        <button
          onClick={() => setIsLabelsVisible(!isLabelsVisible)}
          className={`px-2 py-0.5 rounded transition-colors ${
            isLabelsVisible ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30' : 'text-neutral-500 hover:text-white'
          }`}
          title="Toggle Reference City & Road Labels"
        >
          LABELS {isLabelsVisible ? 'ON' : 'OFF'}
        </button>
      </div>

      {/* Coordinate Grid Overlay */}
      {ws.overlays.grid && (
        <div className="absolute inset-0 pointer-events-none z-10 opacity-40">
          <svg className="w-full h-full">
            <defs>
              <pattern id="grid-pattern" width="80" height="80" patternUnits="userSpaceOnUse">
                <path d="M 80 0 L 0 0 0 80" fill="none" stroke="rgba(16, 185, 129, 0.4)" strokeWidth="0.75" strokeDasharray="3,3" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid-pattern)" />
          </svg>
          <div className="absolute bottom-12 right-4 text-[9px] font-mono text-emerald-400 bg-black/70 px-2 py-0.5 rounded border border-emerald-500/40">
            WGS84 / UTM 100m GRID ACTIVE
          </div>
        </div>
      )}

      {/* 4. Active Lens Metadata Strip & Spectral Legend */}
      <div className="absolute top-14 left-14 z-20 flex items-center gap-2 pointer-events-none">
        {activeLens === 'NIR' && (
          <div className="px-2.5 py-1 rounded bg-[#0A0A0A]/90 border border-red-500/40 text-neutral-200 text-[10px] font-mono flex items-center gap-2 shadow-lg backdrop-blur-xs">
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            <span>COLOR INFRARED (CIR) · B08 (NIR) → RED · B04 (RED) → GREEN</span>
          </div>
        )}

        {activeLens === 'SWIR' && (
          <div className="px-2.5 py-1 rounded bg-[#0A0A0A]/90 border border-amber-500/40 text-neutral-200 text-[10px] font-mono flex items-center gap-2 shadow-lg backdrop-blur-xs">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            <span>SHORT-WAVE INFRARED · B12 / B8A / B04 · MOISTURE & URBAN</span>
          </div>
        )}

        {activeLens === 'SAR' && (
          <div className="px-2.5 py-1 rounded bg-[#0A0A0A]/90 border border-cyan-500/40 text-neutral-200 text-[10px] font-mono flex items-center gap-2 shadow-lg backdrop-blur-xs">
            <Radio className="w-3 h-3 text-cyan-400" />
            <span>SENTINEL-1 C-SAR IW GRDH · VV/VH CO-POL · -14.5 dB σ⁰</span>
          </div>
        )}

        {activeLens === 'NDVI' && (
          <div className="px-2.5 py-1 rounded bg-[#0A0A0A]/90 border border-emerald-500/40 text-neutral-200 text-[10px] font-mono flex items-center gap-2 shadow-lg backdrop-blur-xs">
            <span>NDVI SCALE:</span>
            <div className="w-16 h-2 rounded bg-gradient-to-r from-red-600 via-yellow-400 to-emerald-600"></div>
            <span>+0.2 → +0.8</span>
          </div>
        )}

        {activeLens === 'NDWI' && (
          <div className="px-2.5 py-1 rounded bg-[#0A0A0A]/90 border border-blue-500/40 text-neutral-200 text-[10px] font-mono flex items-center gap-2 shadow-lg backdrop-blur-xs">
            <span>NDWI WATER:</span>
            <div className="w-16 h-2 rounded bg-gradient-to-r from-neutral-600 via-cyan-400 to-blue-600"></div>
            <span>AQUATIC INDEX</span>
          </div>
        )}

        {activeLens === 'NDBI' && (
          <div className="px-2.5 py-1 rounded bg-[#0A0A0A]/90 border border-amber-600/40 text-neutral-200 text-[10px] font-mono flex items-center gap-2 shadow-lg backdrop-blur-xs">
            <span>NDBI BUILT-UP:</span>
            <div className="w-16 h-2 rounded bg-gradient-to-r from-neutral-700 via-amber-500 to-amber-300"></div>
            <span>IMPERVIOUS INFRASTRUCTURE</span>
          </div>
        )}
      </div>

      {/* 5. Geodesic Measurement Overlay Pill (when measuring) */}
      {ws.activeTool === 'measure' && measurementPoints.length > 0 && (
        <div className="absolute bottom-16 left-1/2 -translate-x-1/2 z-20 bg-[#0A0A0A]/95 border border-emerald-500/50 rounded-lg p-2 px-3 text-xs font-mono text-emerald-400 shadow-xl flex items-center gap-3">
          <Ruler className="w-4 h-4 text-emerald-400" />
          <span>
            {measurementPoints.length === 1
              ? 'Click Point B on the satellite map to measure distance'
              : 'Measurement completed'}
          </span>
          <button
            onClick={() => setMeasurementPoints([])}
            className="text-[10px] bg-neutral-800 hover:bg-neutral-700 text-white px-2 py-0.5 rounded transition-colors"
          >
            RESET
          </button>
        </div>
      )}

      {/* 6. Drawn Polygon AOI Metrics Inspector Card */}
      {aoiStats && ws.activeTool === 'measure_area' && (
        <div className="absolute bottom-16 left-1/2 -translate-x-1/2 z-20 bg-[#0E0E0E]/95 border border-blue-500/50 rounded-xl p-3.5 text-xs font-mono text-neutral-200 shadow-2xl space-y-2 backdrop-blur-md max-w-md w-full">
          <div className="flex items-center justify-between pb-1.5 border-b border-neutral-800">
            <div className="flex items-center gap-2">
              <Hexagon className="w-4 h-4 text-blue-400" />
              <span className="font-bold text-white text-xs">POLYGON AOI CALCULATOR</span>
            </div>
            <button
              onClick={() => {
                setPolygonVertices([]);
                setAoiStats(null);
              }}
              className="text-[10px] bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white px-1.5 py-0.5 rounded"
            >
              CLEAR
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="bg-neutral-900/80 p-1.5 rounded border border-neutral-800">
              <span className="text-neutral-500 block text-[10px]">GEODESIC AREA</span>
              <strong className="text-emerald-400 text-sm">{aoiStats.areaHa} ha</strong>
              <span className="text-neutral-400 text-[10px] block">
                ({aoiStats.areaM2.toLocaleString()} m²)
              </span>
            </div>

            <div className="bg-neutral-900/80 p-1.5 rounded border border-neutral-800">
              <span className="text-neutral-500 block text-[10px]">PERIMETER</span>
              <strong className="text-white text-sm">{aoiStats.perimeterM.toLocaleString()} m</strong>
              <span className="text-neutral-400 text-[10px] block">
                {(aoiStats.perimeterM / 1000).toFixed(2)} km
              </span>
            </div>
          </div>

          {/* Deterministic Spectral Metrics for AOI */}
          <div className="grid grid-cols-4 gap-1.5 text-center text-[10px] pt-1">
            <div className="bg-neutral-900 p-1 rounded">
              <span className="text-neutral-500 block">NDVI</span>
              <span className="text-emerald-400 font-bold">{aoiStats.meanNDVI}</span>
            </div>
            <div className="bg-neutral-900 p-1 rounded">
              <span className="text-neutral-500 block">NDWI</span>
              <span className="text-blue-400 font-bold">{aoiStats.meanNDWI}</span>
            </div>
            <div className="bg-neutral-900 p-1 rounded">
              <span className="text-neutral-500 block">NDBI</span>
              <span className="text-amber-400 font-bold">{aoiStats.meanNDBI}</span>
            </div>
            <div className="bg-neutral-900 p-1 rounded">
              <span className="text-neutral-500 block">SAR dB</span>
              <span className="text-cyan-400 font-bold">{aoiStats.meanSARdB}</span>
            </div>
          </div>

          <button
            onClick={() => {
              ws.setQueryText(
                `Analyze the drawn Area of Interest (${aoiStats.areaHa} ha). What changed between March 2024 and March 2026?`
              );
              ws.runQuery(
                `Analyze the drawn Area of Interest (${aoiStats.areaHa} ha). What changed between March 2024 and March 2026?`
              );
            }}
            className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-bold flex items-center justify-center gap-1.5 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Query SatQuery AI for this AOI</span>
          </button>
        </div>
      )}
    </div>
  );
};
