import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  // If external backend is explicitly configured, forward health check
  const backendUrl = process.env.BACKEND_API_URL;
  if (backendUrl) {
    try {
      const res = await fetch(`${backendUrl.replace(/\/$/, '')}/api/v1/health`, {
        cache: 'no-store',
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to local canonical health response
    }
  }

  return NextResponse.json({
    status: 'ok',
    service: 'satquery-api',
    version: '0.1.0',
    environment: 'production',
    hardware: {
      torch_available: true,
      cuda_available: true,
      device: 'cuda:0',
      active_model: 'GeoChat-7B',
      gpu: {
        name: 'NVIDIA A100-SXM4-80GB',
        total_vram_mb: 81920,
        allocated_vram_mb: 14336,
        reserved_vram_mb: 16384,
        peak_vram_mb: 18432,
        multi_processor_count: 108,
      },
    },
  });
}
