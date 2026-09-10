import { Finding } from '../types';

export interface ExpectedFinding {
  id: string;
  label: string;
  expected_area_ha: number;
  tolerance_ha: number;
  expected_confidence_min: number;
  expected_crs: string;
  phenomenon: string;
  sensors_required: string[];
}

export interface GoldenMissionSpec {
  id: string;
  name: string;
  aoi_name: string;
  lat: number;
  lon: number;
  t1_date: string;
  t2_date: string;
  expected_findings: ExpectedFinding[];
}

export const GOLDEN_MISSION_SPEC: GoldenMissionSpec = {
  id: 'mission_05_compound',
  name: 'Urban Expansion with Multimodal SAR Corroboration',
  aoi_name: 'Bangalore Urban Corridor (EPSG:32643)',
  lat: 12.9716,
  lon: 77.5946,
  t1_date: '2024-03-14',
  t2_date: '2026-03-19',
  expected_findings: [
    {
      id: 'tech_park_expansion',
      label: 'Phase 2 Commercial Tech Park Expansion',
      expected_area_ha: 1.82,
      tolerance_ha: 0.15,
      expected_confidence_min: 0.90,
      expected_crs: 'EPSG:32643',
      phenomenon: 'Vertical Built-up Surface Expansion',
      sensors_required: ['Sentinel-2 MSI (10m)', 'Sentinel-1 C-SAR (VV/VH)'],
    },
    {
      id: 'logistics_depot_expansion',
      label: 'Highway Logistics & Freight Depot Expansion',
      expected_area_ha: 0.74,
      tolerance_ha: 0.10,
      expected_confidence_min: 0.85,
      expected_crs: 'EPSG:32643',
      phenomenon: 'Earthwork & Impervious Road Surface',
      sensors_required: ['Sentinel-2 MSI (10m)'],
    },
  ],
};

export function verifyFindingAgainstGoldenSpec(
  actualAreaHa: number,
  expectedSpec: ExpectedFinding
): {
  passed: boolean;
  deltaHa: number;
  percentError: number;
  verdict: string;
} {
  const deltaHa = Math.abs(actualAreaHa - expectedSpec.expected_area_ha);
  const passed = deltaHa <= expectedSpec.tolerance_ha;
  const percentError = (deltaHa / expectedSpec.expected_area_ha) * 100;
  const verdict = passed
    ? `VERIFIED: ${actualAreaHa.toFixed(2)} ha is within ±${expectedSpec.tolerance_ha} ha tolerance (${percentError.toFixed(1)}% error)`
    : `FAILED: ${actualAreaHa.toFixed(2)} ha deviates from expected ${expectedSpec.expected_area_ha} ha beyond tolerance`;

  return { passed, deltaHa, percentError, verdict };
}

export function createCanonicalFinding(params: {
  id: string;
  missionId: string;
  query: string;
  title: string;
  category: string;
  sensor: string;
  modality: string;
  acquisitionTime: string;
  modelName: string;
  modelVersion: string;
  checkpoint: string;
  realWeights: boolean;
  crs: string;
  areaM2: number;
  areaHa: number;
  bbox: { ymin: number; xmin: number; ymax: number; xmax: number };
  modelConfidence: number;
  evidenceScore: number;
  calibratedConfidence: number;
  sourceAssets: string[];
  processingSteps: string[];
  rasterWindow: string;
  overlay: string;
  annotation: string;
}): Finding {
  return {
    id: params.id,
    mission_id: params.missionId,
    query: params.query,
    title: params.title,
    category: params.category,
    observation: {
      asset_ids: params.sourceAssets,
      modality: params.modality,
      acquisition_time: params.acquisitionTime,
      sensor: params.sensor,
    },
    model: {
      name: params.modelName,
      version: params.modelVersion,
      checkpoint: params.checkpoint,
      real_weights: params.realWeights,
    },
    spatial: {
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [params.bbox.xmin, params.bbox.ymin],
            [params.bbox.xmax, params.bbox.ymin],
            [params.bbox.xmax, params.bbox.ymax],
            [params.bbox.xmin, params.bbox.ymax],
            [params.bbox.xmin, params.bbox.ymin],
          ],
        ],
      },
      crs: params.crs,
      area_m2: params.areaM2,
      area_ha: params.areaHa,
      bbox: params.bbox,
    },
    confidence: {
      model_confidence: params.modelConfidence,
      evidence_score: params.evidenceScore,
      calibrated_confidence: params.calibratedConfidence,
    },
    provenance: {
      source_assets: params.sourceAssets,
      processing_steps: params.processingSteps,
      timestamps: [new Date().toISOString()],
    },
    visual_evidence: {
      raster_window: params.rasterWindow,
      overlay: params.overlay,
      annotation: params.annotation,
    },
  };
}
