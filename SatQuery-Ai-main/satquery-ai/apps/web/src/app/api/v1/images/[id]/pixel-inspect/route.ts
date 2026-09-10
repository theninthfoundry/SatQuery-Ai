import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await req.json();
    const { lat, lon, compare_image_id } = body;

    return NextResponse.json({
      image_id: id,
      lat: lat ?? 12.9716,
      lon: lon ?? 77.5946,
      pixel: { x: 5490, y: 5490 },
      values: {
        B02_blue: 1420,
        B03_green: 1680,
        B04_red: 1890,
        B08_nir: 3450,
        ndvi: 0.29,
        ndwi: -0.34,
      },
      sar_backscatter_db: -14.2,
      corroboration: 'Strong double-bounce scattering consistent with commercial structures.',
      compare_result: compare_image_id
        ? {
            compare_image_id,
            difference_magnitude: 0.42,
            significant_change: true,
          }
        : null,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || 'Pixel inspect failed' }, { status: 500 });
  }
}
