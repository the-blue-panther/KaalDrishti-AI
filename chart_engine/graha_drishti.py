"""
Graha Drishti (ग्रह दृष्टि) - Planetary Aspects System
======================================================

Implements the complete Vedic planetary aspect (drishti) system.

Key Rules (BPHS Ch. 26):
1. ALL planets aspect the 7th house from themselves (100% strength)
2. SPECIAL ASPECTS:
   - Jupiter (Guru): 5th, 7th, 9th houses
   - Mars (Mangal): 4th, 7th, 8th houses
   - Saturn (Shani): 3rd, 7th, 10th houses
3. Rahu/Ketu aspect like Jupiter (5,7,9) in modern interpretation
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"

BENEFICS = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}
MALEFICS = {Planet.SUN, Planet.MARS, Planet.SATURN}

SPECIAL_ASPECTS: Dict[Planet, List[int]] = {
    Planet.SUN: [],
    Planet.MOON: [],
    Planet.MARS: [4, 8],
    Planet.MERCURY: [],
    Planet.JUPITER: [5, 9],
    Planet.VENUS: [],
    Planet.SATURN: [3, 10],
    Planet.RAHU: [5, 7, 9],
    Planet.KETU: [5, 7, 9],
}

FULL_ASPECT = 60.0
THREE_QUARTER = 45.0
HALF = 30.0
QUARTER = 15.0


@dataclass
class AspectResult:
    aspect_matrix: Dict[str, Dict[str, float]]
    total_received: Dict[str, float]
    total_cast: Dict[str, float]
    benefic_count: Dict[str, int]
    malefic_count: Dict[str, int]
    most_aspected: str
    least_aspected: str

    def to_dict(self) -> dict:
        return {
            "aspect_matrix": self.aspect_matrix,
            "total_aspect_received": {k: round(v, 1) for k, v in self.total_received.items()},
            "total_aspect_cast": {k: round(v, 1) for k, v in self.total_cast.items()},
            "benefic_aspects_count": self.benefic_count,
            "malefic_aspects_count": self.malefic_count,
            "most_aspected_planet": self.most_aspected,
            "least_aspected_planet": self.least_aspected,
        }


class GrahaDrishtiEngine:
    """Complete Vedic planetary aspect calculation engine."""

    @staticmethod
    def _rel_house(from_house: int, to_house: int) -> int:
        """Get relative house (1-12) from one house to another."""
        return ((to_house - from_house) % 12) + 1

    @classmethod
    def calculate_aspect_strength(cls, asp_planet: Planet, from_house: int, to_house: int) -> float:
        """Calculate aspect strength from a planet to a target house."""
        rel = cls._rel_house(from_house, to_house)
        special = SPECIAL_ASPECTS.get(asp_planet, [])
        all_aspect = [7] + special

        if rel in all_aspect:
            return FULL_ASPECT

        for ah in all_aspect:
            diff = min(abs(rel - ah), 12 - abs(rel - ah))
            if diff == 1:
                return THREE_QUARTER
            elif diff == 2:
                return HALF
            elif diff == 3:
                return QUARTER

        return 0.0

    @classmethod
    def calculate_aspect_matrix(cls, planet_houses: Dict[str, int]) -> AspectResult:
        """Calculate complete aspect matrix for all planets."""
        matrix: Dict[str, Dict[str, float]] = {}
        total_received: Dict[str, float] = {}
        total_cast: Dict[str, float] = {}
        ben_count: Dict[str, int] = {}
        mal_count: Dict[str, int] = {}

        for p in planet_houses:
            matrix[p] = {}
            total_received[p] = 0.0
            total_cast[p] = 0.0
            ben_count[p] = 0
            mal_count[p] = 0

        for asp_name, asp_house in planet_houses.items():
            try:
                asp_planet = Planet(asp_name)
            except ValueError:
                continue

            is_benefic = asp_planet in BENEFICS

            for tgt_name, tgt_house in planet_houses.items():
                if asp_name == tgt_name:
                    continue

                strength = cls.calculate_aspect_strength(asp_planet, asp_house, tgt_house)
                if strength > 0:
                    matrix[tgt_name][asp_name] = round(strength, 1)
                    total_received[tgt_name] += strength
                    total_cast[asp_name] += strength
                    if is_benefic:
                        ben_count[tgt_name] += 1
                    else:
                        mal_count[tgt_name] += 1

        most = max(total_received, key=total_received.get) if total_received else "N/A"
        least = min(total_received, key=total_received.get) if total_received else "N/A"

        return AspectResult(
            aspect_matrix=matrix,
            total_received={k: round(v, 1) for k, v in total_received.items()},
            total_cast={k: round(v, 1) for k, v in total_cast.items()},
            benefic_count=ben_count,
            malefic_count=mal_count,
            most_aspected=most,
            least_aspected=least,
        )

    @classmethod
    def get_aspects_on_planet(cls, target: str, planet_houses: Dict[str, int]) -> Dict[str, float]:
        """Get all aspects received by a specific planet."""
        result = cls.calculate_aspect_matrix(planet_houses)
        return result.aspect_matrix.get(target, {})

    @classmethod
    def get_aspects_by_planet(cls, aspecting: str, planet_houses: Dict[str, int]) -> Dict[str, float]:
        """Get all aspects cast by a specific planet."""
        result = cls.calculate_aspect_matrix(planet_houses)
        cast = {}
        for tgt, asp_by in result.aspect_matrix.items():
            if aspecting in asp_by:
                cast[tgt] = asp_by[aspecting]
        return cast

    @classmethod
    def get_drik_bala_contribution(cls, planet_houses: Dict[str, int]) -> Dict[str, float]:
        """Calculate Drik Bala contribution for Shadbala from aspects."""
        result = cls.calculate_aspect_matrix(planet_houses)
        drik = {}
        for planet, aspects in result.aspect_matrix.items():
            net = 0.0
            for asp_by, strength in aspects.items():
                try:
                    p = Planet(asp_by)
                except ValueError:
                    continue
                if p in BENEFICS:
                    net += strength
                elif p in MALEFICS:
                    net -= strength * 0.5
            drik[planet] = max(0.0, min(60.0, 30.0 + net))
        return {k: round(v, 1) for k, v in drik.items()}


if __name__ == "__main__":
    engine = GrahaDrishtiEngine()
    test = {"Sun": 5, "Moon": 1, "Mars": 9, "Mercury": 4, "Jupiter": 11, "Venus": 6, "Saturn": 2}
    result = engine.calculate_aspect_matrix(test)
    print("=" * 50)
    print("GRAHA DRISHTI RESULTS")
    print("=" * 50)
    for p, aspects in result.aspect_matrix.items():
        if aspects:
            asp_list = ", ".join(f"{a}={v:.0f}" for a, v in sorted(aspects.items()))
            print(f"  {p} ← {asp_list}")
    print(f"\nMost Aspected: {result.most_aspected}")
    print(f"Least Aspected: {result.least_aspected}")
    print("\nDrik Bala:", engine.get_drik_bala_contribution(test))
