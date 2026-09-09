import { CustomAOI } from '../types/aoi';

const EARTH_RADIUS_M = 6371008.8; // WGS84 mean radius

/**
 * Calculates geodesic area of a spherical polygon using Girard's theorem / spherical excess formula.
 * Coordinates are array of [lon, lat] in degrees.
 */
export function calculateGeodesicPolygonArea(coords: [number, number][]): number {
  if (!coords || coords.length < 3) return 0;

  // Ensure ring is closed
  const points = [...coords];
  const first = points[0];
  const last = points[points.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    points.push([first[0], first[1]]);
  }

  const toRad = (deg: number) => (deg * Math.PI) / 180;
  let totalArea = 0;

  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];

    const lambda1 = toRad(p1[0]);
    const phi1 = toRad(p1[1]);
    const lambda2 = toRad(p2[0]);
    const phi2 = toRad(p2[1]);

    // Spherical trapezoid integration
    totalArea += (lambda2 - lambda1) * (2 + Math.sin(phi1) + Math.sin(phi2));
  }

  totalArea = (Math.abs(totalArea) * EARTH_RADIUS_M * EARTH_RADIUS_M) / 2.0;
  return Math.round(totalArea);
}

/**
 * Calculates geodesic perimeter of a polygon in meters.
 */
export function calculateGeodesicPerimeter(coords: [number, number][]): number {
  if (!coords || coords.length < 2) return 0;

  const toRad = (deg: number) => (deg * Math.PI) / 180;
  let totalDist = 0;

  for (let i = 0; i < coords.length - 1; i++) {
    const lon1 = toRad(coords[i][0]);
    const lat1 = toRad(coords[i][1]);
    const lon2 = toRad(coords[i + 1][0]);
    const lat2 = toRad(coords[i + 1][1]);

    const dLat = lat2 - lat1;
    const dLon = lon2 - lon1;

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    totalDist += EARTH_RADIUS_M * c;
  }

  return Math.round(totalDist);
}

/**
 * Checks for simple line segment intersections (self-intersection).
 */
export function checkSelfIntersection(coords: [number, number][]): boolean {
  if (!coords || coords.length < 4) return false;

  const ccw = (A: [number, number], B: [number, number], C: [number, number]) => {
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0]);
  };

  const intersect = (
    A: [number, number],
    B: [number, number],
    C: [number, number],
    D: [number, number]
  ) => {
    return ccw(A, C, D) !== ccw(B, C, D) && ccw(A, B, C) !== ccw(A, B, D);
  };

  const n = coords.length;
  for (let i = 0; i < n - 1; i++) {
    for (let j = i + 2; j < n - 1; j++) {
      if (i === 0 && j === n - 2) continue; // adjacent endpoints
      if (intersect(coords[i], coords[i + 1], coords[j], coords[j + 1])) {
        return true;
      }
    }
  }
  return false;
}

/**
 * Reprojects Web Mercator EPSG:3857 coordinates to WGS84 [lon, lat]
 */
export function mercatorToWgs84(x: number, y: number): [number, number] {
  const lon = (x / 20037508.34) * 180;
  let lat = (y / 20037508.34) * 180;
  lat = (180 / Math.PI) * (2 * Math.atan(Math.exp((lat * Math.PI) / 180)) - Math.PI / 2);
  return [lon, lat];
}

/**
 * Parses KML string into coordinates array [[lon, lat], ...]
 */
export function parseKMLCoordinates(kmlText: string): [number, number][] {
  const coordRegex = /<coordinates>([\s\S]*?)<\/coordinates>/i;
  const match = kmlText.match(coordRegex);
  if (!match) return [];

  const raw = match[1].trim();
  const pairs = raw.split(/\s+/);
  const result: [number, number][] = [];

  for (const pair of pairs) {
    const parts = pair.split(',');
    if (parts.length >= 2) {
      const lon = parseFloat(parts[0]);
      const lat = parseFloat(parts[1]);
      if (!isNaN(lon) && !isNaN(lat)) {
        result.push([lon, lat]);
      }
    }
  }

  return result;
}

/**
 * Main parser that turns raw text (GeoJSON, KML, or Shapefile-JSON) into a valid CustomAOI object.
 */
