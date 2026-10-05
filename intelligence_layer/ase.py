from feature_extraction.extractor import FeatureSet
from feature_extraction.dictionaries import (
    determine_full_dignity, get_compound_relationship,
    OWN_SIGNS, MOOLATRIKONA, EXALTATION, DEBILITATION
)
from chart_engine.models import PlanetName, ZodiacSign

class AstrologicalScoringEngine:

    # Full 7-tier dignity score mapping
    DIGNITY_SCORES = {
        "Exalted": 1.0,
        "Moolatrikona": 0.9,
        "Own Sign": 0.85,
        "Great Friend": 0.75,
        "Friend": 0.65,
        "Neutral": 0.5,
        "Enemy": 0.3,
        "Great Enemy": 0.2,
        "Debilitated": 0.1,
    }

    @staticmethod
    def _score_planet(planet_name: str, features: FeatureSet) -> float:
        """
        Scores planet using full 7-tier dignity: Exalted > Moolatrikona > Own > Great Friend > Friend > Neutral > Enemy > Great Enemy > Debilitated.
        """
        dignity = features.strength[planet_name]["dignity"]
        return AstrologicalScoringEngine.DIGNITY_SCORES.get(dignity, 0.5)

    @staticmethod
    def _score_house(house_num: int, features: FeatureSet) -> float:
        # H_score = w1 * lord_strength + w2 * occupancy
        house_lords = features.relational["house_lords"]
        # Handle dict keys that might be ints or strings
        house_data = house_lords.get(str(house_num)) or house_lords.get(house_num)
        lord = house_data["lord"]
        lord_score = AstrologicalScoringEngine._score_planet(lord, features)

        # Occupancy: counts all planets sitting inside this specific house
        occupants = sum(1 for p, pos in features.positional.items() if pos["house"] == house_num)

        # Max out occupancy score contribution at 0.2 (0.1 per planet)
        occupancy_score = min(0.2, occupants * 0.1)

        # Combine Lord's baseline strength with actual localized planetary mass
        return (0.8 * lord_score) + occupancy_score

    @staticmethod
    def score_career(features: FeatureSet) -> dict:
        """Career scoring via 10th, 6th, 2nd, 11th houses + Saturn/Sun."""
        h10 = AstrologicalScoringEngine._score_house(10, features)
        h6 = AstrologicalScoringEngine._score_house(6, features)
        h2 = AstrologicalScoringEngine._score_house(2, features)
        h11 = AstrologicalScoringEngine._score_house(11, features)

        saturn = AstrologicalScoringEngine._score_planet("Saturn", features)
        sun = AstrologicalScoringEngine._score_planet("Sun", features)
        planet_score = (saturn + sun) / 2.0

        career_score = (0.35 * h10) + (0.2 * h6) + (0.2 * h2) + (0.15 * h11) + (0.1 * planet_score)

        return {
            "raw_score": round(career_score, 3),
            "astrological_strength_band": "HIGH" if career_score > 0.6 else ("MEDIUM" if career_score > 0.4 else "LOW"),
            "contributing_factors": [
                f"Tenth House Power: {h10:.2f}",
                f"Karma/Authority Planets (Saturn/Sun): {planet_score:.2f}"
            ]
        }

    # ================================================================
    # ALL LIFE DOMAIN SCORING METHODS (Priority 7)
    # ================================================================

    @staticmethod
    def score_marriage(features: FeatureSet) -> dict:
        """Marriage scoring: D1+D9, 7th house, Venus, Jupiter, 2nd house."""
        h7 = AstrologicalScoringEngine._score_house(7, features)
        h2 = AstrologicalScoringEngine._score_house(2, features)
        venus = AstrologicalScoringEngine._score_planet("Venus", features)
        jupiter = AstrologicalScoringEngine._score_planet("Jupiter", features)
        moon = AstrologicalScoringEngine._score_planet("Moon", features)

        score = (0.30 * h7) + (0.15 * h2) + (0.25 * venus) + (0.15 * jupiter) + (0.15 * moon)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Marriage & Relationships"
        }

    @staticmethod
    def score_wealth(features: FeatureSet) -> dict:
        """Wealth scoring: D1+D2, 2nd, 11th, Jupiter, Venus."""
        h2 = AstrologicalScoringEngine._score_house(2, features)
        h11 = AstrologicalScoringEngine._score_house(11, features)
        h9 = AstrologicalScoringEngine._score_house(9, features)
        jupiter = AstrologicalScoringEngine._score_planet("Jupiter", features)
        venus = AstrologicalScoringEngine._score_planet("Venus", features)

        score = (0.30 * h2) + (0.25 * h11) + (0.15 * h9) + (0.15 * jupiter) + (0.15 * venus)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Wealth & Finances"
        }

    @staticmethod
    def score_health(features: FeatureSet) -> dict:
        """Health scoring: D1+D6, Ascendant, Sun, Saturn, Mars."""
        h1 = AstrologicalScoringEngine._score_house(1, features)
        h6 = AstrologicalScoringEngine._score_house(6, features)
        h8 = AstrologicalScoringEngine._score_house(8, features)
        sun = AstrologicalScoringEngine._score_planet("Sun", features)
        saturn = AstrologicalScoringEngine._score_planet("Saturn", features)
        mars = AstrologicalScoringEngine._score_planet("Mars", features)

        # Lower 6th/8th house scores = better health (they're disease houses)
        health_penalty = 1.0 - ((1.0 - h6) * 0.3 + (1.0 - h8) * 0.3)
        score = (0.25 * h1) + (0.15 * health_penalty) + (0.20 * sun) + (0.20 * mars) + (0.20 * saturn)
        score = max(0.1, min(1.0, score))
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Health & Vitality"
        }

    @staticmethod
    def score_education(features: FeatureSet) -> dict:
        """Education scoring: D1+D24, 4th, 5th, Mercury, Jupiter."""
        h4 = AstrologicalScoringEngine._score_house(4, features)
        h5 = AstrologicalScoringEngine._score_house(5, features)
        h9 = AstrologicalScoringEngine._score_house(9, features)
        mercury = AstrologicalScoringEngine._score_planet("Mercury", features)
        jupiter = AstrologicalScoringEngine._score_planet("Jupiter", features)

        score = (0.20 * h4) + (0.25 * h5) + (0.20 * h9) + (0.20 * mercury) + (0.15 * jupiter)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Education & Learning"
        }

    @staticmethod
    def score_children(features: FeatureSet) -> dict:
        """Children/Progeny scoring: D1+D7, 5th house, Jupiter."""
        h5 = AstrologicalScoringEngine._score_house(5, features)
        jupiter = AstrologicalScoringEngine._score_planet("Jupiter", features)
        moon = AstrologicalScoringEngine._score_planet("Moon", features)

        score = (0.40 * h5) + (0.35 * jupiter) + (0.25 * moon)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Children & Progeny"
        }

    @staticmethod
    def score_spiritual(features: FeatureSet) -> dict:
        """Spiritual scoring: D1+D20, 12th, 9th, Ketu, Jupiter."""
        h12 = AstrologicalScoringEngine._score_house(12, features)
        h9 = AstrologicalScoringEngine._score_house(9, features)
        h8 = AstrologicalScoringEngine._score_house(8, features)
        jupiter = AstrologicalScoringEngine._score_planet("Jupiter", features)
        ketu_data = features.strength.get("Ketu", features.strength.get("Saturn", {}))
        ketu_score = 0.5  # Ketu doesn't have standard dignity, use neutral

        score = (0.25 * h12) + (0.20 * h9) + (0.15 * h8) + (0.25 * jupiter) + (0.15 * ketu_score)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Spirituality & Moksha"
        }

    @staticmethod
    def score_foreign_travel(features: FeatureSet) -> dict:
        """Foreign settlement/travel scoring: D1+D4, 12th, 9th, Rahu."""
        h12 = AstrologicalScoringEngine._score_house(12, features)
        h9 = AstrologicalScoringEngine._score_house(9, features)
        h7 = AstrologicalScoringEngine._score_house(7, features)
        moon = AstrologicalScoringEngine._score_planet("Moon", features)

        # Rahu influence: check if Rahu is in 12th, 9th, or 7th
        rahu_boost = 0.0
        rahu_house = features.positional.get("Rahu", {}).get("house", 0)
        if rahu_house in [12, 9, 7]:
            rahu_boost = 0.2

        score = (0.30 * h12) + (0.25 * h9) + (0.15 * h7) + (0.15 * moon) + rahu_boost
        score = min(1.0, score)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Foreign Travel & Settlement"
        }

    @staticmethod
    def score_property(features: FeatureSet) -> dict:
        """Property/Real Estate scoring: D1+D4, 4th house, Mars."""
        h4 = AstrologicalScoringEngine._score_house(4, features)
        h2 = AstrologicalScoringEngine._score_house(2, features)
        h11 = AstrologicalScoringEngine._score_house(11, features)
        mars = AstrologicalScoringEngine._score_planet("Mars", features)

        score = (0.35 * h4) + (0.20 * h2) + (0.15 * h11) + (0.30 * mars)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Property & Real Estate"
        }

    @staticmethod
    def score_vehicle(features: FeatureSet) -> dict:
        """Vehicle/Luxury scoring: D1+D16, 4th house, Venus."""
        h4 = AstrologicalScoringEngine._score_house(4, features)
        venus = AstrologicalScoringEngine._score_planet("Venus", features)

        score = (0.50 * h4) + (0.50 * venus)
        return {
            "raw_score": round(score, 3),
            "astrological_strength_band": "HIGH" if score > 0.6 else ("MEDIUM" if score > 0.4 else "LOW"),
            "domain": "Vehicles & Luxuries"
        }

    @classmethod
    def score_all_domains(cls, features: FeatureSet) -> dict:
        """Score all life domains and return consolidated results."""
        return {
            "career": cls.score_career(features),
            "marriage": cls.score_marriage(features),
            "wealth": cls.score_wealth(features),
            "health": cls.score_health(features),
            "education": cls.score_education(features),
            "children": cls.score_children(features),
            "spiritual": cls.score_spiritual(features),
            "foreign_travel": cls.score_foreign_travel(features),
            "property": cls.score_property(features),
            "vehicle": cls.score_vehicle(features),
        }
