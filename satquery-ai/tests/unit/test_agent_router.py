"""Unit tests for agent query router and intent classifier evaluation matrix."""

from backend.agent.router import classify_intent, IntentType


def test_agent_routing_evaluation_matrix():
    """Evaluate agent routing accuracy across 12 distinct remote sensing intent scenarios."""
    test_matrix = [
        ("Describe this scene and weather conditions", 1, False, IntentType.VQA),
        ("What land cover classes are present in this image?", 1, False, IntentType.VQA),
        ("Highlight the water reservoir", 1, False, IntentType.GROUNDING),
        ("Locate the airport runway", 1, False, IntentType.GROUNDING),
        ("Find the large industrial storage tanks", 1, False, IntentType.GROUNDING),
        ("What changed between these two dates?", 2, False, IntentType.CHANGE_DETECTION),
        ("Did the built-up area increase over time?", 2, False, IntentType.CHANGE_DETECTION),
        ("Show me the surface difference and growth", 2, False, IntentType.CHANGE_DETECTION),
        ("Use both sensors to detect water and buildings", 2, True, IntentType.OPTICAL_SAR_FUSION),
        ("Corroborate optical findings with SAR radar backscatter", 2, True, IntentType.OPTICAL_SAR_FUSION),
        ("Analyze Sentinel-1 C-band penetration", 1, True, IntentType.OPTICAL_SAR_FUSION),
        ("Where is the agricultural vegetation cluster?", 1, False, IntentType.GROUNDING),
    ]

    correct = 0
    for query, img_count, has_sar, expected_intent in test_matrix:
        intent, conf, params = classify_intent(
            query=query,
            available_image_count=img_count,
            has_sar=has_sar,
        )
        if intent == expected_intent:
            correct += 1
        else:
            print(f"FAILED ROUTE: Query='{query}' -> Got={intent}, Expected={expected_intent}")

    accuracy_pct = (correct / len(test_matrix)) * 100.0
    print(f"Agent Routing Accuracy: {accuracy_pct:.1f}% ({correct}/{len(test_matrix)})")
    assert accuracy_pct == 100.0
