from feature_extraction.extractor import FeatureSet
from chart_engine.chart_state import ChartState

class DivisionalIntelligenceSystem:
    @staticmethod
    def validate_career_d10(features: FeatureSet, base_career_score: dict, chart: ChartState) -> dict:
        """
        Implements the logic of the '2.1 Division Intelligence System.md'.
        Takes the primary D1 Career Score and checks the D10 Dashamsha Varga for validation/conflict.
        """
        # Determine the D1 10th House Lord
        house_lords = features.relational["house_lords"]
        h10_data = house_lords.get("10") or house_lords.get(10)
        h10_lord = h10_data["lord"]

        # Retrieve the D10 placement directly from the canonical ChartState.
        h10_lord_d10_sign = chart.divisional_charts["D10_Dashamsha"][h10_lord]

        # Simple intelligent heuristic: If the D1 lord sits in a strong Varga state, we boost.
        # This prevents the AI Agent from being blindly optimistic when a Varga ruins the D1 chart.
        enhanced_score = base_career_score["raw_score"]
        conflict_detected = "No Conflict"

        # If the D10 sign is the Lord's debilitation point, trigger an override warning
        from feature_extraction.dictionaries import DEBILITATION

        # DEBILITATION[PlanetName.SUN] -> ZodiacSign.LIBRA
        # Need to parse dictionary keys dynamically
        debilitated = False
        for p, d_sign in DEBILITATION.items():
            if p.value == h10_lord and d_sign.value == h10_lord_d10_sign:
                debilitated = True
                break

        if debilitated:
            enhanced_score *= 0.7 # 30% penalty
            conflict_detected = f"WARNING: D1 Career is strong, but the 10th Lord ({h10_lord}) is Debilitated in the D10 Dashamsha. Massive friction expected."

        return {
            "enhanced_career_score": round(enhanced_score, 3),
            "original_d1_score": base_career_score["raw_score"],
            "d10_validation_status": conflict_detected,
            "d10_lord_placement": f"{h10_lord} sits in D10 {h10_lord_d10_sign}"
        }
