import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { bbox, collection = 'sentinel-2-l2a' } = body;

    const mockItems = [
      {
        id: 'S2A_MSIL2A_20260319T052218_N0511_R047',
        collection,
        datetime: '2026-03-19T05:22:18Z',
        bbox: bbox || [77.5, 12.85, 77.75, 13.1],
        properties: {
          'eo:cloud_cover': 0.8,
          platform: 'Sentinel-2B',
          instruments: ['MSI'],
          gsd: 10.0,
          proj_epsg: 32643,
        },
        assets: {
          visual: {
            href: '/api/v1/images/opt_t2/preview',
            title: 'True color image (TCI)',
            type: 'image/tiff; application=geotiff; profile=cloud-optimized',
          },
        },
      },
      {
        id: 'S1A_IW_GRDH_1SDV_20260318T124500_R032',
        collection: 'sentinel-1-grd',
        datetime: '2026-03-18T12:45:00Z',
        bbox: bbox || [77.5, 12.85, 77.75, 13.1],
        properties: {
          'sar:polarizations': ['VV', 'VH'],
          platform: 'Sentinel-1A',
          instruments: ['C-SAR'],
          gsd: 10.0,
          proj_epsg: 32643,
        },
        assets: {
          visual: {
            href: '/api/v1/images/sar_s1/preview',
            title: 'SAR Calibrated Backscatter',
            type: 'image/tiff; application=geotiff',
          },
        },
      },
      {
        id: 'S2A_MSIL2A_20240315T052021_N0500_R047',
        collection,
        datetime: '2024-03-15T05:20:21Z',
        bbox: bbox || [77.5, 12.85, 77.75, 13.1],
        properties: {
          'eo:cloud_cover': 1.2,
          platform: 'Sentinel-2A',
          instruments: ['MSI'],
          gsd: 10.0,
          proj_epsg: 32643,
        },
        assets: {
          visual: {
            href: '/api/v1/images/opt_t1/preview',
            title: 'Historical Baseline (T1)',
            type: 'image/tiff; application=geotiff; profile=cloud-optimized',
          },
        },
      },
    ];

    return NextResponse.json({
      type: 'FeatureCollection',
      features: mockItems.map((item) => ({
        type: 'Feature',
        id: item.id,
        bbox: item.bbox,
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [item.bbox[0], item.bbox[1]],
              [item.bbox[2], item.bbox[1]],
              [item.bbox[2], item.bbox[3]],
              [item.bbox[0], item.bbox[3]],
              [item.bbox[0], item.bbox[1]],
            ],
          ],
        },
        properties: item.properties,
        assets: item.assets,
      })),
      context: {
        returned: mockItems.length,
        limit: 10,
        matched: mockItems.length,
      },
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || 'STAC search failed' }, { status: 500 });
  }
}
