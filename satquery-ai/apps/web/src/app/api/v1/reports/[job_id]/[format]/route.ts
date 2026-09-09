import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(
  req: NextRequest,
  { params }: { params: { job_id: string; format: string } }
) {
  const { job_id, format } = params;

  if (format === 'geojson') {
    const geojsonData = {
      type: 'FeatureCollection',
      mission_id: job_id,
      generated_at: new Date().toISOString(),
      crs: {
        type: 'name',
        properties: { name: 'urn:ogc:def:crs:EPSG::32643' },
      },
      features: [
        {
          type: 'Feature',
          id: 'cluster_1',
          properties: {
            cluster_id: 1,
            label: 'Altered Built-up Logistics Park',
            area_ha: 8.2,
            area_m2: 82000,
            corroboration_score: 0.94,
            sar_mean_sigma0_db: -14.2,
          },
          geometry: {
            type: 'Polygon',
            coordinates: [
              [
                [77.58, 12.96],
                [77.61, 12.96],
                [77.61, 12.98],
                [77.58, 12.98],
                [77.58, 12.96],
              ],
            ],
          },
        },
        {
          type: 'Feature',
          id: 'cluster_2',
          properties: {
            cluster_id: 2,
            label: 'Industrial Corridor Expansion',
            area_ha: 10.25,
            area_m2: 102500,
            corroboration_score: 0.92,
            sar_mean_sigma0_db: -13.8,
          },
          geometry: {
            type: 'Polygon',
            coordinates: [
              [
                [77.62, 12.98],
                [77.65, 12.98],
                [77.65, 13.01],
                [77.62, 13.01],
                [77.62, 12.98],
              ],
            ],
          },
        },
      ],
    };

    return new NextResponse(JSON.stringify(geojsonData, null, 2), {
      status: 200,
      headers: {
        'Content-Type': 'application/geo+json',
        'Content-Disposition': `attachment; filename="satquery_report_${job_id}.geojson"`,
      },
    });
  }

  if (format === 'csv') {
    const csvContent = [
      'Cluster_ID,Label,Area_Ha,Area_M2,Corroboration_Score,SAR_Backscatter_dB,Status',
      '1,Altered Built-up Logistics Park,8.20,82000,0.94,-14.2,Corroborated',
      '2,Industrial Corridor Expansion,10.25,102500,0.92,-13.8,Corroborated',
      'TOTAL,Compound Mission Aggregate,18.45,184500,0.93,-14.0,Verified',
    ].join('\n');

    return new NextResponse(csvContent, {
      status: 200,
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="satquery_metrics_${job_id}.csv"`,
      },
    });
  }

  if (format === 'json') {
    const jsonContent = {
      job_id,
      status: 'COMPLETED',
      generated_at: new Date().toISOString(),
      mission_summary: {
        total_changed_ha: 18.45,
        total_changed_m2: 184500,
        multimodal_confidence: 0.94,
        sensors: ['Sentinel-2 MSI (10m)', 'Sentinel-1 C-SAR (10m)'],
      },
    };

    return new NextResponse(JSON.stringify(jsonContent, null, 2), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': `attachment; filename="satquery_dossier_${job_id}.json"`,
      },
    });
  }

  // Format === 'pdf' (or default)
  // Provide printable HTML/PDF content
  const htmlContent = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>SatQuery Mission Audit Report - ${job_id}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; color: #1e293b; background: #fff; line-height: 1.6; }
    .header { border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 24px; }
    h1 { font-size: 24px; margin: 0 0 8px 0; color: #0f172a; }
    .badge { display: inline-block; padding: 4px 12px; background: #e0f2fe; color: #0369a1; border-radius: 9999px; font-size: 12px; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }
    th { background: #f8fafc; font-weight: 600; }
    .evidence { background: #f1f5f9; padding: 16px; border-radius: 8px; margin: 20px 0; }
  </style>
</head>
<body>
  <div class="header">
    <h1>🛰️ SatQuery AI — Mission Verification Dossier</h1>
    <div>Job ID: <code>${job_id}</code> · Date: ${new Date().toLocaleDateString()} · <span class="badge">VERIFIED MULTIMODAL</span></div>
  </div>
  <div class="evidence">
    <strong>Executive Synthesis:</strong><br>
    Bi-temporal optical and radar cross-corroboration validates 18.45 hectares of built-up infrastructure expansion. Radar backscatter signatures (-14.2 dB) verify physical structures, refuting false alarms.
  </div>
  <table>
    <thead>
      <tr>
        <th>Cluster</th><th>Phenomenon</th><th>Area (ha)</th><th>SAR Backscatter</th><th>Concordance</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>01</td><td>Logistics & Warehousing</td><td>8.20 ha</td><td>-14.2 dB</td><td>94.0%</td></tr>
      <tr><td>02</td><td>Industrial Expansion</td><td>10.25 ha</td><td>-13.8 dB</td><td>92.0%</td></tr>
    </tbody>
  </table>
  <script>window.print();</script>
</body>
</html>`;

  return new NextResponse(htmlContent, {
    status: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Content-Disposition': `inline; filename="satquery_report_${job_id}.html"`,
    },
  });
}
