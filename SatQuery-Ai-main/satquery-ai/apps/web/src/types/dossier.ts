export interface InspectionDossier {
  id: string;
  name: string;
  date: string; // ISO format 'YYYY-MM-DD'
  time?: string; // e.g. '14:30 UTC'
  missionId: string;
  jobId: string;
  location: string;
  coordinates: { lat: number; lon: number };
  sensors: string;
  modality: 'optical' | 'sar' | 'compound' | 'multispectral';
  task: string;
  status: 'VERIFIED' | 'CALIBRATED' | 'ANALYZED' | 'ARCHIVED';
  confidence: number; // 0 - 100
  utmZone: string;
  areaAoi: string;
  findings: string;
  keyMetrics: {
    label: string;
    value: string;
  }[];
  reportUrls?: {
    pdf: string;
    geojson: string;
    csv: string;
    json: string;
  };
}

export const PREVIOUS_INSPECTION_DOSSIERS: InspectionDossier[] = [
  {
    id: 'DOS-2026-0115-BLR',
    name: 'Compound Multimodal Analysis — Bangalore Corridor',
    date: '2026-01-15',
    time: '11:42 UTC',
    missionId: 'mission_05_compound',
    jobId: 'mission_05_compound',
    location: 'Bangalore Urban Corridor (12.97°N, 77.59°E)',
    coordinates: { lat: 12.9716, lon: 77.5946 },
    sensors: 'Sentinel-2 Optical (10m) + Sentinel-1 SAR C-band',
    modality: 'compound',
    task: 'Temporal Change + Optical & SAR Radar Corroboration',
    status: 'VERIFIED',
    confidence: 94.2,
    utmZone: 'EPSG:32643 (UTM Zone 43N)',
    areaAoi: '12.64 km²',
    findings: 'Built-up surface area increased by +2.56 ha (25,600 m²) with 94% radar corroboration across -14.5 dB SAR backscatter.',
    keyMetrics: [
      { label: 'Area Change', value: '+2.56 ha' },
      { label: 'Radar Corroboration', value: '94.2%' },
      { label: 'SAR Threshold', value: '-14.5 dB' },
      { label: 'Native GSD', value: '10.0 m' },
    ],
    reportUrls: {
      pdf: '/api/v1/reports/mission_05_compound/pdf',
      geojson: '/api/v1/reports/mission_05_compound/geojson',
      csv: '/api/v1/reports/mission_05_compound/csv',
      json: '/api/v1/reports/mission_05_compound/json',
    },
  },
  {
    id: 'DOS-2026-0104-HYD',
    name: 'Hyderabad Urban Corridor & Reservoir Encroachment',
    date: '2026-01-04',
    time: '09:15 UTC',
    missionId: 'mission_06_hyderabad',
    jobId: 'mission_06_hyderabad',
    location: 'Hyderabad Urban Corridor (17.39°N, 78.49°E)',
    coordinates: { lat: 17.385, lon: 78.4867 },
    sensors: 'Sentinel-2 MSI (10m) + Sentinel-1 C-SAR (10m)',
    modality: 'compound',
    task: 'Bi-Temporal Built-Up Expansion & Water Body Dynamics',
    status: 'VERIFIED',
    confidence: 92.8,
    utmZone: 'EPSG:32644 (UTM Zone 44N)',
    areaAoi: '25.00 km²',
    findings: 'Industrial encroachment detected along northwestern water reservoir perimeter (+3.12 ha), cross-verified against C-SAR radar intensity.',
    keyMetrics: [
      { label: 'Encroachment', value: '+3.12 ha' },
      { label: 'Water Contraction', value: '-1.85 ha' },
      { label: 'Concordance', value: '92.8%' },
      { label: 'Sensor Pair', value: 'MSI / C-SAR' },
    ],
    reportUrls: {
      pdf: '/api/v1/reports/mission_06_hyderabad/pdf',
      geojson: '/api/v1/reports/mission_06_hyderabad/geojson',
      csv: '/api/v1/reports/mission_06_hyderabad/csv',
      json: '/api/v1/reports/mission_06_hyderabad/json',
    },
  },
  {
    id: 'DOS-2025-1120-ASM',
    name: 'Assam Valley Visual Grounding & Floodplain Extent',
    date: '2025-11-20',
    time: '14:28 UTC',
    missionId: 'mission_02_grounding',
    jobId: 'mission_02_grounding',
    location: 'Assam Valley (26.20°N, 92.93°E)',
    coordinates: { lat: 26.2006, lon: 92.9376 },
    sensors: 'Sentinel-2 Multi-Spectral (10m GSD)',
    modality: 'multispectral',
    task: 'Text-Guided Referring Expression Localization',
    status: 'CALIBRATED',
    confidence: 96.4,
    utmZone: 'EPSG:32646 (UTM Zone 46N)',
    areaAoi: '18.45 km²',
    findings: 'Primary river channel and braided riverbanks localized with Mean IoU 78.4% and exact 18.45 km² extent.',
    keyMetrics: [
      { label: 'Water Body Area', value: '18.45 km²' },
      { label: 'Mean IoU', value: '78.4%' },
      { label: 'Precision@50', value: '100%' },
      { label: 'GSD Resolution', value: '10m' },
    ],
    reportUrls: {
      pdf: '/api/v1/reports/mission_02_grounding/pdf',
      geojson: '/api/v1/reports/mission_02_grounding/geojson',
      csv: '/api/v1/reports/mission_02_grounding/csv',
      json: '/api/v1/reports/mission_02_grounding/json',
    },
  },
  {
    id: 'DOS-2025-0814-BPH',
    name: 'Brahmaputra Basin Optical + SAR Dual Radar Corroboration',
    date: '2025-08-14',
    time: '06:50 UTC',
    missionId: 'mission_04_opticals_sar',
    jobId: 'mission_04_opticals_sar',
    location: 'Brahmaputra Basin (26.20°N, 92.93°E)',
    coordinates: { lat: 26.2006, lon: 92.9376 },
    sensors: 'Sentinel-1 C-band SAR + Sentinel-2 Optical',
    modality: 'sar',
    task: 'Cross-Modal Decision Concordance & Radar Backscatter',
    status: 'VERIFIED',
    confidence: 95.1,
    utmZone: 'EPSG:32646 (UTM Zone 46N)',
    areaAoi: '15.20 km²',
    findings: 'Cloud-penetrating SAR radar corroborated standing water boundary during heavy monsoon cloud overcast with -16.2 dB backscatter threshold.',
    keyMetrics: [
      { label: 'Concordance', value: '95.1%' },
      { label: 'Cloud Overcast', value: '88% Pct' },
      { label: 'SAR Penetration', value: '100%' },
      { label: 'Threshold', value: '-16.2 dB' },
    ],
    reportUrls: {
      pdf: '/api/v1/reports/mission_04_opticals_sar/pdf',
      geojson: '/api/v1/reports/mission_04_opticals_sar/geojson',
      csv: '/api/v1/reports/mission_04_opticals_sar/csv',
      json: '/api/v1/reports/mission_04_opticals_sar/json',
    },
  },
  {
    id: 'DOS-2024-1002-AMD',
    name: 'Ahmedabad SAC Space Applications Center Land Cover Inspection',
    date: '2024-10-02',
    time: '10:12 UTC',
    missionId: 'mission_01_vqa',
    jobId: 'mission_01_vqa',
    location: 'Ahmedabad (ISRO SAC) (23.02°N, 72.51°E)',
    coordinates: { lat: 23.0225, lon: 72.5085 },
    sensors: 'Sentinel-2 MSI · 10m GSD',
    modality: 'optical',
    task: 'Multi-Spectral Terrain & Land Cover Reasoning',
    status: 'CALIBRATED',
    confidence: 91.5,
    utmZone: 'EPSG:32643 (UTM Zone 43N)',
    areaAoi: '15.80 km²',
    findings: 'Identified major institutional footprints, high-reflectance commercial zones, and urban canopy with BLEU-4 score of 0.74.',
    keyMetrics: [
      { label: 'Land Cover Accuracy', value: '80.0%' },
      { label: 'BLEU-4 Score', value: '0.74' },
      { label: 'NDVI Index', value: '0.48' },
      { label: 'CRS Datum', value: 'WGS84 43N' },
    ],
    reportUrls: {
      pdf: '/api/v1/reports/mission_01_vqa/pdf',
      geojson: '/api/v1/reports/mission_01_vqa/geojson',
      csv: '/api/v1/reports/mission_01_vqa/csv',
      json: '/api/v1/reports/mission_01_vqa/json',
    },
  },
  {
    id: 'DOS-2024-0418-BLR',
    name: 'Bangalore Peri-Urban Bi-Temporal Siamese ChangeNet',
    date: '2024-04-18',
    time: '13:05 UTC',
    missionId: 'mission_03_temporal',
    jobId: 'mission_03_temporal',
    location: 'Bangalore Peri-Urban (12.97°N, 77.59°E)',
    coordinates: { lat: 12.9716, lon: 77.5946 },
    sensors: 'Sentinel-2 Multi-Temporal Pairs (2024 vs 2026)',
    modality: 'optical',
    task: 'Siamese ChangeNet 2D Convolutional Surface Change',
    status: 'VERIFIED',
    confidence: 94.0,
    utmZone: 'EPSG:32643 (UTM Zone 43N)',
    areaAoi: '12.64 km²',
    findings: 'Detected new arterial bypass construction grading and logistics warehouse footprint expansion totaling 2.56 hectares.',
    keyMetrics: [
      { label: 'Changed Ground Area', value: '25,600 m²' },
      { label: 'Hectares Quantified', value: '+2.56 ha' },
      { label: 'Clusters Tracked', value: '3 Active' },
      { label: 'IoU Agreement', value: '89.2%' },
    ],
    reportUrls: {
      pdf: '/api/v1/reports/mission_03_temporal/pdf',
      geojson: '/api/v1/reports/mission_03_temporal/geojson',
      csv: '/api/v1/reports/mission_03_temporal/csv',
      json: '/api/v1/reports/mission_03_temporal/json',
    },
  },
  {
    id: 'DOS-2024-0118-SHR',
    name: 'Sriharikota SDSC Launch Complex Coastal Land Cover',
    date: '2024-01-18',
    time: '08:22 UTC',
    missionId: 'mission_01_vqa',
    jobId: 'mission_01_vqa',
    location: 'Sriharikota (ISRO SDSC) (13.72°N, 80.23°E)',
    coordinates: { lat: 13.7199, lon: 80.2304 },
    sensors: 'Sentinel-2 MSI (10m) + Cartosat Baseline',
    modality: 'optical',
    task: 'Multi-Spectral Coastal & Island Security Monitoring',
    status: 'VERIFIED',
    confidence: 97.1,
    utmZone: 'EPSG:32644 (UTM Zone 44N)',
    areaAoi: '22.10 km²',
    findings: 'Coastal shoreline stability and mangrove vegetation density verified with NDVI 0.62. Launch pad clearance verified.',
    keyMetrics: [
      { label: 'Coastal Stability', value: '100% Stable' },
      { label: 'Mangrove NDVI', value: '0.62' },
      { label: 'Total AOI', value: '22.1 km²' },
      { label: 'Verification', value: 'Calibrated' },
    ],
    reportUrls: {
      pdf: '/api/v1/reports/mission_01_vqa/pdf',
      geojson: '/api/v1/reports/mission_01_vqa/geojson',
      csv: '/api/v1/reports/mission_01_vqa/csv',
      json: '/api/v1/reports/mission_01_vqa/json',
    },
  },
];
