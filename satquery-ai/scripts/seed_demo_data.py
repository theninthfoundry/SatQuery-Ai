"""Seed realistic ISRO demonstration scenarios for offline standalone operation."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord, AOIRecord
from backend.geospatial.metadata import extract_raster_metadata
from backend.storage.preview import generate_preview
from tests.fixtures.synthetic_raster import create_synthetic_multiband_geotiff
from tests.fixtures.synthetic_bitemporal import create_synthetic_bitemporal_pair
from tests.fixtures.synthetic_optical_sar import create_synthetic_optical_sar_pair


def seed_demo_scenarios():
    """Generate and ingest 3 canonical ISRO demonstration scenarios into the database."""
    print("🛰️  Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = next(get_db())

    demo_dir = Path("./data/demo")
    demo_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create Default AOI
    aoi = db.get(AOIRecord, "aoi_demo_isro")
    if not aoi:
        aoi = AOIRecord(
            id="aoi_demo_isro",
            name="Ahmedabad & Gujarat Coastal AOI (SAC/ISRO Demo)",
            description="Canonical demonstration region covering Sabarmati river basin and coastal corridor.",
            geometry_geojson={
                "type": "Polygon",
                "coordinates": [[[72.50, 23.00], [72.65, 23.00], [72.65, 23.10], [72.50, 23.10], [72.50, 23.00]]],
            },
        )
        db.add(aoi)
        db.commit()
        print("✅ Seeded AOI: Ahmedabad & Gujarat Coastal AOI")

    # 2. Scenario 1: High-Resolution Optical Scene (VQA & Grounding)
    scene1_path = demo_dir / "scene_optical_ahmedabad.tif"
    create_synthetic_multiband_geotiff(scene1_path, width=128, height=128, bands=4, epsg=32643)
    meta1 = extract_raster_metadata(scene1_path)
    prev1 = Path(settings.preview_dir) / "demo_scene1_prev.png"
    generate_preview(scene1_path, prev1)

    img1 = db.get(ImageRecord, "img_demo_optical_1") or ImageRecord(
        id="img_demo_optical_1",
        aoi_id="aoi_demo_isro",
        filename="scene_optical_ahmedabad.tif",
        path=str(scene1_path),
        preview_path=f"/api/v1/images/img_demo_optical_1/preview",
        format="GTiff",
        width=128,
        height=128,
        band_count=4,
        dtype="uint8",
        crs=meta1.crs.name,
        epsg=meta1.crs.epsg,
        bounds=meta1.bounds.wgs84.__dict__ if meta1.bounds and meta1.bounds.wgs84 else None,
        resolution=meta1.resolution.__dict__ if meta1.resolution else None,
        modality=meta1.modality.detected,
        metadata_json=meta1.to_dict(),
        is_valid=True,
    )
    db.merge(img1)
    print("✅ Seeded Scenario 1: High-Resolution Optical Scene (img_demo_optical_1)")

    # 3. Scenario 2: Bi-Temporal Change Pair (Before & After)
    before_path, after_path = create_synthetic_bitemporal_pair(demo_dir, width=128, height=128, change_box_size=32)
    meta_b = extract_raster_metadata(before_path)
    meta_a = extract_raster_metadata(after_path)
    prev_b = Path(settings.preview_dir) / "demo_before_prev.png"
    prev_a = Path(settings.preview_dir) / "demo_after_prev.png"
    generate_preview(before_path, prev_b)
    generate_preview(after_path, prev_a)

    img_b = db.get(ImageRecord, "img_demo_bitemporal_t1") or ImageRecord(
        id="img_demo_bitemporal_t1",
        aoi_id="aoi_demo_isro",
        filename="bitemporal_before_t1.tif",
        path=str(before_path),
        preview_path=f"/api/v1/images/img_demo_bitemporal_t1/preview",
        format="GTiff",
        width=128,
        height=128,
        band_count=3,
        dtype="uint8",
        crs=meta_b.crs.name,
        epsg=meta_b.crs.epsg,
        bounds=meta_b.bounds.wgs84.__dict__ if meta_b.bounds and meta_b.bounds.wgs84 else None,
        resolution=meta_b.resolution.__dict__ if meta_b.resolution else None,
        modality=meta_b.modality.detected,
        metadata_json=meta_b.to_dict(),
        is_valid=True,
    )
    img_a = db.get(ImageRecord, "img_demo_bitemporal_t2") or ImageRecord(
        id="img_demo_bitemporal_t2",
        aoi_id="aoi_demo_isro",
        filename="bitemporal_after_t2.tif",
        path=str(after_path),
        preview_path=f"/api/v1/images/img_demo_bitemporal_t2/preview",
        format="GTiff",
        width=128,
        height=128,
        band_count=3,
        dtype="uint8",
        crs=meta_a.crs.name,
        epsg=meta_a.crs.epsg,
        bounds=meta_a.bounds.wgs84.__dict__ if meta_a.bounds and meta_a.bounds.wgs84 else None,
        resolution=meta_a.resolution.__dict__ if meta_a.resolution else None,
        modality=meta_a.modality.detected,
        metadata_json=meta_a.to_dict(),
        is_valid=True,
    )
    db.merge(img_b)
    db.merge(img_a)
    print("✅ Seeded Scenario 2: Bi-Temporal Change Detection Pair (img_demo_bitemporal_t1 & t2)")

    # 4. Scenario 3: Co-registered Optical + SAR Pair
    opt_path, sar_path = create_synthetic_optical_sar_pair(demo_dir, width=128, height=128)
    meta_opt = extract_raster_metadata(opt_path)
    meta_sar = extract_raster_metadata(sar_path)
    prev_opt = Path(settings.preview_dir) / "demo_opt_prev.png"
    prev_sar = Path(settings.preview_dir) / "demo_sar_prev.png"
    generate_preview(opt_path, prev_opt)
    generate_preview(sar_path, prev_sar)

    img_opt = db.get(ImageRecord, "img_demo_sentinel2_optical") or ImageRecord(
        id="img_demo_sentinel2_optical",
        aoi_id="aoi_demo_isro",
        filename="sentinel2_optical_coastal.tif",
        path=str(opt_path),
        preview_path=f"/api/v1/images/img_demo_sentinel2_optical/preview",
        format="GTiff",
        width=128,
        height=128,
        band_count=3,
        dtype="uint8",
        crs=meta_opt.crs.name,
        epsg=meta_opt.crs.epsg,
        bounds=meta_opt.bounds.wgs84.__dict__ if meta_opt.bounds and meta_opt.bounds.wgs84 else None,
        resolution=meta_opt.resolution.__dict__ if meta_opt.resolution else None,
        modality="optical",
        metadata_json=meta_opt.to_dict(),
        is_valid=True,
    )
    img_sar = db.get(ImageRecord, "img_demo_sentinel1_sar") or ImageRecord(
        id="img_demo_sentinel1_sar",
        aoi_id="aoi_demo_isro",
        filename="sentinel1_sar_coastal.tif",
        path=str(sar_path),
        preview_path=f"/api/v1/images/img_demo_sentinel1_sar/preview",
        format="GTiff",
        width=128,
        height=128,
        band_count=1,
        dtype="float32",
        crs=meta_sar.crs.name,
        epsg=meta_sar.crs.epsg,
        bounds=meta_sar.bounds.wgs84.__dict__ if meta_sar.bounds and meta_sar.bounds.wgs84 else None,
        resolution=meta_sar.resolution.__dict__ if meta_sar.resolution else None,
        modality="sar",
        metadata_json=meta_sar.to_dict(),
        is_valid=True,
    )
    db.merge(img_opt)
    db.merge(img_sar)
    print("✅ Seeded Scenario 3: Co-registered Optical + SAR Pair (img_demo_sentinel2_optical & sentinel1_sar)")

    db.commit()
    print("\n🚀 All 3 ISRO Demonstration Scenarios Successfully Seeded!")


if __name__ == "__main__":
    seed_demo_scenarios()
