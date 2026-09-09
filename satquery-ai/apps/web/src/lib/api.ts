import {
  HealthResponse,
  ImageInspectionResponse,
  VQAAnalysisResult,
  GroundingAnalysisResult,
  ChangeAnalysisResult,
  OpticalSARAnalysisResult,
  AgentQueryResponse,
  ImageSummary,
} from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/health`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return await res.json();
  } catch (error) {
    return {
      status: 'offline',
      service: 'satquery-api',
      hardware: {
        torch_available: false,
        cuda_available: false,
        device: 'offline',
        gpu: null,
      },
    };
  }
}

export async function fetchImagesList(): Promise<ImageSummary[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/images`, { cache: 'no-store' });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function inspectImageFile(file: File, aoiId?: string): Promise<ImageInspectionResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (aoiId) {
    formData.append('aoi_id', aoiId);
  }

  const res = await fetch(`${API_BASE}/api/v1/images/inspect`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Upload failed (${res.status}): ${errText}`);
  }

  return await res.json();
}

export async function submitAgentQuery(
  query: string,
  imageIds: string[],
  aoiId?: string,
  context?: {
    lat?: number;
    lon?: number;
    location_name?: string;
    utm_zone?: string;
    expected_source_image_id?: string;
    source_image_id?: string;
    [key: string]: any;
  }
): Promise<AgentQueryResponse> {
  const res = await fetch(`${API_BASE}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      image_ids: imageIds,
      aoi_id: aoiId,
      lat: context?.lat,
      lon: context?.lon,
      location_name: context?.location_name,
      utm_zone: context?.utm_zone,
      expected_source_image_id: context?.expected_source_image_id,
      source_image_id: context?.source_image_id,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Agent orchestration failed (${res.status}): ${errText}`);
  }

  return await res.json();
}

export const executeAgentQuery = submitAgentQuery;

export async function submitVQA(imageId: string, question: string): Promise<VQAAnalysisResult> {
  const res = await fetch(`${API_BASE}/api/v1/analysis/vqa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId, question }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`VQA analysis failed (${res.status}): ${errText}`);
  }

  return await res.json();
}

export async function submitGrounding(
  imageId: string,
  referringExpression: string
): Promise<GroundingAnalysisResult> {
  const res = await fetch(`${API_BASE}/api/v1/analysis/grounding`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId, referring_expression: referringExpression }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Visual grounding failed (${res.status}): ${errText}`);
  }

  return await res.json();
}

export async function submitChangeAnalysis(
  imageBeforeId: string,
  imageAfterId: string,
  threshold: number = 0.5,
  aoiId?: string
): Promise<ChangeAnalysisResult> {
  const res = await fetch(`${API_BASE}/api/v1/analysis/change`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_before_id: imageBeforeId,
      image_after_id: imageAfterId,
      threshold,
      aoi_id: aoiId,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Change analysis failed (${res.status}): ${errText}`);
  }

  return await res.json();
}

export async function submitOpticalSARAnalysis(
  opticalImageId: string,
  sarImageId: string,
  aoiId?: string
): Promise<OpticalSARAnalysisResult> {
  const res = await fetch(`${API_BASE}/api/v1/analysis/optical-sar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      optical_image_id: opticalImageId,
      sar_image_id: sarImageId,
      aoi_id: aoiId,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Optical+SAR multimodal analysis failed (${res.status}): ${errText}`);
  }

  return await res.json();
}

export function getPreviewUrl(previewPathOrUrl?: string | null): string | null {
  if (!previewPathOrUrl) return null;
  if (previewPathOrUrl.startsWith('http')) return previewPathOrUrl;
  return `${API_BASE}${previewPathOrUrl}`;
}

export function getReportDownloadUrl(endpoint: string): string {
  if (endpoint.startsWith('http')) return endpoint;
  return `${API_BASE}${endpoint}`;
}

export async function pixelInspect(
  imageId: string,
  lat: number,
  lon: number,
  compareImageId?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/images/${imageId}/pixel-inspect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lat, lon, compare_image_id: compareImageId }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Pixel inspect failed: ${errText}`);
  }
  return await res.json();
}

export async function computeZonalStats(
  imageId: string,
  geometry: any,
  bandIndex: number = 1
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/images/${imageId}/zonal-stats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ geometry, band_index: bandIndex }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Zonal stats failed: ${errText}`);
  }
  return await res.json();
}

export async function uploadAOIFile(file: File, name?: string): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);

  const url = `${API_BASE}/api/v1/aoi/upload`;

  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  const contentType = res.headers.get('content-type') || '';

  if (!res.ok) {
    const body = contentType.includes('application/json')
      ? await res.json().catch(() => null)
      : await res.text();

    const message =
      typeof body === 'string'
        ? body
        : body?.detail?.message ||
          body?.detail ||
          body?.message ||
          `HTTP ${res.status}`;

    throw new Error(`AOI upload failed (${res.status}): ${message}`);
  }

  if (!contentType.includes('application/json')) {
    const body = await res.text();
    throw new Error(
      `AOI endpoint returned ${contentType || 'unknown content type'} instead of JSON. ` +
      `URL: ${url}. Response starts with: ${body.slice(0, 200)}`
    );
  }

  return await res.json();
}

export async function fetchObservationsTimeline(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/images/timeline`, { cache: 'no-store' });
  if (!res.ok) return { count: 0, timeline: [] };
  return await res.json();
}

export async function replayAnalysisJob(jobId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/analysis/${jobId}/replay`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Analysis replay failed: ${errText}`);
  }
  return await res.json();
}

export async function searchSTAC(params: {
  bbox: number[];
  start_date?: string;
  end_date?: string;
  collection?: string;
  max_cloud_cover?: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/stac/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      bbox: params.bbox,
      start_date: params.start_date || '2024-01-01',
      end_date: params.end_date || '2026-12-31',
      collection: params.collection || 'sentinel-2-l2a',
      max_cloud_cover: params.max_cloud_cover || 25.0,
      limit: 10,
    }),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`STAC search failed: ${errText}`);
  }
  return await res.json();
}

export async function fetchModelsManifest(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/models`, { cache: 'no-store' });
  if (!res.ok) return { models: [], manifest: null, hardware: null };
  return await res.json();
}
