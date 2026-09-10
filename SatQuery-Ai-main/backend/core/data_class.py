"""
Truth Lock 3.0 data classification (per the latest audit's section 1.3).

Every EvidenceContract must declare which of these categories produced it.
This is stricter than fallback_used/is_real_weights alone: it also covers
non-model deterministic engines and demo/fixture isolation, so a synthetic
fixture can never be mistaken for validated analysis, and a deterministic
GIS result (which is real, just not ML) isn't miscategorized as a model
result either.
"""

from __future__ import annotations

from enum import Enum


class DataClass(str, Enum):
    REAL_MODEL = "REAL_MODEL"                          # verified checkpoint, real inference
    REAL_DATA = "REAL_DATA"                             # real observation, no model involved
    DETERMINISTIC_ANALYSIS = "DETERMINISTIC_ANALYSIS"    # e.g. MNDWI water detector
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"               # test/demo data, must never reach production evidence
    DEMO_PLACEHOLDER = "DEMO_PLACEHOLDER"                 # UI mock content, not analysis
    UNAVAILABLE_CAPABILITY = "UNAVAILABLE_CAPABILITY"     # model/engine not ready; fail-closed result


PRODUCTION_ALLOWED: frozenset[DataClass] = frozenset({
    DataClass.REAL_MODEL,
    DataClass.REAL_DATA,
    DataClass.DETERMINISTIC_ANALYSIS,
    DataClass.UNAVAILABLE_CAPABILITY,  # allowed: it's an honest abstention, not a fabrication
})


class DataClassPolicyError(ValueError):
    pass


def assert_production_safe(data_class: DataClass, *, environment: str) -> None:
    """
    Call this at the API boundary before any result leaves the backend
    toward a real (non-test) client. Refuses to let SYNTHETIC_FIXTURE or
    DEMO_PLACEHOLDER content reach a production response.
    """
    if environment == "production" and data_class not in PRODUCTION_ALLOWED:
        raise DataClassPolicyError(
            f"Refusing to serve a {data_class.value} result in a production "
            f"environment. Only {sorted(c.value for c in PRODUCTION_ALLOWED)} "
            f"are allowed outside test/demo contexts."
        )
