import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/**
 * TRUTH-LOCK FIX — see TRUTHLOCK_FINDINGS.md at repo root.
 *
 * The previous implementation always returned the same two hardcoded
 * change clusters (8.2 ha + 10.25 ha = 18.45 ha total, is_trained: true,
 * "Siamese 2D convolutional difference network converged at 95.2% F1
 * score") for EVERY request, regardless of which images were compared.
 *
 * Per backend/agent/change_contract.py's fail-closed contract: when
 * ChangeNet isn't verified/READY, the result must be labeled
 * "classical_rgb_change_fallback", never attributed to ChangeNet, and
 * must never claim is_trained: true without a verified checkpoint. This
 * route now proxies to the real backend or fails closed — it no longer
 * invents change clusters.
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
        image_before_id: body?.image_before_id ?? null,
        image_after_id: body?.image_after_id ?? null,
        change_percent: null,
        total_area_ha: null,
        regions_geojson: { type: 'FeatureCollection', features: [] },
        model_name: 'classical_rgb_change_fallback',
        is_trained: false,
        fallback_used: true,
        data_class: 'UNAVAILABLE_CAPABILITY',
        reason: 'BACKEND_API_URL not configured; no real change-detection backend is reachable.',
      },
      { status: 503 }
    );
  }

  try {
    const res = await fetch(`${backendUrl.replace(/\/$/, '')}/api/v1/analysis/change`, {
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
        model_name: 'classical_rgb_change_fallback',
        is_trained: false,
        fallback_used: true,
        data_class: 'UNAVAILABLE_CAPABILITY',
        reason: `Could not reach change-detection backend: ${err?.message || 'unknown error'}.`,
      },
      { status: 502 }
    );
  }
}
