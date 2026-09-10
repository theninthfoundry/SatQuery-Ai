import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const CANONICAL_TIMELINE = [
  {
    id: 'opt_t1',
    filename: 'S2A_MSIL2A_20240315_T43PGJ_Bangalore_T1.tif',
    date: '2024-03-15',
    created_at: '2024-03-15T05:30:00Z',
    modality: 'multispectral',
    platform: 'Sentinel-2A',
    cloud_cover_percentage: 1.2,
    resolution_m: 10.0,
    crs: 'EPSG:32643',
    bounds: { min_lon: 77.5, min_lat: 12.85, max_lon: 77.75, max_lat: 13.1 },
    preview_url: null,
  },
  {
    id: 'img_demo_brahmaputra_flood',
    filename: 'S2_Brahmaputra_Assam_Grounding_10m.tif',
    date: '2025-07-22',
    created_at: '2025-07-22T04:15:00Z',
    modality: 'multispectral',
    platform: 'Sentinel-2B',
    cloud_cover_percentage: 3.5,
    resolution_m: 10.0,
    crs: 'EPSG:32646',
    bounds: { min_lon: 92.8, min_lat: 26.1, max_lon: 93.1, max_lat: 26.3 },
    preview_url: null,
  },
  {
    id: 'sar_s1',
    filename: 'S1A_IW_GRDH_1SDV_20260318_Bangalore_SAR.tif',
    date: '2026-03-18',
    created_at: '2026-03-18T12:45:00Z',
    modality: 'sar',
    platform: 'Sentinel-1A C-SAR',
    cloud_cover_percentage: 0.0,
    resolution_m: 10.0,
    crs: 'EPSG:32643',
    bounds: { min_lon: 77.5, min_lat: 12.85, max_lon: 77.75, max_lat: 13.1 },
    preview_url: null,
  },
  {
    id: 'opt_t2',
    filename: 'S2B_MSIL2A_20260319_T43PGJ_Bangalore_T2.tif',
    date: '2026-03-19',
    created_at: '2026-03-19T05:30:00Z',
    modality: 'multispectral',
    platform: 'Sentinel-2B',
    cloud_cover_percentage: 0.8,
    resolution_m: 10.0,
    crs: 'EPSG:32643',
    bounds: { min_lon: 77.5, min_lat: 12.85, max_lon: 77.75, max_lat: 13.1 },
    preview_url: null,
  },
];

export async function GET() {
  const backendUrl = process.env.BACKEND_API_URL;
  if (backendUrl) {
    try {
      const res = await fetch(`${backendUrl.replace(/\/$/, '')}/api/v1/images/timeline`, {
        cache: 'no-store',
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to canonical timeline
    }
  }

  return NextResponse.json({
    count: CANONICAL_TIMELINE.length,
    timeline: CANONICAL_TIMELINE,
  });
}
