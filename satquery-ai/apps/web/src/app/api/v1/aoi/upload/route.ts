import { NextRequest, NextResponse } from 'next/server';
import { parseAndValidateAOI } from '../../../../../lib/aoiParser';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;
    const nameParam = formData.get('name') as string | null;

    if (!file) {
      return NextResponse.json(
        { detail: 'No file uploaded. Expected multipart form field "file".' },
        { status: 400 }
      );
    }

    const filename = file.name || 'imported_aoi.geojson';
    const aoiName = nameParam || filename.replace(/\.[^/.]+$/, '');

    // 1. If an external Python backend is configured, attempt forwarding
    const backendUrl = process.env.BACKEND_API_URL;
    if (backendUrl && !backendUrl.includes(':8000')) {
      try {
        const backendFormData = new FormData();
        backendFormData.append('file', file);
        if (nameParam) backendFormData.append('name', nameParam);

        const targetUrl = `${backendUrl.replace(/\/$/, '')}/api/v1/aoi/upload`;
        const res = await fetch(targetUrl, {
          method: 'POST',
          body: backendFormData,
        });

        if (res.ok) {
          const data = await res.json();
          return NextResponse.json(data, { status: res.status });
        }
      } catch (backendErr) {
        console.warn('Backend proxy forward failed, falling back to canonical internal geometry engine:', backendErr);
      }
    }

    // 2. Canonical Evidence-Backed Geometry Engine
    const text = await file.text();
    if (!text || text.trim().length === 0) {
      return NextResponse.json(
        { detail: 'Uploaded AOI boundary file is empty.' },
        { status: 400 }
      );
    }

    const parseResult = parseAndValidateAOI(text, aoiName);

    if (!parseResult.success || !parseResult.aoi) {
      return NextResponse.json(
        {
          detail: {
            message: 'Failed to parse AOI file',
            errors: [parseResult.error || 'Invalid geometry or unsupported boundary format.'],
            warnings: parseResult.warnings || [],
          },
        },
        { status: 422 }
      );
    }

    const aoi = parseResult.aoi;
    const bbox = [
      aoi.bounds.minLon,
      aoi.bounds.minLat,
      aoi.bounds.maxLon,
      aoi.bounds.maxLat,
    ];

    const responsePayload = {
      status: 'success',
      id: aoi.id,
      name: aoi.name,
      description: `Imported from ${filename}`,
      geometry: aoi.geojson?.geometry || {
        type: 'Polygon',
        coordinates: aoi.coordinates,
      },
      area_ha: aoi.areaHa,
      area_m2: aoi.areaM2,
      perimeter_m: aoi.perimeterM,
      bbox,
      crs: 'EPSG:4326',
      created_at: aoi.createdAt,
      source: {
        filename,
        vertexCount: aoi.vertexCount,
      },
      warnings: parseResult.warnings || [],
    };

    return NextResponse.json(responsePayload, { status: 200 });
  } catch (err: any) {
    console.error('AOI upload endpoint error:', err);
    return NextResponse.json(
      { detail: `Internal AOI processing error: ${err.message || String(err)}` },
      { status: 500 }
    );
  }
}
