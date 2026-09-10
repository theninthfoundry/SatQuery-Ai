"""Integration test verifying the behavioral matrix across 3 visually different scenes.

Same query + different imagery = different evidence.
1. Water-rich scene    -> ANSWER with real polygon
2. Urban scene         -> ABSTAIN
3. Vegetation scene    -> ABSTAIN
"""

from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS

from backend.geospatial.water_body import WaterBodyAnalyzer
from backend.engines.spatial_ranking import SpatialRankingEngine
from backend.db import get_db, Base, engine
from backend.models_db import ImageRecord
from tests.fixtures.synthetic_raster import create_synthetic_water_geotiff, create_synthetic_multiband_geotiff


def create_pure_vegetation_geotiff(output_path: Path, width: int = 128, height: int = 128, epsg: int = 32643) -> Path:
    """Create a 4-band GeoTIFF representing dense agricultural vegetation (high NIR, very negative NDWI)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transform = from_origin(500000.0, 3000000.0, 10.0, 10.0)
    crs = CRS.from_epsg(epsg)

    # 4 Bands: Blue, Green, Red, NIR
    data = np.zeros((4, height, width), dtype=np.uint16)
    data[0] = 350   # Blue
    data[1] = 600   # Green
    data[2] = 400   # Red
    data[3] = 3200  # NIR (NDWI = (600 - 3200) / (600 + 3200) = -0.684 across all pixels)

    profile = {
        "driver": "GTiff",
        "dtype": "uint16",
        "nodata": 0,
        "width": width,
        "height": height,
        "count": 4,
        "crs": crs,
        "transform": transform,
        "compress": "lzw",
    }
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(data)
    return output_path


class TestBehavioralMatrixWater:

    @pytest.fixture(autouse=True)
    def setup_scenes(self, tmp_path):
        Base.metadata.create_all(bind=engine)
        self.db = next(get_db())

        self.demo_dir = Path("./data/demo")
        self.demo_dir.mkdir(parents=True, exist_ok=True)

        # Scene 1: Water-rich
        self.water_path = self.demo_dir / "scene_brahmaputra_flood.tif"
        if not self.water_path.exists():
            create_synthetic_water_geotiff(self.water_path, width=128, height=128, epsg=32643)

        # Scene 2: Urban
        self.urban_path = self.demo_dir / "scene_optical_ahmedabad.tif"
        if not self.urban_path.exists():
            create_synthetic_multiband_geotiff(self.urban_path, width=128, height=128, bands=4, epsg=32643)

        # Scene 3: Vegetation
        self.veg_path = tmp_path / "scene_vegetation_dense.tif"
        create_pure_vegetation_geotiff(self.veg_path, width=128, height=128, epsg=32643)

        # Register all 3 in DB
        for img_id, path, fn in [
            ("img_matrix_water", self.water_path, "scene_brahmaputra_flood.tif"),
            ("img_matrix_urban", self.urban_path, "scene_optical_ahmedabad.tif"),
            ("img_matrix_veg", self.veg_path, "scene_vegetation_dense.tif"),
        ]:
            img = self.db.get(ImageRecord, img_id)
            if not img:
                img = ImageRecord(
                    id=img_id,
                    filename=fn,
                    path=str(path),
                    format="GTiff",
                    width=128,
                    height=128,
                    band_count=4,
                    dtype="uint8",
                    crs="WGS 84 / UTM zone 43N",
                    epsg=32643,
                    is_valid=True,
                )
                self.db.add(img)
        self.db.commit()

    def test_behavioral_matrix_across_scenes(self):
        """Verify identical query produces 3 scientifically differentiated outputs."""
        query = "Where is the largest water body?"
        engine_inst = SpatialRankingEngine()

        # 1. Water-rich scene execution
        res_water = engine_inst.rank(
            image_id="img_matrix_water",
            target="water_body",
            operation="largest",
            db=self.db,
            query=query,
        )
        assert res_water["status"] == "success"
        assert res_water["evidence_contract"]["gate_decision"] == "ANSWER"
        assert res_water["finding"]["area_ha"] > 5.0
        assert len(res_water["evidence_contract"]["spatial_evidence"]["features"]) >= 1

        # 2. Urban scene execution
        res_urban = engine_inst.rank(
            image_id="img_matrix_urban",
            target="water_body",
            operation="largest",
            db=self.db,
            query=query,
        )
        assert res_urban["status"] == "success"
        assert res_urban["evidence_contract"]["gate_decision"] == "ABSTAIN"
        assert res_urban["finding"]["area_ha"] == 0.0
        assert len(res_urban["evidence_contract"]["spatial_evidence"]["features"]) == 0

        # 3. Dense vegetation scene execution
        res_veg = engine_inst.rank(
            image_id="img_matrix_veg",
            target="water_body",
            operation="largest",
            db=self.db,
            query=query,
        )
        assert res_veg["status"] == "success"
        assert res_veg["evidence_contract"]["gate_decision"] == "ABSTAIN"
        assert res_veg["finding"]["area_ha"] == 0.0
        assert len(res_veg["evidence_contract"]["spatial_evidence"]["features"]) == 0

        # Behavioral Matrix Verification:
        # Decisions must be distinct between water and non-water
        assert res_water["evidence_contract"]["gate_decision"] != res_urban["evidence_contract"]["gate_decision"]
        assert res_water["finding"]["area_ha"] > res_urban["finding"]["area_ha"]
        assert res_urban["evidence_contract"]["gate_decision"] == res_veg["evidence_contract"]["gate_decision"] == "ABSTAIN"
