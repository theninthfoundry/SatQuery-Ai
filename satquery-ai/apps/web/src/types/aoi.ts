export interface CustomAOI {
  id: string;
  name: string;
  format: 'geojson' | 'kml' | 'shapefile' | 'drawn';
  geojson: any;
  coordinates: [number, number][][]; // [ [ [lon, lat], ... ] ]
  bounds: {
    minLat: number;
    maxLat: number;
    minLon: number;
    maxLon: number;
    centerLat: number;
    centerLon: number;
  };
  areaM2: number;
  areaHa: number;
  perimeterM: number;
  vertexCount: number;
  crs: string;
  isMaskingEnabled: boolean;
  createdAt: string;
}

export interface SentinelWatch {
  id: string;
  name: string;
  aoiId: string;
  aoiName: string;
  aoiCenter: { lat: number; lon: number };
  sensors: string[];
  frequency: string;
  conditions: {
    builtUpIncreaseHa?: number;
    ndviDecreasePct?: number;
    sarAnomalyDb?: number;
  };
  status: 'MONITORING' | 'TRIGGERED' | 'PAUSED';
  lastCheck: string;
  nextScene: string;
  metrics: {
    builtUpDeltaHa: number;
    vegetationDeltaPct: number;
    sarAnomaly: string;
  };
  createdAt: string;
}

export interface SpectralPointData {
  lat: number;
  lon: number;
  utmE: number;
  utmN: number;
  gsd: string;
  landCover: string;
  bands: {
    b02: number; // Blue (490nm)
    b03: number; // Green (560nm)
    b04: number; // Red (665nm)
    b05: number; // Red Edge 1 (705nm)
    b06: number; // Red Edge 2 (740nm)
    b07: number; // Red Edge 3 (783nm)
    b08: number; // NIR (842nm)
    b8a: number; // Narrow NIR (865nm)
    b11: number; // SWIR-1 (1610nm)
    b12: number; // SWIR-2 (2190nm)
  };
  indices: {
    ndvi: number;
    ndwi: number;
    ndbi: number;
  };
  sar: {
    vvDb: number;
    vhDb: number;
    ratioDb: number;
  };
}

export interface ZonalStatistics {
  meanNDVI: number;
  medianNDVI: number;
  stdDevNDVI: number;
  minNDVI: number;
  maxNDVI: number;
  meanNDWI: number;
  meanNDBI: number;
  meanSARdB: number;
  areaHa: number;
  pixelCount: number;
}

export interface EpochObservation {
  id: string;
  epochNumber: number;
  date: string;
  sensor: 'Sentinel-2 MSI' | 'Sentinel-1 C-SAR' | 'Sentinel-2 + Sentinel-1';
  cloudCoverPct: number;
  resolution: string;
  orbitMetadata: string;
  sunElevationDeg: number;
  thumbnailUrl?: string;
  isCloudFree: boolean;
  builtUpHa: number;
  meanNdvi: number;
  sarMeanDb: number;
}
