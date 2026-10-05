from zoneinfo import ZoneInfo
from typing import Any, Dict
from datetime import timezone

from pydantic import BaseModel, ConfigDict

from chart_engine.chart_state import ChartState
from chart_engine.models import PlanetName, ZodiacSign
from feature_extraction.dictionaries import SIGN_LORDS, determine_full_dignity

class FeatureSet(BaseModel):
    """Explicit semantic projection of the canonical ChartState."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    positional: Dict[str, Any]
    strength: Dict[str, Any]
    relational: Dict[str, Any]
    temporal: Dict[str, Any]
    composite: Dict[str, Any]

class FeatureExtractor:
    @staticmethod
    def extract_positional(chart: ChartState) -> Dict:
        """Project canonical planetary positions into semantic feature records."""
        return {
            planet.value: {
                "sign": position.sign.value,
                "house": position.house_number,
                "nakshatra_idx": position.nakshatra_index,
                "is_retrograde": position.is_retrograde,
            }
            for planet, position in chart.planetary_positions.items()
        }

    @staticmethod
    def extract_strength(chart: ChartState) -> Dict:
        """Project canonical positions into the existing full dignity model."""
        all_planet_houses = {
            planet.value: position.house_number
            for planet, position in chart.planetary_positions.items()
        }
        str_feats = {}

        for planet, position in chart.planetary_positions.items():
            dignity = determine_full_dignity(
                planet,
                position.sign,
                position.longitude_ecliptic % 30.0,
                position.house_number,
                all_planet_houses,
            )
            str_feats[planet.value] = {
                "dignity": dignity,
                "is_retrograde": position.is_retrograde,
            }

        return str_feats

    @staticmethod
    def extract_relational(chart: ChartState) -> Dict:
        """Derive house lordships from the canonical Ascendant and positions."""
        from chart_engine.coordinate_transformer import ZODIAC_ORDER

        rel = {"house_lords": {}}
        asc_idx = ZODIAC_ORDER.index(chart.metadata.ascendant)

        for house_offset in range(12):
            house_num = house_offset + 1
            sign_enum = ZODIAC_ORDER[(asc_idx + house_offset) % 12]
            lord = SIGN_LORDS.get(sign_enum)
            if lord and lord in chart.planetary_positions:
                rel["house_lords"][house_num] = {
                    "lord": lord.value,
                    "lord_is_in_house": chart.planetary_positions[lord].house_number,
                }

        return rel

    @staticmethod
    def extract_temporal(chart: ChartState) -> Dict:
        """Project dasha state using the chart's explicit calculation reference time."""
        from chart_engine.vimshottari_dasha import VimshottariDasha

        dasha_dict = chart.dasha_timeline
        dasha_array = dasha_dict.get("Vimshottari", [])
        component_status = chart.metadata.component_status
        system_quality = {
            "Vimshottari": component_status.get("vimshottari", "unknown"),
            "Yogini": component_status.get("yogini_dasha", "unknown"),
            "Ashtottari": component_status.get("ashtottari_dasha", "unknown"),
        }
        if not dasha_array:
            return {
                "active_mahadasha": "Unknown",
                "active_antardasha": "Unknown",
                "active_pratyantardasha": "Unknown",
                "upcoming_dasha_sequence": [],
                "yogini_dasha_sequence": dasha_dict.get("Yogini", []),
                "ashtottari_dasha_sequence": dasha_dict.get("Ashtottari", []),
                "dasha_system_quality": system_quality,
            }

        # Dasha boundaries use the chart's UT Julian Day and are stored as
        # naive UTC for legacy compatibility. Compare in that same time basis
        # using the explicit replay instant, never the wall-clock execution time.
        reference_time = chart.metadata.reference_time_utc.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

        active = VimshottariDasha.get_current_dasha(dasha_array, reference_time)
        horizon = VimshottariDasha.get_dasha_horizon(
            dasha_array,
            reference_time,
            horizon_years=25,
        )

        return {
            "active_mahadasha": active.get("mahadasha", "Unknown"),
            "active_antardasha": active.get("antardasha", "Unknown"),
            "active_pratyantardasha": active.get("pratyantardasha", "Unknown"),
            "upcoming_dasha_sequence": horizon,
            "yogini_dasha_sequence": dasha_dict.get("Yogini", []),
            "ashtottari_dasha_sequence": dasha_dict.get("Ashtottari", []),
            "dasha_system_quality": system_quality,
        }

    @staticmethod
    def extract_composite(chart: ChartState, strength: dict, relational: dict = None) -> Dict:
        """
        Layer 5: Full yoga detection using YogaDetector + combustion/planetary war data.
        """
        from chart_engine.yoga_detector import YogaDetector

        planet_houses = {
            planet.value: position.house_number
            for planet, position in chart.planetary_positions.items()
        }
        dignities = {name: data["dignity"] for name, data in strength.items()}

        house_lords = {}
        relational_data = relational or {}
        for h_num, h_data in relational_data.get("house_lords", {}).items():
            if isinstance(h_data, dict):
                house_lords[int(h_num)] = h_data

        yoga_result = YogaDetector.detect_all(
            planet_houses,
            dignities=dignities,
            house_lords=house_lords,
        )

        combustion_data = chart.combustion
        combust_planets = [
            planet
            for planet, status in combustion_data.get("combustion_status", {}).items()
            if status
        ]
        planetary_wars = combustion_data.get("planetary_wars", [])

        return {
            "yogas": [y["name"] for y in yoga_result.detected_yogas],
            "yoga_details": yoga_result.detected_yogas,
            "yoga_categories": yoga_result.yoga_categories,
            "total_yogas": yoga_result.total_yogas,
            "combust_planets": combust_planets,
            "planetary_wars": planetary_wars,
        }

    @classmethod
    def generate_features(cls, chart: ChartState) -> FeatureSet:
        """
        Orchestrates all 5 layers securely into Pydantic enforcement.
        Now uses full 7-tier dignity, YogaDetector, and combustion data.
        """
        pos = cls.extract_positional(chart)
        strength = cls.extract_strength(chart)
        relational = cls.extract_relational(chart)

        return FeatureSet(
            positional=pos,
            strength=strength,
            relational=relational,
            temporal=cls.extract_temporal(chart),
            composite=cls.extract_composite(chart, strength, relational),
        )
