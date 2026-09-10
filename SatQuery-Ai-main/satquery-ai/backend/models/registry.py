"""Model registry and auditable provenance taxonomy for remote sensing AI models."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from dataclasses import dataclass, field


class EntityType(str, Enum):
    """Rigorous classification of computational and data assets."""
    MODEL = "MODEL"
    DETERMINISTIC_ENGINE = "DETERMINISTIC_ENGINE"
    DATASET = "DATASET"
    EXPERIMENT = "EXPERIMENT"
    ARTIFACT = "ARTIFACT"


class RuntimeStatus(str, Enum):
    """Allowed runtime states for models. These reflect actual runtime checks."""
    NOT_INSTALLED = "NOT_INSTALLED"
    CHECKPOINT_FOUND = "CHECKPOINT_FOUND"
    CHECKPOINT_VERIFIED = "CHECKPOINT_VERIFIED"
    READY_CPU = "READY_CPU"
    READY_CUDA = "READY_CUDA"
    UNTRAINED = "UNTRAINED"
    FALLBACK_ONLY = "FALLBACK_ONLY"
    ERROR = "ERROR"
    UNAVAILABLE = "UNAVAILABLE"


class TruthState(str, Enum):
    """Allowed truth states distinguishing the source of evaluation claims."""
    UPSTREAM_REPORTED = "UPSTREAM_REPORTED"
    SATQUERY_TRAINED = "SATQUERY_TRAINED"
    SATQUERY_MEASURED = "SATQUERY_MEASURED"
    LOCAL_REPRODUCED = "LOCAL_REPRODUCED"
    UNTRAINED_MODEL = "UNTRAINED_MODEL"
    CLASSICAL_ENGINE = "CLASSICAL_ENGINE"
    FALLBACK = "FALLBACK"
    UNKNOWN = "UNKNOWN"


class EvaluationSource(str, Enum):
    """Distinguishes where benchmark/evaluation numbers originate."""
    UPSTREAM_REPORTED = "UPSTREAM_REPORTED"
    SATQUERY_MEASURED = "SATQUERY_MEASURED"
    SYNTHETIC_REGRESSION = "SYNTHETIC_REGRESSION"
    NOT_EVALUATED = "NOT_EVALUATED"


@runtime_checkable
class ModelAdapter(Protocol):
    """Standardized interface for all perception and VLM model adapters."""
    name: str
    task: str
    capabilities: List[str]
    vram_estimate_mb: int

    @property
    def status(self) -> str:
        """Return 'registered', 'not_installed', 'ready', or 'error'."""
        ...

    def load(self, device: str = "cpu") -> None:
        """Load model weights onto target device."""
        ...

    def unload(self) -> None:
        """Evict model from device memory."""
        ...

    def health(self) -> Dict[str, Any]:
        """Return diagnostic health and availability status."""
        ...


@dataclass
class ModelMetadata:
    """Rigorous model provenance taxonomy for statistical neural models."""
    id: str = ""
    name: str = ""
    task: str = ""
    architecture: str = ""
    pretrained_source: str = ""
    task_finetuned: bool = False
    training_dataset: str = ""
    validation_dataset: str = ""
    entity_type: str = EntityType.MODEL.value
    checkpoint: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    training_commit: Optional[str] = None
    evaluation_metrics: Dict[str, Any] = field(default_factory=dict)
    evaluation_source: str = EvaluationSource.NOT_EVALUATED.value
    runtime_status: str = RuntimeStatus.NOT_INSTALLED.value
    truth_state: str = TruthState.UNKNOWN.value
    fallback_available: bool = False
    fallback_type: Optional[str] = None
    vram_estimate_mb: int = 0
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "id": self.id,
            "name": self.name,
            "task": self.task,
            "architecture": self.architecture,
            "pretrained_source": self.pretrained_source,
            "task_finetuned": self.task_finetuned,
            "training_dataset": self.training_dataset,
            "validation_dataset": self.validation_dataset,
            "checkpoint": self.checkpoint,
            "checkpoint_sha256": self.checkpoint_sha256,
            "training_commit": self.training_commit,
            "evaluation_metrics": self.evaluation_metrics,
            "evaluation_source": self.evaluation_source,
            "runtime_status": self.runtime_status,
            "truth_state": self.truth_state,
            "fallback_available": self.fallback_available,
            "fallback_type": self.fallback_type,
            "vram_estimate_mb": self.vram_estimate_mb,
            "description": self.description,
            "capabilities": self.capabilities,
            "notes": self.notes,
        }


@dataclass
class EngineMetadata:
    """Rigorous provenance taxonomy for deterministic GIS and physical calculation engines."""
    name: str
    task: str
    algorithm: str
    mathematical_basis: str
    entity_type: str = EntityType.DETERMINISTIC_ENGINE.value
    runtime_status: str = "READY_CPU"
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    verification_standard: str = "Survey of India / Physical Spectral Theory"
    uncertainty_formulation: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "name": self.name,
            "task": self.task,
            "algorithm": self.algorithm,
            "mathematical_basis": self.mathematical_basis,
            "runtime_status": self.runtime_status,
            "capabilities": self.capabilities,
            "description": self.description,
            "verification_standard": self.verification_standard,
            "uncertainty_formulation": self.uncertainty_formulation,
            "notes": self.notes,
        }


class StubModelAdapter:
    """Explicit uninstalled / Phase-1 candidate model adapter."""

    def __init__(
        self,
        name: str,
        task: str,
        description: str,
        capabilities: List[str],
        vram_estimate_mb: int,
        phase_target: str = "Phase 1",
    ):
        self.name = name
        self.task = task
        self.description = description
        self.capabilities = capabilities
        self.vram_estimate_mb = vram_estimate_mb
        self.phase_target = phase_target
        self._is_loaded = False

    @property
    def status(self) -> str:
        return "not_installed"

    def load(self, device: str = "cpu") -> None:
        raise NotImplementedError(
            f"Model '{self.name}' is scheduled for {self.phase_target} and is not yet installed in Phase 0."
        )

    def unload(self) -> None:
        self._is_loaded = False

    def health(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "task": self.task,
            "status": self.status,
            "installed": False,
            "vram_estimate_mb": self.vram_estimate_mb,
            "message": f"Model '{self.name}' not installed. Scheduled for {self.phase_target}.",
        }


class ModelRegistry:
    """Central registry tracking AI models, deterministic engines, and runtime health."""

    def __init__(self):
        self._models: Dict[str, ModelAdapter] = {}
        self._provenance: Dict[str, ModelMetadata] = {}
        self._engines: Dict[str, EngineMetadata] = {}
        self._register_default_entities()

    def _register_default_entities(self) -> None:
        # === 1. NEURAL MODELS ===
        # GeoChat-7B (VLM)
        self.register(
            "geochat",
            StubModelAdapter(
                name="GeoChat-7B",
                task="vqa_and_grounding",
                description="Remote sensing vision-language model for single-image VQA and visual grounding",
                capabilities=["vqa", "grounding", "scene_description"],
                vram_estimate_mb=4500,
                phase_target="Phase 1",
            ),
        )
        self.register_provenance(
            "geochat",
            ModelMetadata(
                id="geochat",
                name="GeoChat-7B",
                task="vqa_and_grounding",
                architecture="LLaVA-1.5 RS Fine-tuned (Vicuna-7B + CLIP-ViT-L/14)",
                pretrained_source="MBZUAI/geochat-7b",
                task_finetuned=False,
                training_dataset="RSVQA / LR & HR Instruct Multimodal Alignment",
                validation_dataset="RSVQA-HR Test Split / VRSBench Grounding",
                checkpoint="checkpoints/geochat",
                checkpoint_sha256=None,
                training_commit="upstream-mbzuai-release",
                evaluation_metrics={"rsvqa_accuracy": 0.785, "yes_no_acc": 0.862},
                evaluation_source=EvaluationSource.UPSTREAM_REPORTED.value,
                runtime_status=RuntimeStatus.NOT_INSTALLED.value,
                truth_state=TruthState.UPSTREAM_REPORTED.value,
                fallback_available=True,
                fallback_type="OFFLINE_HEURISTIC_VQA",
                vram_estimate_mb=4500,
                description="Remote sensing vision-language model for single-image VQA and semantic visual grounding",
                capabilities=["vqa", "grounding", "scene_description"],
            ),
        )

        # ChangeNet (Bi-Temporal Change Detection)
        self.register_provenance(
            "changenet",
            ModelMetadata(
                id="changenet",
                name="Siamese ChangeNet",
                task="bitemporal_change_detection",
                architecture="Siamese ResNet18 + Feature Pyramid Difference Head",
                pretrained_source="Torchvision ResNet-18",
                task_finetuned=False,
                training_dataset="synthetic_prototype",
                validation_dataset="synthetic_val",
                checkpoint="checkpoints/changenet_best.pt",
                checkpoint_sha256=None,
                training_commit="prototype-synthetic-v1",
                evaluation_metrics={"status": "unverified_checkpoint"},
                evaluation_source=EvaluationSource.NOT_EVALUATED.value,
                runtime_status=RuntimeStatus.UNTRAINED.value,
                truth_state=TruthState.UNTRAINED_MODEL.value,
                fallback_available=True,
                fallback_type="CLASSICAL_SPECTRAL_DIFFERENCE",
                vram_estimate_mb=2500,
                description="Bi-temporal change detection with spectral differential fallback (ΔNDBI / ΔNDVI / ΔNDWI)",
                capabilities=["bitemporal_change", "contour_extraction", "altered_area_ha"],
            ),
        )

        # DOFA (Multimodal Foundation Optical + SAR)
        self.register(
            "dofa",
            StubModelAdapter(
                name="DOFA-Foundation",
                task="cross_modal_representation",
                description="Dynamic Optical-SAR Foundation model for multi-sensor embedding",
                capabilities=["optical_feature_extraction", "sar_feature_extraction"],
                vram_estimate_mb=2500,
                phase_target="Phase 1",
            ),
        )
        self.register_provenance(
            "dofa",
            ModelMetadata(
                id="dofa",
                name="DOFA-Foundation",
                task="cross_modal_representation",
                architecture="Wavelength-Conditioned ViT-Base",
                pretrained_source="earth-chris/dofa-checkpoint",
                task_finetuned=False,
                training_dataset="BigEarthNet-MM (Sentinel-1 SAR + Sentinel-2 Optical)",
                validation_dataset="BigEarthNet-MM Test Split",
                checkpoint="checkpoints/dofa_base.pth",
                checkpoint_sha256=None,
                training_commit="upstream-dofa-v1",
                evaluation_metrics={"map": 0.865, "macro_f1": 0.812},
                evaluation_source=EvaluationSource.UPSTREAM_REPORTED.value,
                runtime_status=RuntimeStatus.NOT_INSTALLED.value,
                truth_state=TruthState.UPSTREAM_REPORTED.value,
                fallback_available=True,
                fallback_type="DETERMINISTIC_CROSS_MODAL_CORROBORATION",
                vram_estimate_mb=2500,
                description="Dynamic Optical-SAR Foundation model for multi-sensor cross-modal concordance",
                capabilities=["optical_feature_extraction", "sar_feature_extraction"],
            ),
        )

        # === 2. DETERMINISTIC GIS ENGINES (NOT NEURAL MODELS) ===
        self.register_engine(
            "water_body_analyzer",
            EngineMetadata(
                name="WaterBodyAnalyzer",
                task="spatial_ranking_and_water_segmentation",
                algorithm="MNDWI Spectral Math + Otsu Adaptive Threshold + Morphological Opening + Connected Components + WGS84 Geodesic Contours",
                mathematical_basis="MNDWI = (Green - SWIR1) / (Green + SWIR1); pyproj.Geod(ellps='WGS84')",
                capabilities=["water_detection", "geodesic_area_ha", "spatial_ranking", "contour_polygonization", "mixed_pixel_uncertainty"],
                description="Deterministic spectral water segmentation and geodesic ellipsoidal area ranking with statistical ambiguity qualification",
                uncertainty_formulation="sigma_area = Perimeter * GSD * 0.5",
            ),
        )

        self.register_engine(
            "built_up_analyzer",
            EngineMetadata(
                name="BuiltUpAnalyzer",
                task="built_up_segmentation_and_ranking",
                algorithm="NDBI/BSI Spectral Math + Otsu Adaptive Threshold + Morphological Closing + Connected Components + WGS84 Geodesic Contours",
                mathematical_basis="NDBI = (SWIR1 - NIR) / (SWIR1 + NIR); pyproj.Geod(ellps='WGS84')",
                capabilities=["built_up_detection", "geodesic_area_ha", "urban_ranking", "contour_polygonization"],
                description="Deterministic spectral built-up extraction and spatial ranking",
                uncertainty_formulation="sigma_area = Perimeter * GSD * 0.5",
            ),
        )

        self.register_engine(
            "vegetation_analyzer",
            EngineMetadata(
                name="VegetationAnalyzer",
                task="vegetation_canopy_segmentation_and_ranking",
                algorithm="NDVI/SAVI Spectral Math + Otsu Adaptive Threshold + Morphological Filtering + Connected Components + WGS84 Geodesic Contours",
                mathematical_basis="NDVI = (NIR - Red) / (NIR + Red); SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)",
                capabilities=["vegetation_detection", "canopy_area_ha", "forest_ranking", "contour_polygonization"],
                description="Deterministic spectral canopy extraction and spatial ranking",
                uncertainty_formulation="sigma_area = Perimeter * GSD * 0.5",
            ),
        )

        self.register_engine(
            "sar_processor",
            EngineMetadata(
                name="SARRadiometricProcessor",
                task="sar_calibration_and_water_corroboration",
                algorithm="Radiometric Calibration to sigma0 (dB) + Lee 5x5 Speckle Filter + Radar Water Thresholding",
                mathematical_basis="sigma0_dB = 10 * log10(DN^2 / A^2); Lee local statistics filter",
                capabilities=["sar_calibration", "lee_filter", "radar_water_threshold", "cross_modal_corroboration"],
                description="Deterministic Sentinel-1 SAR calibration and physical spatial corroboration",
            ),
        )

        self.register_engine(
            "akaze_coregistration",
            EngineMetadata(
                name="AKAZECoRegistration",
                task="bitemporal_image_alignment",
                algorithm="AKAZE Nonlinear Scale Space Feature Detection + RANSAC Affine/Homography Homologous Matching",
                mathematical_basis="Nonlinear diffusion filtering + RANSAC residual error RMSE < 0.5 px",
                capabilities=["subpixel_alignment", "homography_estimation", "rmse_qualification"],
                description="Deterministic feature-based geometric coregistration for multi-temporal optical imagery",
            ),
        )

        self.register_engine(
            "geodesic_geometry",
            EngineMetadata(
                name="GeodesicGeometryEngine",
                task="ellipsoidal_spatial_measurement",
                algorithm="Karney Geodesic Inverse Problem on WGS84 Ellipsoid (PyProj / Shapely 2.0)",
                mathematical_basis="WGS84 Reference Ellipsoid (a=6378137.0m, f=1/298.257223563)",
                capabilities=["geodesic_area_m2", "geodesic_area_ha", "geodesic_perimeter_m", "two_point_distance_m"],
                description="Deterministic geodetic surface measurement compliant with Survey of India standards",
            ),
        )

    def register(self, key: str, adapter: ModelAdapter) -> None:
        self._models[key] = adapter

    def register_provenance(self, key: str, meta: ModelMetadata) -> None:
        self._provenance[key] = meta

    def register_engine(self, key: str, engine: EngineMetadata) -> None:
        self._engines[key] = engine

    def get(self, key: str) -> Optional[ModelAdapter]:
        return self._models.get(key)

    def get_provenance(self, key: str) -> Optional[ModelMetadata]:
        return self._provenance.get(key)

    def get_engine(self, key: str) -> Optional[EngineMetadata]:
        return self._engines.get(key)

    def list_engines(self) -> List[Dict[str, Any]]:
        result = []
        for key, engine in sorted(self._engines.items()):
            d = engine.to_dict()
            d["key"] = key
            result.append(d)
        return result

    def list_entities(self) -> Dict[str, Any]:
        return {
            "models": self.list_models(),
            "deterministic_engines": self.list_engines(),
        }

    def list_models(self) -> List[Dict[str, Any]]:
        result = []
        # Return provenance metadata merged with runtime adapter health
        all_keys = set(self._models.keys()) | set(self._provenance.keys())
        for key in sorted(all_keys):
            prov = self._provenance.get(key)
            adapter = self._models.get(key)
            if prov:
                d = prov.to_dict()
                d["key"] = key
                if adapter:
                    d["runtime_status"] = adapter.status
                result.append(d)
            elif adapter:
                d = {
                    "entity_type": EntityType.MODEL.value,
                    "key": key,
                    "name": getattr(adapter, "name", key),
                    "task": getattr(adapter, "task", "unknown"),
                    "architecture": "Unspecified",
                    "pretrained_source": "Unspecified",
                    "task_finetuned": False,
                    "training_dataset": "None",
                    "validation_dataset": "None",
                    "checkpoint": None,
                    "checkpoint_sha256": None,
                    "training_commit": None,
                    "evaluation_metrics": {},
                    "runtime_status": adapter.status,
                    "vram_estimate_mb": getattr(adapter, "vram_estimate_mb", 0),
                    "description": getattr(adapter, "description", ""),
                    "capabilities": getattr(adapter, "capabilities", []),
                }
                result.append(d)
        return result


model_registry = ModelRegistry()

