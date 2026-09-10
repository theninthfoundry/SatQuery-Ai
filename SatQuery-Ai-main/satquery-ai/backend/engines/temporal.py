"""Multi-temporal observation reasoning and trajectory analysis engine.

Extends analysis beyond simple bi-temporal (T1-T2) pairs into full
N-observation Earth Observation time-series trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class TrendType(str, Enum):
    """Categorization of temporal trajectory trends."""
    ACCELERATING_INCREASE = "accelerating_increase"
    STEADY_INCREASE = "steady_increase"
    DECELERATING_INCREASE = "decelerating_increase"
    STABLE = "stable"
    DECELERATING_DECREASE = "decelerating_decrease"
    STEADY_DECREASE = "steady_decrease"
    ACCELERATING_DECREASE = "accelerating_decrease"
    EPISODIC_PULSE = "episodic_pulse"  # e.g., flood spike, fire scar
    CYCLICAL_SEASONAL = "cyclical_seasonal"


@dataclass
class TemporalObservation:
    """A single dated observation in a time series."""
    asset_id: str
    timestamp: datetime
    metric_name: str
    value: float  # Scalar area, percentage, or mean index (e.g., mean NDVI, built-up area in m²)
    unit: str = "fraction"
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "value": round(self.value, 4),
            "unit": self.unit,
            "quality_score": round(self.quality_score, 3),
            "metadata": self.metadata,
        }


@dataclass
class TemporalTrajectory:
    """Analyzed trajectory of a monitored phenomenon across multiple dates."""
    metric_name: str
    unit: str
    observations_count: int
    first_timestamp: datetime
    last_timestamp: datetime
    total_duration_days: float

    # Quantitative change
    start_value: float
    end_value: float
    absolute_change: float
    percentage_change: float
    annualized_rate_of_change: float  # Change per 365 days

    # Dynamic behavior
    trend_type: TrendType
    monotonic: bool
    inflection_points: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    warnings: List[str] = field(default_factory=list)
    narrative_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "unit": self.unit,
            "observations_count": self.observations_count,
            "time_span": {
                "start": self.first_timestamp.isoformat(),
                "end": self.last_timestamp.isoformat(),
                "duration_days": round(self.total_duration_days, 1),
            },
            "values": {
                "start": round(self.start_value, 4),
                "end": round(self.end_value, 4),
                "absolute_change": round(self.absolute_change, 4),
                "percentage_change": round(self.percentage_change, 2),
                "annualized_rate": round(self.annualized_rate_of_change, 4),
            },
            "dynamics": {
                "trend_type": self.trend_type.value,
                "monotonic": self.monotonic,
                "inflection_points": self.inflection_points,
            },
            "confidence": round(self.confidence, 3),
            "warnings": self.warnings,
            "summary": self.narrative_summary,
        }


class TemporalReasoningEngine:
    """Reasoning engine for multi-temporal satellite data analysis."""

    def analyze_trajectory(
        self,
        observations: List[TemporalObservation],
        phenomenon_type: str = "general",  # "built_up", "vegetation", "water", "disaster"
    ) -> TemporalTrajectory:
        """Analyze a sequence of observations ordered across time.
        
        Args:
            observations: List of temporal observations.
            phenomenon_type: Type of surface feature being tracked.
            
        Returns:
            TemporalTrajectory with rigorous trend classification and rate estimates.
        """
        if len(observations) < 2:
            raise ValueError("Trajectory analysis requires at least 2 temporal observations")

        # 1. Sort by timestamp
        sorted_obs = sorted(observations, key=lambda x: x.timestamp)
        metric_name = sorted_obs[0].metric_name
        unit = sorted_obs[0].unit

        t_first = sorted_obs[0].timestamp
        t_last = sorted_obs[-1].timestamp
        duration_days = max(1.0, (t_last - t_first).total_seconds() / 86400.0)

        # 2. Extract values and days relative to start
        days = np.array([(o.timestamp - t_first).total_seconds() / 86400.0 for o in sorted_obs])
        values = np.array([o.value for o in sorted_obs], dtype=np.float64)
        weights = np.array([max(0.1, o.quality_score) for o in sorted_obs], dtype=np.float64)

        start_val = float(values[0])
        end_val = float(values[-1])
        abs_change = end_val - start_val
        pct_change = (abs_change / max(1e-6, abs(start_val))) * 100.0 if abs(start_val) > 1e-6 else 0.0
        annualized_rate = (abs_change / duration_days) * 365.25

        warnings: List[str] = []

        # 3. Quality & consistency checks
        if duration_days < 7.0 and phenomenon_type == "built_up":
            warnings.append(
                f"Observation interval ({duration_days:.1f} days) is unusually short for urban expansion monitoring."
            )

        # Built-up area is generally monotonic (buildings rarely dematerialize overnight)
        diffs = np.diff(values)
        is_increasing = bool(np.all(diffs >= -1e-5))
        is_decreasing = bool(np.all(diffs <= 1e-5))
        is_monotonic = is_increasing or is_decreasing

        if phenomenon_type == "built_up" and not is_increasing and abs_change > 0:
            decrease_count = int(np.sum(diffs < -0.01 * (start_val + 1e-6)))
            if decrease_count > 0:
                warnings.append(
                    f"Non-monotonic built-up trajectory detected ({decrease_count} decrease intervals). "
                    f"Possible seasonal vegetation masking or cloud occlusion."
                )

        # 4. Trend classification
        trend_type, inflections = self._classify_trend(days, values, weights, duration_days)

        # 5. Confidence calculation
        avg_quality = float(np.mean(weights))
        sample_penalty = 1.0 if len(sorted_obs) >= 4 else (0.85 if len(sorted_obs) == 3 else 0.75)
        overall_confidence = min(0.98, avg_quality * sample_penalty)

        # 6. Narrative synthesis
        summary = self._generate_summary(
            phenomenon_type, metric_name, start_val, end_val, abs_change, pct_change,
            annualized_rate, duration_days, trend_type, unit
        )

        return TemporalTrajectory(
            metric_name=metric_name,
            unit=unit,
            observations_count=len(sorted_obs),
            first_timestamp=t_first,
            last_timestamp=t_last,
            total_duration_days=duration_days,
            start_value=start_val,
            end_value=end_val,
            absolute_change=abs_change,
            percentage_change=pct_change,
            annualized_rate_of_change=annualized_rate,
            trend_type=trend_type,
            monotonic=is_monotonic,
            inflection_points=inflections,
            confidence=overall_confidence,
            warnings=warnings,
            narrative_summary=summary,
        )

    def _classify_trend(
        self,
        days: np.ndarray,
        values: np.ndarray,
        weights: np.ndarray,
        duration_days: float,
    ) -> Tuple[TrendType, List[Dict[str, Any]]]:
        """Determine mathematical trend type and locate significant inflection points."""
        n = len(values)
        if n == 2:
            delta = values[1] - values[0]
            rel_delta = delta / max(1e-5, abs(values[0]))
            if abs(rel_delta) < 0.02:
                return TrendType.STABLE, []
            return (TrendType.STEADY_INCREASE if delta > 0 else TrendType.STEADY_DECREASE), []

        # Polynomial fit for curvature
        try:
            poly_deg = min(2, n - 1)
            coeffs = np.polyfit(days, values, deg=poly_deg, w=weights)
        except Exception:
            coeffs = np.array([0.0, 0.0])

        total_delta = values[-1] - values[0]
        rel_change = total_delta / max(1e-5, abs(values[0]))

        inflections: List[Dict[str, Any]] = []
        # Check for intermediate peaks/spikes (episodic pulse)
        max_idx = int(np.argmax(values))
        min_idx = int(np.argmin(values))
        if 0 < max_idx < n - 1 and (values[max_idx] - max(values[0], values[-1])) > 0.10 * max(1e-5, abs(values[0])):
            inflections.append({
                "type": "peak",
                "observation_index": max_idx,
                "day": float(days[max_idx]),
                "value": float(values[max_idx]),
            })
            return TrendType.EPISODIC_PULSE, inflections

        if 0 < min_idx < n - 1 and (min(values[0], values[-1]) - values[min_idx]) > 0.10 * max(1e-5, abs(values[0])):
            inflections.append({
                "type": "trough",
                "observation_index": min_idx,
                "day": float(days[min_idx]),
                "value": float(values[min_idx]),
            })
            return TrendType.EPISODIC_PULSE, inflections

        if abs(rel_change) < 0.03:
            return TrendType.STABLE, []

        if len(coeffs) == 3:
            # Quadratic: y = a*x^2 + b*x + c
            a, b, _ = coeffs
            if total_delta > 0:
                if a > 1e-7:
                    return TrendType.ACCELERATING_INCREASE, []
                elif a < -1e-7:
                    return TrendType.DECELERATING_INCREASE, []
                return TrendType.STEADY_INCREASE, []
            else:
                if a < -1e-7:
                    return TrendType.ACCELERATING_DECREASE, []
                elif a > 1e-7:
                    return TrendType.DECELERATING_DECREASE, []
                return TrendType.STEADY_DECREASE, []

        return (TrendType.STEADY_INCREASE if total_delta > 0 else TrendType.STEADY_DECREASE), []

    def _generate_summary(
        self,
        phenomenon: str,
        metric: str,
        start_val: float,
        end_val: float,
        abs_change: float,
        pct_change: float,
        annualized_rate: float,
        duration_days: float,
        trend: TrendType,
        unit: str,
    ) -> str:
        """Synthesize natural language domain-specific assessment."""
        direction = "increased" if abs_change > 0 else ("decreased" if abs_change < 0 else "remained constant")
        trend_desc = trend.value.replace("_", " ")

        summary = (
            f"Over a {duration_days:.0f}-day observation period, {metric} {direction} "
            f"from {start_val:.3f} to {end_val:.3f} {unit} ({pct_change:+.1f}%). "
            f"The dynamic trajectory follows an {trend_desc} pattern with an annualized "
            f"rate of {annualized_rate:+.3f} {unit}/year."
        )
        return summary
