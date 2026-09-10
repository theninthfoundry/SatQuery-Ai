"""Integration tests for the complete Spatial Ranking pipeline."""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.agent.query_planner import QueryCapabilityPlanner
from backend.engines.spatial_ranking import SpatialRankingEngine
from backend.mission.parser import MissionParser, MissionIntent
from backend.mission.planner import MissionPlanner
from backend.mission.dag import NodeType
from tests.fixtures.synthetic_raster import (
    create_synthetic_water_geotiff,
    HAS_RASTERIO,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def synthetic_water_raster(tmp_path):
    tif_path = tmp_path / "synthetic_water_test.tif"
    create_synthetic_water_geotiff(tif_path, width=128, height=128)
    return str(tif_path)


class TestSpatialRankingPipeline:

    def test_query_planner_parses_superlatives_correctly(self):
        """Verify natural language decomposition separates semantic intent from geospatial computation."""
        planner = QueryCapabilityPlanner()

        plan1 = planner.plan("Where is the largest water body?")
        assert plan1.intent == "spatial_ranking"
        assert plan1.target == "water_body"
        assert plan1.operation == "largest"
        assert plan1.measurement == "area"
        assert plan1.geometry_required is True

        plan2 = planner.plan("Locate the biggest lake in this scene")
        assert plan2.intent == "spatial_ranking"
        assert plan2.target == "water_body"
        assert plan2.operation == "largest"

        plan3 = planner.plan("Find the smallest reservoir")
        assert plan3.intent == "spatial_ranking"
        assert plan3.target == "water_body"
        assert plan3.operation == "smallest"

    def test_mission_parser_and_dag_generation(self):
        """Verify mission parser assigns SPATIAL_RANKING intent and constructs executable DAG."""
        parser = MissionParser()
        mission = parser.parse_query("Where is the largest water body?")

        assert mission.intent == MissionIntent.SPATIAL_RANKING

        planner = MissionPlanner()
        dag = planner.build_plan(mission)

        ranking_nodes = [n for n in dag.nodes.values() if n.type == NodeType.SPATIAL_RANKING]
        assert len(ranking_nodes) >= 1, "Expected DAG to contain SPATIAL_RANKING node"

    @pytest.mark.skipif(not HAS_RASTERIO, reason="rasterio required for geospatial tests")
    def test_spatial_ranking_engine_execution(self, synthetic_water_raster):
        """Verify SpatialRankingEngine executes detection, geodesic measurement, and ranking."""
        engine = SpatialRankingEngine()
        result = engine.execute(
            image_path=synthetic_water_raster,
            target="water_body",
            operation="largest",
        )

        assert result["status"] == "success"
        assert result["total_ranked"] >= 2
        assert result["decision"] in ["ANSWER", "QUALIFY"]

        features = result["features"]
        assert len(features) >= 2
        largest = features[0]
        second = features[1]

        # Check properties and geometry
        assert largest["properties"]["rank"] == 1
        assert largest["properties"]["is_largest"] is True
        assert largest["properties"]["area_m2"] > second["properties"]["area_m2"]
        assert largest["geometry"]["type"] == "Polygon"
        assert len(largest["geometry"]["coordinates"][0]) >= 4

        # Check evidence contract
        assert "evidence_contract" in result
        contract = result["evidence_contract"]
        assert contract["decision"] in ["ANSWER", "QUALIFY"]
        assert "confidence" in contract

    @pytest.mark.skipif(not HAS_RASTERIO, reason="rasterio required for geospatial tests")
    def test_api_spatial_rank_endpoint(self, client, synthetic_water_raster):
        """Verify POST /api/v1/analysis/spatial-rank HTTP endpoint integration."""
        payload = {
            "image_path": synthetic_water_raster,
            "target": "water_body",
            "operation": "largest",
            "min_area_m2": 500.0,
        }

        response = client.post("/api/v1/analysis/spatial-rank", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["task"] == "spatial_ranking"
        assert data["status"] == "success"
        assert data["total_ranked"] >= 2
        assert len(data["features"]) >= 2
        assert data["features"][0]["properties"]["rank"] == 1
        assert "ha" in data["answer"]
