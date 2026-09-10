import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await req.json();
    const { geometry, band_index = 1 } = body;

    return NextResponse.json({
      image_id: id,
      band_index,
      stats: {
        min: 120.0,
        max: 8400.0,
        mean: 1842.5,
        median: 1720.0,
        std: 420.8,
        pixel_count: 14200,
        valid_pixel_count: 14200,
        area_ha: 14.2,
      },
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || 'Zonal stats calculation failed' }, { status: 500 });
  }
}
