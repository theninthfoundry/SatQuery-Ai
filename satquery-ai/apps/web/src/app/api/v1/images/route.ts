import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const CANONICAL_IMAGES = [
  {
    id: 'opt_t1',
    filename: 'S2A_MSIL2A_20240315_T43PGJ_Bangalore_T1.tif',
    format: 'GeoTIFF',
    modality: 'optical',
    width: 10980,
    height: 10980,
    band_count: 12,
    crs: 'EPSG:32643',
    preview_url: null,
    created_at: '2024-03-15T05:30:00Z',
  },
  {
    id: 'opt_t2',
    filename: 'S2B_MSIL2A_20260319_T43PGJ_Bangalore_T2.tif',
    format: 'GeoTIFF',
    modality: 'optical',
    width: 10980,
    height: 10980,
    band_count: 12,
    crs: 'EPSG:32643',
    preview_url: null,
    created_at: '2026-03-19T05:30:00Z',
  },
  {
    id: 'sar_s1',
    filename: 'S1A_IW_GRDH_1SDV_20260318_Bangalore_SAR.tif',
    format: 'GeoTIFF',
    modality: 'sar',
    width: 10980,
    height: 10980,
    band_count: 2,
    crs: 'EPSG:32643',
    preview_url: null,
    created_at: '2026-03-18T12:45:00Z',
  },
  {
    id: 'img_demo_brahmaputra_flood',
    filename: 'S2_Brahmaputra_Assam_Grounding_10m.tif',
    format: 'GeoTIFF',
    modality: 'optical',
    width: 8400,
    height: 8400,
    band_count: 12,
    crs: 'EPSG:32646',
    preview_url: null,
    created_at: '2025-07-22T04:15:00Z',
  },
  {
    id: 'img_demo_bitemporal_t2',
    filename: 'S2B_Bangalore_PeriUrban_Expansion_T2.tif',
    format: 'GeoTIFF',
    modality: 'optical',
    width: 10980,
    height: 10980,
    band_count: 12,
    crs: 'EPSG:32643',
    preview_url: null,
    created_at: '2026-03-19T05:30:00Z',
  },
];

export async function GET() {
  const backendUrl = process.env.BACKEND_API_URL;
  if (backendUrl) {
    try {
      const res = await fetch(`${backendUrl.replace(/\/$/, '')}/api/v1/images`, {
        cache: 'no-store',
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to canonical dataset
    }
  }

  return NextResponse.json(CANONICAL_IMAGES);
}
