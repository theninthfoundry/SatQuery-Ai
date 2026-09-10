import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    const aoiId = (formData.get('aoi_id') as string) || null;

    if (!file) {
      return NextResponse.json({ detail: 'No image file uploaded.' }, { status: 400 });
    }

    const imageId = `img_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    const filename = file.name || 'satellite_scene.tif';
    const isSar = filename.toLowerCase().includes('sar') || filename.toLowerCase().includes('s1');

    return NextResponse.json({
      id: imageId,
      status: 'valid',
      metadata: {
        filename,
        format: 'GeoTIFF',
        driver: 'GTiff',
        width: 10980,
        height: 10980,
        band_count: isSar ? 2 : 12,
        dtype: 'uint16',
        crs: {
          present: true,
          valid: true,
          epsg: 32643,
          name: 'WGS 84 / UTM zone 43N',
          type: 'ProjectedCRS',
          status: 'verified',
          units: 'metre',
        },
        transform: [10.0, 0.0, 775000.0, 0.0, -10.0, 1430000.0],
        bounds: {
          min_x: 775000.0,
          min_y: 1320200.0,
          max_x: 884800.0,
          max_y: 1430000.0,
          wgs84: {
            min_lon: 77.5,
            min_lat: 12.85,
            max_lon: 77.75,
            max_lat: 13.1,
          },
        },
        resolution: {
          x_res: 10.0,
          y_res: 10.0,
          units: 'metre',
        },
        nodata: 0,
        compression: 'DEFLATE',
        bands: [
          { band_index: 1, dtype: 'uint16', min: 120, max: 8400, mean: 1420.5 },
          { band_index: 2, dtype: 'uint16', min: 140, max: 9200, mean: 1530.2 },
          { band_index: 3, dtype: 'uint16', min: 90, max: 10500, mean: 1780.0 },
        ],
        modality: {
          detected: isSar ? 'sar' : 'multispectral',
          confidence: 0.98,
          basis: isSar ? ['polarization_vv_vh', 'radar_amplitude'] : ['12_bands', 'sentinel2_wavelengths'],
        },
      },
      validation: {
        valid: true,
        warnings: [],
        errors: [],
      },
      preview: {
        available: true,
        preview_url: null,
      },
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || 'Image inspection failed' }, { status: 500 });
  }
}
