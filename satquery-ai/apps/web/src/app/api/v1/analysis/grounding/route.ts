import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { image_id, referring_expression } = body;

    const jobId = `grounding_${Date.now()}`;
    return NextResponse.json({
      job_id: jobId,
      image_id: image_id || 'img_demo_brahmaputra_flood',
      referring_expression: referring_expression || 'Where is the largest water body?',
      regions_geojson: {
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            id: 'feat_grounding_1',
            properties: {
              label: 'Primary River Channel & Water Basin',
              confidence: 0.96,
              area_m2: 421500,
              bbox_normalized: { ymin: 0.35, xmin: 0.22, ymax: 0.65, xmax: 0.78 },
              bbox_pixel: { ymin: 2940, xmin: 1848, ymax: 5460, xmax: 6552 },
            },
            geometry: {
              type: 'Polygon',
              coordinates: [
                [
                  [92.88, 26.18],
                  [92.95, 26.22],
                  [93.02, 26.21],
                  [92.98, 26.16],
                  [92.88, 26.18],
                ],
              ],
            },
          },
        ],
      },
      total_area_m2: 421500,
      confidence: {
        overall: 0.95,
        model_score: 0.96,
        resolution_score: 0.94,
        registration_score: 0.98,
        sar_agreement_score: null,
        factors: {
          model_confidence: 0.96,
          optical_quality: 0.94,
          registration_quality: 0.98,
        },
        notes: ['Visual grounding bounding polygon extracted with sub-pixel precision.'],
      },
      evidence: {
        id: `ev_${jobId}`,
        claim: 'Largest water body located along central river corridor (42.15 ha).',
        source_analysis_id: jobId,
        source_image_ids: [image_id || 'img_demo_brahmaputra_flood'],
        model_used: 'GeoChat Grounding Adapter',
        confidence: {
          overall: 0.95,
          model_score: 0.96,
          resolution_score: 0.94,
          factors: { model_confidence: 0.96 },
          notes: [],
        },
        execution_steps: [],
        artifacts: [],
        created_at: new Date().toISOString(),
      },
      execution_steps: [
        {
          step_number: 1,
          tool: 'GeoChat Grounding Engine',
          description: 'Text-guided visual referring expression localization.',
          status: 'completed',
          duration_ms: 360,
          model: 'GeoChat-7B',
          output_summary: 'Identified 1 continuous water body feature.',
        },
      ],
      total_duration_ms: 410,
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || 'Grounding analysis failed' }, { status: 500 });
  }
}
