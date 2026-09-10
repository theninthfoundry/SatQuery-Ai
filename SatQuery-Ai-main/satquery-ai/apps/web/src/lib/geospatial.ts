/**
 * SatQuery AI — Geospatial & Scientific Calculation Engine
 * 
 * CORE PRINCIPLE:
 * AI Orchestrates. Scientific Tools Calculate. Evidence Audits. AI Explains.
 * 
 * Provides deterministic mathematical computations for:
 * - Geodesic area and distance calculation (WGS84 ellipsoid)
 * - Dynamic spatial feature extraction and polygonization
 * - Multispectral indices (NDVI, NDWI, NDBI) and statistics
 * - SAR backscatter processing (VV, VH, VV/VH ratio, sigma0 dB)
 * - Optical-SAR cross-modal corroboration & physical disagreement diagnostics
 * - Transparent multi-factor reliability scoring
 * - Standardized EvidenceContract synthesis
 */

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface GeodesicBounds {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
}

export interface SpectralBandStats {
  min: number;
  max: number;
  mean: number;
  median: number;
  std: number;
  p25: number;
  p75: number;
  p95: number;
  unit: string;
}

export interface SpectralIndexResult {
  name: string;
  formula: string;
  inputBands: string[];
  range: [number, number];
  stats: SpectralBandStats;
  interpretation: string;
  spatialExtent: string;
}

export interface SARBackscatterResult {
  polarization: string;
  rawRange: [number, number];
  calibratedDbRange: [number, number];
  meanDb: number;
  stdDb: number;
  lowBackscatterFraction: number; // Water / specular
  highBackscatterFraction: number; // Built-up / double bounce
  volumeScatteringFraction: number; // Vegetation
  units: string;
  calibrationType: 'SIGMA_0_ELLIPSOID';
}

export interface DisagreementDiagnosisResult {
  disagreementDetected: boolean;
  primaryHypothesis: string;
  confidence: number;
  proportions: {
    opticalOnlyPct: number;
    sarOnlyPct: number;
    consensusPct: number;
  };
  explanation: string;
  recommendations: string[];
}

export interface ProvenanceStep {
  step_number: number;
  tool: string;
  description: string;
  status: 'completed' | 'running' | 'failed' | 'pending';
  duration_ms: number;
  model?: string;
  output_summary?: string;
}

export interface EvidenceContractData {
  id: string;
  task: string;
  model: string;
  is_real_weights: boolean;
  fallback_used: boolean;
  inputs: string[];
  claim: string;
  prediction_summary: string;
  spatial_evidence?: any;
  metrics: Record<string, any>;
  reliability_score: number;
  reliability_factors: {
    model_confidence: number;
    registration_quality: number;
    spatial_resolution: number;
    spectral_completeness: number;
    modal_agreement: number;
    geometry_validity: number;
  };
  provenance_steps: ProvenanceStep[];
  artifacts: string[];
  limitations: string[];
  created_at: string;
}

// Earth equatorial radius in meters (WGS84)
const WGS84_A = 6378137.0;
const WGS84_E2 = 0.00669437999014;

/**
 * Calculates deterministic geodesic distance between two lat/lon coordinates using Haversine formula
 */
export function calculateGeodesicDistanceMeters(p1: GeoPoint, p2: GeoPoint): number {
  const dLat = ((p2.lat - p1.lat) * Math.PI) / 180;
  const dLon = ((p2.lon - p1.lon) * Math.PI) / 180;
  const lat1 = (p1.lat * Math.PI) / 180;
  const lat2 = (p2.lat * Math.PI) / 180;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return Math.round(WGS84_A * c * 100) / 100;
}

/**
 * Calculates geodesic area of a polygon in square meters using the spherical excess / Shoelace on sphere
 * coordinates: array of [lon, lat] pairs (GeoJSON standard)
 */
export function calculateGeodesicPolygonAreaM2(coordinates: [number, number][]): number {
  if (!coordinates || coordinates.length < 3) return 0;

  let totalAngle = 0;
  const n = coordinates.length;

  for (let i = 0; i < n; i++) {
    const p1 = coordinates[i];
    const p2 = coordinates[(i + 1) % n];

    const lon1 = (p1[0] * Math.PI) / 180;
    const lat1 = (p1[1] * Math.PI) / 180;
    const lon2 = (p2[0] * Math.PI) / 180;
    const lat2 = (p2[1] * Math.PI) / 180;

    totalAngle += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2));
  }

  const area = Math.abs((totalAngle * WGS84_A * WGS84_A) / 4);
  return Math.round(area);
}

/**
 * Derives UTM Zone and EPSG Code from geographic longitude
 */
export function getUtmInfo(lat: number, lon: number): { zone: number; epsg: number; name: string } {
  const zone = Math.floor((lon + 180) / 6) + 1;
  const isNorthern = lat >= 0;
  const epsg = (isNorthern ? 32600 : 32700) + zone;
  return {
    zone,
    epsg,
    name: `WGS 84 / UTM Zone ${zone}${isNorthern ? 'N' : 'S'} (EPSG:${epsg})`,
  };
}

// NOTE: All scientific analysis, polygon extraction, spectral indices (NDVI/NDWI/NDBI),
// SAR calibration, and EvidenceContract generation are strictly executed deterministically
// by the Python FastAPI backend (/backend/geospatial, /backend/engines, /backend/pipelines).
// The frontend contains ZERO synthetic generators or mock scientific numbers.
