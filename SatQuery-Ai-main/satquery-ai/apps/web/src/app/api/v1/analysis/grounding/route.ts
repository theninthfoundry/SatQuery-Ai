import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/**
 * TRUTH-LOCK FIX — see TRUTHLOCK_FINDINGS.md at repo root.
 *
 * The previous implementation always returned a single hardcoded
 * grounding feature ("Primary River Channel & Water Basin", 421500 m²,
 * confidence 0.96, a fixed WGS84 polygon over the Brahmaputra) for EVERY
 * request, regardless of image_id or referring_expression. No model ran.
 *
 * Per the project's own grounding fail-closed contract
 * (backend/agent/grounding_contract.py — offline_fallback_grounding),
 * an unavailable model must return boxes: [], confidence: null,
 * fallback: true — never a plausible-looking box. This route now mirrors
 * that contract: proxy to the real backend, or fail closed.
 */

export async function POST(req: NextRequest) {
  let body: any;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ status: 'error', detail: 'Invalid JSON body.' }, { status: 400 });
  }

  const backendUrl = process.env.BACKEND_API_URL;
  if (!backendUrl) {
    return NextResponse.json(
      {
        job_id: null,
        image_id: body?.image_id ?? null,
        referring_expression: body?.referring_expression ?? null,
        regions_geojson: { type: 'FeatureCollection', features: [] },
        total_area_m2: null,
        confidence: null,
        fallback_used: true,
        execution_mode: 'offline_fallback',
        data_class: 'UNAVAILABLE_CAPABILITY',
        reason: 'BACKEND_API_URL not configured; no real grounding model is reachable.',
      },
      { status: 503 }
    );
  }

  try {
    const res = await fetch(`${backendUrl.replace(/\/$/, '')}/api/v1/analysis/grounding`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60_000),
    });
    const text = await res.text();
    let data: unknown;
    try {
      data = text.length ? JSON.parse(text) : {};
    } catch {
      return NextResponse.json(
        { status: 'error', reason: `Backend returned non-JSON (HTTP ${res.status}).`, data_class: 'UNAVAILABLE_CAPABILITY' },
        { status: 502 }
      );
    }
    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json(
      {
        regions_geojson: { type: 'FeatureCollection', features: [] },
        confidence: null,
        fallback_used: true,
        execution_mode: 'offline_fallback',
        data_class: 'UNAVAILABLE_CAPABILITY',
        reason: `Could not reach grounding backend: ${err?.message || 'unknown error'}.`,
      },
      { status: 502 }
    );
  }
}