export function parseAndValidateAOI(
  rawInput: string,
  aoiName: string = 'Imported AOI'
): { success: boolean; aoi?: CustomAOI; error?: string; warnings?: string[] } {
  const warnings: string[] = [];
  let format: 'geojson' | 'kml' | 'shapefile' = 'geojson';
  let coords: [number, number][] = [];
  let detectedCrs = 'EPSG:4326 (WGS84)';
  let geojsonOutput: any = null;

  const trimmed = rawInput.trim();

  // 1. Determine format and extract rings
  if (trimmed.startsWith('<') && (trimmed.includes('<kml') || trimmed.includes('<coordinates>'))) {
    format = 'kml';
    coords = parseKMLCoordinates(trimmed);
    if (coords.length === 0) {
      return { success: false, error: 'Could not find valid <coordinates> in KML.' };
    }
  } else {
    // Attempt JSON parsing (GeoJSON or Shapefile JSON)
    try {
      const parsed = JSON.parse(trimmed);

      // Check if FeatureCollection, Feature, or Geometry
      let geometry = parsed;
      if (parsed.type === 'FeatureCollection' && parsed.features && parsed.features.length > 0) {
        geometry = parsed.features[0].geometry;
      } else if (parsed.type === 'Feature' && parsed.geometry) {
        geometry = parsed.geometry;
      }

      if (parsed.crs && parsed.crs.properties && parsed.crs.properties.name) {
        detectedCrs = parsed.crs.properties.name;
      }

      if (geometry.type === 'Polygon') {
        coords = geometry.coordinates[0];
      } else if (geometry.type === 'MultiPolygon') {
        warnings.push('Multipart polygon detected: using primary outer boundary shell.');
        coords = geometry.coordinates[0][0];
      } else {
        return { success: false, error: `Unsupported geometry type: ${geometry.type}. Must be Polygon or MultiPolygon.` };
      }
    } catch (e: any) {
      return { success: false, error: `Invalid JSON/GeoJSON syntax: ${e.message}` };
    }
  }

  if (!coords || coords.length < 3) {
    return { success: false, error: 'AOI geometry requires at least 3 vertices.' };
  }

  // Detect Web Mercator and reproject
  const sampleX = coords[0][0];
  const sampleY = coords[0][1];
  if (Math.abs(sampleX) > 180 || Math.abs(sampleY) > 90) {
    detectedCrs = 'EPSG:3857 (Reprojected to WGS84)';
    warnings.push('Projected coordinates detected (EPSG:3857) — automatically reprojected to EPSG:4326.');
    coords = coords.map((c) => mercatorToWgs84(c[0], c[1]));
  }

  // Ensure ring closure
  const first = coords[0];
  const last = coords[coords.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    coords.push([first[0], first[1]]);
  }

  // Self intersection check
  const isSelfIntersecting = checkSelfIntersection(coords);
  if (isSelfIntersecting) {
    warnings.push('Self-intersection detected in polygon boundary — topological cleaning recommended.');
  }

  // Bounds & Centroid calculation
  let minLon = 180;
  let maxLon = -180;
  let minLat = 90;
  let maxLat = -90;
  let sumLon = 0;
  let sumLat = 0;

  for (const [lon, lat] of coords) {
    if (lon < minLon) minLon = lon;
    if (lon > maxLon) maxLon = lon;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
    sumLon += lon;
    sumLat += lat;
  }

  const centerLon = +(sumLon / coords.length).toFixed(6);
  const centerLat = +(sumLat / coords.length).toFixed(6);

  // Area & Perimeter
  const areaM2 = calculateGeodesicPolygonArea(coords);
  const areaHa = +(areaM2 / 10000).toFixed(2);
  const perimeterM = calculateGeodesicPerimeter(coords);

  geojsonOutput = {
    type: 'Feature',
    properties: {
      name: aoiName,
      area_ha: areaHa,
      area_m2: areaM2,
      perimeter_m: perimeterM,
      crs: detectedCrs,
    },
    geometry: {
      type: 'Polygon',
      coordinates: [coords],
    },
  };

  const aoi: CustomAOI = {
    id: `aoi_${Date.now()}`,
    name: aoiName,
    format,
    geojson: geojsonOutput,
    coordinates: [coords],
    bounds: {
      minLat,
      maxLat,
      minLon,
      maxLon,
      centerLat,
      centerLon,
    },
    areaM2,
    areaHa,
    perimeterM,
    vertexCount: coords.length,
    crs: detectedCrs,
    isMaskingEnabled: true,
    createdAt: new Date().toISOString(),
  };

  return { success: true, aoi, warnings };
}
