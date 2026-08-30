export interface CRSInfo {
  present: boolean;
  valid: boolean;
  epsg: number | null;
  name: string | null;
  type: string;
  status: string;
  units: string | null;
}

export interface BoundingBox {
  min_x: number;
  min_y: number;
  max_x: number;
  max_y: number;
  wgs84?: {
    min_lon: number;
    min_lat: number;
    max_lon: number;
    max_lat: number;
  } | null;
}

export interface SpatialResolution {
  x_res: number;
  y_res: number;
  units: string;
}

export interface BandStatistics {
  band_index: number;
  dtype: string;
  min: number;
  max: number;
  mean: number;
  std?: number | null;
  nodata?: number | null;
}

export interface ModalityInfo {
  detected: string;
  confidence: number;
  basis: string[];
}

export interface RasterMetadata {
  filename: string;
  format: string;
  driver?: string | null;
  width: number;
  height: number;
  band_count: number;
  dtype: string;
  crs: CRSInfo;
  transform: number[];
  bounds?: BoundingBox | null;
  resolution: SpatialResolution;
  nodata?: number | null;
  compression?: string | null;
  bands: BandStatistics[];
  modality: ModalityInfo;
  tags?: Record<string, string>;
}

export interface ValidationResult {
  valid: boolean;
  warnings: string[];
  errors: string[];
}

export interface PreviewInfo {
  available: boolean;
  preview_url?: string | null;
}

export interface ImageInspectionResponse {
  id: string;
  status: string;
  metadata?: RasterMetadata | null;
  validation: ValidationResult;
  preview: PreviewInfo;
}

export interface ImageSummary {
  id: string;
  filename: string;
  format: string;
  modality: string;
  width: number;
  height: number;
  band_count: number;
  crs?: string | null;
  preview_url?: string | null;
  created_at: string;
}

export interface ExecutionStep {
  step_number: number;
  tool: string;
  description: string;
  status: string;
  duration_ms: number;
  model?: string | null;
  output_summary?: string | null;
}

export interface ConfidenceScore {
  overall: number;
  model_score: number;
  resolution_score: number;
  registration_score?: number | null;
  sar_agreement_score?: number | null;
  factors: Record<string, number>;
  notes: string[];
}

export interface EvidenceObject {
  id: string;
  claim: string;
  source_analysis_id: string;
  source_image_ids: string[];
  model_used: string;
  output_geometry?: any;
  confidence: ConfidenceScore;
  execution_steps: ExecutionStep[];
  artifacts: string[];
  created_at: string;
}

export interface VQAAnalysisResult {
  job_id: string;
  image_id: string;
  question: string;
  answer: string;
  confidence: ConfidenceScore;
  evidence: EvidenceObject;
  execution_steps: ExecutionStep[];
  total_duration_ms: number;
}

export interface GroundingFeature {
  type: string;
  id: string;
  properties: {
    label: string;
    confidence: number;
    area_m2: number;
    bbox_normalized: { ymin: number; xmin: number; ymax: number; xmax: number };
    bbox_pixel: { ymin: number; xmin: number; ymax: number; xmax: number };
  };
  geometry: any;
}

export interface GroundingAnalysisResult {
  job_id: string;
  image_id: string;
  referring_expression: string;
  regions_geojson: {
    type: string;
    features: GroundingFeature[];
  };
  total_area_m2: number;
  confidence: ConfidenceScore;
  evidence: EvidenceObject;
  execution_steps: ExecutionStep[];
  total_duration_ms: number;
}

export interface ChangeFeature {
  type: string;
  id: string;
  properties: {
    cluster_id: number;
    area_m2: number;
    area_ha: number;
    pixel_count: number;
  };
  geometry: any;
}

export interface ChangeAnalysisResult {
  job_id: string;
  image_before_id: string;
  image_after_id: string;
  change_percent: number;
  total_area_m2: number;
  total_area_ha: number;
  cluster_count: number;
  regions_geojson: {
    type: string;
    features: ChangeFeature[];
  };
  mask_preview_url: string;
  is_trained: boolean;
  confidence: ConfidenceScore;
  evidence: EvidenceObject;
  execution_steps: ExecutionStep[];
  total_duration_ms: number;
}

export interface OpticalSARAnalysisResult {
  job_id: string;
  optical_image_id: string;
  sar_image_id: string;
  corroboration_score: number;
  joint_claim: string;
  optical_features: {
    sensor: string;
    band_count: number;
    mean_spectral: number[];
    water_fraction_proxy: number;
    embedding_dim: number;
  };
  sar_features: {
    sensor: string;
    polarization: string;
    mean_sigma0_db: number;
    min_sigma0_db: number;
    max_sigma0_db: number;
    std_sigma0_db: number;
    low_backscatter_fraction: number;
    embedding_dim: number;
  };
  confidence: ConfidenceScore;
  evidence: EvidenceObject;
  execution_steps: ExecutionStep[];
  total_duration_ms: number;
}

export interface AgentQueryResponse {
  query: string;
  intent: string;
  intent_confidence: number;
  job_id: string;
  answer: string;
  pipeline_result: any;
  confidence: ConfidenceScore;
  evidence: EvidenceObject;
  execution_steps: ExecutionStep[];
  report_urls: {
    pdf: string;
    geojson: string;
    csv: string;
  };
  total_duration_ms: number;
}

export interface HardwareInfo {
  torch_available: boolean;
  cuda_available: boolean;
  device: string;
  active_model?: string | null;
  gpu?: {
    name: string;
    total_vram_mb: number;
    allocated_vram_mb: number;
    reserved_vram_mb: number;
    peak_vram_mb: number;
    multi_processor_count: number;
  } | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version?: string;
  environment?: string;
  hardware?: HardwareInfo;
}
