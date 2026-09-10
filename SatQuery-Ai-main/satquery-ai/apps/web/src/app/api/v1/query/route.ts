import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/**
 * TRUTH-LOCK FIX — see TRUTHLOCK_FINDINGS.md at repo root for the full
 * audit this replaces (original fabricated version preserved alongside
 * this file as route.ts.ORIGINAL_FABRICATED.bak for reference).
 *
 * The previous implementation of this route did NOT call a real backend
 * in the common case. It keyword-matched the query text
 * (queryLower.includes('sar'), .includes('water body'), etc.) and
 * returned a fully fabricated analysis: is_real_weights: true, fixed
 * area/confidence numbers (0.94, 0.95, 0.96, 18.45 ha, 42.15 ha...), and
 * a canned natural-language "answer" — with no actual model inference,
 * no actual GIS computation, and no real backend call unless
 * BACKEND_API_URL happened to be set AND reachable. On any failure it
 * silently fell through to the same fabricated payload.
 *
 * This version does exactly one thing: forward the request to the real
 * FastAPI backend. If the backend isn't configured or isn't reachable,
 * it returns a clear, honest "unavailable" response — never a fabricated
 * analysis. The frontend must treat a non-200 / status:"unavailable"
 * response as ABSTAIN, not silently render stale/fake data.
 */

interface QueryPayload {
  query: string;
  image_ids?: string[];
  aoi_id?: string;
  lat?: number;
  lon?: number;
  location_name?: string;
  utm_zone?: string;
  expected_source_image_id?: string;
  source_image_id?: string;
}

export async function POST(req: NextRequest) {
  let payload: QueryPayload;
  try {
    payload = await req.json();
  } catch {
    return NextResponse.json({ status: 'error', detail: 'Invalid JSON body.' }, { status: 400 });
  }

  const backendUrl = process.env.BACKEND_API_URL;
  if (!backendUrl) {
    return NextResponse.json(
      {
        status: 'unavailable',
        reason:
          'BACKEND_API_URL is not configured. No real analysis backend is reachable, ' +
          'so no result can be produced. This is not an error to hide — it is the ' +
          'correct behavior: refuse to fabricate a result.',
        query: payload.query,
        data_class: 'UNAVAILABLE_CAPABILITY',
      },
      { status: 503 }
    );
  }

  try {
    const res = await fetch(`${backendUrl.replace(/\/$/, '')}/api/v1/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(120_000),
    });

    const text = await res.text();
    let data: unknown;
    try {
      data = text.length ? JSON.parse(text) : {};
    } catch {
      // Backend returned something that isn't JSON (e.g. an HTML error
      // page from an auth wall or proxy) — surface that honestly instead
      // of crashing with "Unexpected token '<'" or silently fabricating
      // a result.
      return NextResponse.json(
        {
          status: 'error',
          reason: `Backend returned a non-JSON response (HTTP ${res.status}). This usually ` +
            `means the request hit an auth wall or the wrong path, not that analysis ran.`,
          data_class: 'UNAVAILABLE_CAPABILITY',
        },
        { status: 502 }
      );
    }

    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json(
      {
        status: 'unavailable',
        reason: `Could not reach analysis backend: ${err?.message || 'unknown error'}. ` +
          `Refusing to fabricate a result.`,
        query: payload.query,
        data_class: 'UNAVAILABLE_CAPABILITY',
      },
      { status: 502 }
    );
  }
}
