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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

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
  aoiId?: string
): Promise<AgentQueryResponse> {
  const res = await fetch(`${API_BASE}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, image_ids: imageIds, aoi_id: aoiId }),
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
