import { NextResponse } from 'next/server';

interface SearchSuggestion {
  id: string;
  type: 'mission' | 'report' | 'coordinate' | 'stac' | 'finding';
  title: string;
  subtitle: string;
  badge: string;
  data: any;
}

const CANONICAL_MISSIONS_DATA = [
  {
    id: 'mission_05_compound',
    tag: 'MISSION 05 ★',
    name: 'Compound Multimodal Analysis (Grand Showcase)',
    location: 'Bangalore Urban Corridor (12.97°N, 77.59°E)',
    lat: 12.9716,
    lon: 77.5946,
    sensors: 'Sentinel-2 Optical (10m) + Sentinel-1 SAR C-band',
    keywords: ['bangalore', 'compound', 'multimodal', 'sar', 'radar', 'built-up', '12.97', '77.59'],
  },
  {
    id: 'mission_06_hyderabad',
    tag: 'MISSION 06',
    name: 'Hyderabad Urban Corridor & Lake Basin',
    location: 'Hyderabad Urban Corridor (17.39°N, 78.49°E)',
    lat: 17.3850,
    lon: 78.4867,
    sensors: 'Sentinel-2 MSI (10m) + Sentinel-1 C-SAR (10m)',
    keywords: ['hyderabad', 'urban', 'lake', 'industrial', 'hitec', '17.38', '78.48'],
  },
  {
    id: 'mission_01_vqa',
    tag: 'MISSION 01',
    name: 'Single-Image RS-VQA (Land Cover)',
    location: 'Karnataka (12.97°N, 77.59°E)',
    lat: 12.9716,
    lon: 77.5946,
    sensors: 'Sentinel-2 MSI · 10m GSD',
    keywords: ['vqa', 'land cover', 'karnataka', 'transport', 'corridor'],
  },
  {
    id: 'mission_02_grounding',
    tag: 'MISSION 02',
    name: 'Visual Grounding & Metric Area',
    location: 'Assam Valley (26.20°N, 92.93°E)',
    lat: 26.2006,
    lon: 92.9376,
    sensors: 'Sentinel-2 Multi-Spectral (10m GSD)',
    keywords: ['assam', 'grounding', 'floodplain', 'river', 'water body', 'brahmaputra'],
  },
  {
    id: 'mission_03_temporal',
    tag: 'MISSION 03',
    name: 'Bi-Temporal Change Detection',
    location: 'Bangalore Peri-Urban (12.97°N, 77.59°E)',
    lat: 12.9716,
    lon: 77.5946,
    sensors: 'Sentinel-2 Multi-Temporal Pairs (2024 vs 2026)',
    keywords: ['temporal', 'changenet', 'change detection', 'peri-urban', 'expansion'],
  },
  {
    id: 'mission_04_opticals_sar',
    tag: 'MISSION 04',
    name: 'Optical + SAR Corroboration',
    location: 'Brahmaputra Basin (26.20°N, 92.93°E)',
    lat: 26.2006,
    lon: 92.9376,
    sensors: 'Sentinel-1 C-band SAR + Sentinel-2 Optical',
    keywords: ['sar', 'radar', 'backscatter', 'brahmaputra', 'corroboration'],
  },
];

const REPORTS_DATA = [
  {
    id: 'report_golden_mission_5',
    title: 'Mission 05 Golden Benchmark Audit Dossier',
    subtitle: 'Compound ChangeNet 2D CNN (IoU 0.842) · 1.82 ha expansion verified',
    badge: 'REPORT',
    keywords: ['report', 'dossier', 'audit', 'benchmark', 'iou', 'verification', 'golden'],
  },
  {
    id: 'report_hyderabad_expansion',
    title: 'Hyderabad Industrial Corridor Bi-Temporal Analysis',
    subtitle: 'Surface Infrastructure Growth (2024–2026) · Sentinel-1 Radar Confirmed',
    badge: 'REPORT',
    keywords: ['hyderabad', 'industrial', 'growth', 'report', 'audit', 'infrastructure'],
  },
  {
    id: 'report_assam_floodplain',
    title: 'Brahmaputra River Basin Hydrological & Land Cover Report',
    subtitle: 'NDWI Inundation Dynamics · Sentinel-2 MSI Multi-Band Matrix',
    badge: 'REPORT',
    keywords: ['assam', 'brahmaputra', 'hydrological', 'ndwi', 'floodplain', 'water'],
  },
];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = (searchParams.get('q') || '').trim();

  if (!q) {
    return NextResponse.json({ query: '', suggestions: [] });
  }

  const queryLower = q.toLowerCase();
  const suggestions: SearchSuggestion[] = [];

  // 1. Check if user typed coordinates (e.g., "17.385, 78.486" or "12.97 77.59")
  const coordMatch = q.match(/^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$/);
  if (coordMatch) {
    const lat = parseFloat(coordMatch[1]);
    const lon = parseFloat(coordMatch[2]);
    if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
      suggestions.push({
        id: `coord_${lat}_${lon}`,
        type: 'coordinate',
        title: `Navigate to (${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E)`,
        subtitle: `Geodetic WGS84 EPSG:4326 · UTM Zone ${Math.floor((lon + 180) / 6) + 1}`,
        badge: 'GEO COORD',
        data: { lat, lon },
      });
    }
  }

  // 2. Search Missions
  for (const m of CANONICAL_MISSIONS_DATA) {
    const isMatch =
      m.id.toLowerCase().includes(queryLower) ||
      m.tag.toLowerCase().includes(queryLower) ||
      m.name.toLowerCase().includes(queryLower) ||
      m.location.toLowerCase().includes(queryLower) ||
      m.keywords.some((k) => k.includes(queryLower));

    if (isMatch) {
      suggestions.push({
        id: m.id,
        type: 'mission',
        title: `${m.tag} — ${m.name}`,
        subtitle: `${m.location} · ${m.sensors}`,
        badge: 'MISSION',
        data: m,
      });
    }
  }

  // 3. Search Reports
  for (const r of REPORTS_DATA) {
    const isMatch =
      r.title.toLowerCase().includes(queryLower) ||
      r.subtitle.toLowerCase().includes(queryLower) ||
      r.keywords.some((k) => k.includes(queryLower));

    if (isMatch) {
      suggestions.push({
        id: r.id,
        type: 'report',
        title: r.title,
        subtitle: r.subtitle,
        badge: 'REPORT',
        data: r,
      });
    }
  }

  // 4. STAC Sentinel scene suggestions
  if (queryLower.includes('sentinel') || queryLower.includes('stac') || queryLower.includes('s2') || queryLower.includes('s1')) {
    suggestions.push({
      id: 'stac_s2_l2a',
      type: 'stac',
      title: 'Sentinel-2 MSI Level-2A BOA Catalog',
      subtitle: '10m GSD Multi-Spectral BOA Surface Reflectance Collection',
      badge: 'STAC',
      data: { collection: 'sentinel-2-l2a' },
    });
    suggestions.push({
      id: 'stac_s1_grd',
      type: 'stac',
      title: 'Sentinel-1 C-SAR IW GRDH Catalog',
      subtitle: '10m C-band Microwave Radar Backscatter (VV/VH Polarization)',
      badge: 'STAC',
      data: { collection: 'sentinel-1-grd' },
    });
  }

  return NextResponse.json({
    query: q,
    count: suggestions.length,
    suggestions: suggestions.slice(0, 8),
  });
}
