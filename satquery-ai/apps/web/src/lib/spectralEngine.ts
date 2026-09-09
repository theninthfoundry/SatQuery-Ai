import { SpectralPointData, ZonalStatistics } from '../types/aoi';

/**
 * Computes deterministic multi-spectral BOA surface reflectance (10 bands)
 * and Sentinel-1 SAR C-band backscatter at any given geographic coordinate.
 */
export function getSpectralAndRadarPoint(lat: number, lon: number): SpectralPointData {
  // Derive a pseudo-random yet deterministic spatial hash based on coordinates
  const spatialSeed = Math.abs(Math.sin(lat * 12.9898 + lon * 78.233) * 43758.5453) % 1;
  const zoneNumber = Math.floor((lon + 180) / 6) + 1;
  const utmE = Math.round(500000 + (lon - (zoneNumber * 6 - 183)) * 111000);
  const utmN = Math.round(lat * 110574);

  // Land cover classification heuristic
  // In urban test regions like Bangalore/Hyderabad, variation reflects built-up, vegetated parks, and water bodies
  let landCover = 'VEGETATION / CROP';
  let b02 = 0.045 + spatialSeed * 0.03; // Blue
  let b03 = 0.082 + spatialSeed * 0.035; // Green
  let b04 = 0.051 + spatialSeed * 0.04; // Red
  let b05 = 0.125 + spatialSeed * 0.06; // Red Edge 1
  let b06 = 0.245 + spatialSeed * 0.07; // Red Edge 2
  let b07 = 0.312 + spatialSeed * 0.08; // Red Edge 3
  let b08 = 0.528 + spatialSeed * 0.09; // NIR
  let b8a = 0.495 + spatialSeed * 0.08; // Narrow NIR
  let b11 = 0.185 + spatialSeed * 0.05; // SWIR-1
  let b12 = 0.112 + spatialSeed * 0.04; // SWIR-2

  let vvDb = -11.2 - spatialSeed * 4.2;
  let vhDb = -18.5 - spatialSeed * 3.5;

  // Water check
  if ((spatialSeed * 10) % 3 < 0.45) {
    landCover = 'WATER BODY / RESERVOIR';
    b02 = 0.095;
    b03 = 0.075;
    b04 = 0.032;
    b05 = 0.021;
    b06 = 0.015;
    b07 = 0.012;
    b08 = 0.009;
    b8a = 0.008;
    b11 = 0.005;
    b12 = 0.004;
    vvDb = -22.4 - spatialSeed * 3.0; // Specular dark in radar
    vhDb = -28.1 - spatialSeed * 2.0;
  } else if ((spatialSeed * 10) % 2 < 0.95) {
    // Built-up / Industrial Structure
    landCover = 'URBAN BUILT-UP / INDUSTRIAL';
    b02 = 0.115 + spatialSeed * 0.04;
    b03 = 0.142 + spatialSeed * 0.03;
    b04 = 0.168 + spatialSeed * 0.05;
    b05 = 0.185 + spatialSeed * 0.04;
    b06 = 0.205 + spatialSeed * 0.04;
    b07 = 0.218 + spatialSeed * 0.04;
    b08 = 0.235 + spatialSeed * 0.05;
    b8a = 0.240 + spatialSeed * 0.04;
    b11 = 0.285 + spatialSeed * 0.06; // High SWIR
    b12 = 0.248 + spatialSeed * 0.05;
    vvDb = -6.4 + spatialSeed * 3.2; // Double-bounce corner reflection (> -8 dB)
    vhDb = -12.1 + spatialSeed * 2.8;
  }

  // Calculate standard indices
  const ndvi = +((b08 - b04) / Math.max(0.001, b08 + b04)).toFixed(2);
  const ndwi = +((b03 - b08) / Math.max(0.001, b03 + b08)).toFixed(2);
  const ndbi = +((b11 - b08) / Math.max(0.001, b11 + b08)).toFixed(2);
  const ratioDb = +(vvDb - vhDb).toFixed(1);

  return {
    lat: +lat.toFixed(5),
    lon: +lon.toFixed(5),
    utmE,
    utmN,
    gsd: '10 m',
    landCover,
    bands: {
      b02: +b02.toFixed(3),
      b03: +b03.toFixed(3),
      b04: +b04.toFixed(3),
      b05: +b05.toFixed(3),
      b06: +b06.toFixed(3),
      b07: +b07.toFixed(3),
      b08: +b08.toFixed(3),
      b8a: +b8a.toFixed(3),
      b11: +b11.toFixed(3),
      b12: +b12.toFixed(3),
    },
    indices: { ndvi, ndwi, ndbi },
    sar: { vvDb: +vvDb.toFixed(1), vhDb: +vhDb.toFixed(1), ratioDb },
  };
}

/**
 * Computes deterministic Zonal Statistics over an area in hectares or coordinates array.
 */
export function calculateZonalStatistics(areaHa: number, centerLat: number, centerLon: number): ZonalStatistics {
  // Deterministic zonal metrics derived from geography
  const seed = Math.abs(Math.sin(centerLat * 11.23 + centerLon * 45.67)) % 1;

  const meanNDVI = +(0.52 + seed * 0.24).toFixed(2);
  const medianNDVI = +(meanNDVI + 0.03).toFixed(2);
  const stdDevNDVI = +(0.08 + (seed % 0.06)).toFixed(2);
  const minNDVI = +(meanNDVI - 0.28).toFixed(2);
  const maxNDVI = +(Math.min(0.88, meanNDVI + 0.25)).toFixed(2);

  const meanNDWI = +(-0.18 + seed * 0.35).toFixed(2);
  const meanNDBI = +(0.12 - seed * 0.3).toFixed(2);
  const meanSARdB = +(-13.4 + seed * 5.2).toFixed(1);

  // Sentinel-2 has 10m GSD, so 1 pixel = 100 m² = 0.01 ha.
  // Pixels = Area in m² / 100 = Area in ha * 100.
  const pixelCount = Math.round(areaHa * 1000);

  return {
    meanNDVI,
    medianNDVI,
    stdDevNDVI,
    minNDVI,
    maxNDVI,
    meanNDWI,
    meanNDBI,
    meanSARdB,
    areaHa,
    pixelCount,
  };
}
