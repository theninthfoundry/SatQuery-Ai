"""
scripts/seed_demo_data.py

Generates 3 synthetic-but-geospatially-valid GeoTIFFs matching the
README's demo missions:
  1. Ahmedabad single-image optical scene (VQA + grounding demo -- a
     bright synthetic "reservoir" blob to ground).
  2. Urban-expansion T1/T2 pair (built-up growth in the SE quadrant
     between the two dates, for the change-detection golden mission).
  3. Co-registered optical + SAR pair (water = low optical brightness +
     low SAR backscatter; built-up = high optical + high SAR).

These are synthetic rasters with real, valid affine geotransforms and a
real EPSG CRS -- the geospatial engine's area math is exercised exactly
as it would be on real Sentinel-1/2 or Cartosat/RISAT scenes. They are
NOT claimed to be real satellite imagery anywhere in the pipeline.

Requires: rasterio, numpy.
"""
from pathlib import Path
import numpy as np

try:
    import rasterio
    from rasterio.transform import from_origin
except ImportError as e:
    raise SystemExit(
        "rasterio is required to seed demo data. Install with:\n"
        "  pip install rasterio numpy\n"
        f"(import error: {e})"
    )

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "demo"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Ahmedabad, India approx bounds -- used purely to seed a plausible
# geotransform / UTM zone (43N), not as a claim of real imagery.
AHMEDABAD_LON, AHMEDABAD_LAT = 72.5714, 23.0225
GSD_DEG = 0.00009  # roughly 10m at this latitude


def _write_geotiff(path: Path, arr: np.ndarray, origin_lon: float, origin_lat: float, gsd_deg: float,
                    band_names=None):
    """arr: (bands, H, W) uint16."""
    bands, h, w = arr.shape
    transform = from_origin(origin_lon, origin_lat, gsd_deg, gsd_deg)
    with rasterio.open(
        path, "w", driver="GTiff", height=h, width=w, count=bands,
        dtype=arr.dtype, crs="EPSG:4326", transform=transform,
    ) as dst:
        for i in range(bands):
            dst.write(arr[i], i + 1)
            if band_names:
                dst.set_band_description(i + 1, band_names[i])
    print(f"  wrote {path} ({w}x{h}, {bands} bands)")


def _base_scene(h=512, w=512, seed=0):
    rng = np.random.default_rng(seed)
    blue = rng.integers(1800, 2400, (h, w), dtype=np.uint16)
    green = rng.integers(1900, 2500, (h, w), dtype=np.uint16)
    red = rng.integers(1700, 2300, (h, w), dtype=np.uint16)
    nir = rng.integers(2500, 3800, (h, w), dtype=np.uint16)  # vegetation baseline
    return np.stack([blue, green, red, nir]).astype(np.uint16)


def seed_mission1_optical(h=512, w=512):
    print("Mission 1: Ahmedabad single-image optical scene")
    arr = _base_scene(h, w, seed=1)
    # carve a bright, low-NIR "reservoir" blob for grounding demo
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx, r = int(h * 0.35), int(w * 0.6), 60
    blob = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
    arr[1][blob] = 3200   # high green
    arr[3][blob] = 900    # low NIR -> strong NDWI water signal
    _write_geotiff(OUT_DIR / "mission1_ahmedabad_optical.tif", arr,
                    AHMEDABAD_LON, AHMEDABAD_LAT, GSD_DEG,
                    band_names=["blue", "green", "red", "nir"])


def seed_mission2_urban_change(h=512, w=512):
    print("Mission 2: Urban expansion T1/T2 pair")
    t1 = _base_scene(h, w, seed=2)
    t2 = t1.copy()
    # grow "built-up" (high NDBI-proxy: high NIR/red delta, low veg) in the
    # SE quadrant between T1 and T2, in two distinct clusters
    yy, xx = np.mgrid[0:h, 0:w]
    for (cy, cx, r) in [(int(h * 0.72), int(w * 0.68), 45), (int(h * 0.8), int(w * 0.4), 30)]:
        blob = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
        t2[0][blob] = 3600
        t2[1][blob] = 3400
        t2[2][blob] = 3500
        t2[3][blob] = 1600  # built-up: lower NIR than vegetation
    _write_geotiff(OUT_DIR / "mission2_urban_t1_2024.tif", t1,
                    AHMEDABAD_LON, AHMEDABAD_LAT, GSD_DEG,
                    band_names=["blue", "green", "red", "nir"])
    _write_geotiff(OUT_DIR / "mission2_urban_t2_2026.tif", t2,
                    AHMEDABAD_LON, AHMEDABAD_LAT, GSD_DEG,
                    band_names=["blue", "green", "red", "nir"])


def seed_mission3_optical_sar(h=512, w=512):
    print("Mission 3: Co-registered optical + SAR pair")
    optical = _base_scene(h, w, seed=3)
    yy, xx = np.mgrid[0:h, 0:w]

    # water body: low optical NIR, will get low SAR backscatter too
    cy, cx, r = int(h * 0.3), int(w * 0.3), 55
    water_blob = (yy - cy) ** 2 + (xx - cx) ** 2 <= r ** 2
    optical[1][water_blob] = 3100
    optical[3][water_blob] = 800

    # built-up block: high optical brightness, will get high SAR backscatter
    y0, y1, x0, x1 = int(h * 0.55), int(h * 0.75), int(w * 0.55), int(w * 0.8)
    optical[0][y0:y1, x0:x1] = 3400
    optical[2][y0:y1, x0:x1] = 3500
    optical[3][y0:y1, x0:x1] = 1500

    # cloud-shadow decoy: looks like water optically (low NIR) but will
    # NOT get low SAR backscatter -- exercises the disagreement flag
    cy2, cx2, r2 = int(h * 0.7), int(w * 0.2), 35
    shadow_blob = (yy - cy2) ** 2 + (xx - cx2) ** 2 <= r2 ** 2
    optical[1][shadow_blob] = 1400
    optical[3][shadow_blob] = 700

    sar_db = np.full((h, w), -12.0, dtype=np.float32)  # ambient backscatter baseline
    sar_db[water_blob] = -24.0        # specular -> low backscatter (confirms water)
    sar_db[y0:y1, x0:x1] = -3.0       # corner-reflector -> high backscatter (confirms built-up)
    sar_db[shadow_blob] = -11.0       # NOT low -> disagrees with optical "water" reading

    sar_scaled = ((sar_db + 30.0) * 1000.0).clip(0, 65535).astype(np.uint16)  # store as scaled uint16

    _write_geotiff(OUT_DIR / "mission3_optical.tif", optical,
                    AHMEDABAD_LON, AHMEDABAD_LAT, GSD_DEG,
                    band_names=["blue", "green", "red", "nir"])
    _write_geotiff(OUT_DIR / "mission3_sar.tif", sar_scaled[None, :, :],
                    AHMEDABAD_LON, AHMEDABAD_LAT, GSD_DEG,
                    band_names=["sigma0_scaled_x1000_plus30db"])
    print("  NOTE: SAR band is stored scaled as uint16 ((dB+30)*1000). "
          "Descale with sar_db = arr/1000.0 - 30.0 before fusion.")


if __name__ == "__main__":
    print(f"Seeding demo data into {OUT_DIR}")
    seed_mission1_optical()
    seed_mission2_urban_change()
    seed_mission3_optical_sar()
    print("Done.")
