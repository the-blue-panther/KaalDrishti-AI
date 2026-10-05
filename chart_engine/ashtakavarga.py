"""
Ashtakavarga (अष्टकवर्ग) - The Eight-Fold Point System
========================================================

The most sophisticated transit prediction tool in Vedic astrology.
Each of the 7 planets + Lagna contributes Bindus (0-8 points) to every
house/sign, creating a comprehensive strength matrix.

Key concepts:
1. Bhinnashtakavarga - Individual planet's point distribution (8 per sign)
2. Sarvashtakavarga - Sum of all 7 planets' points (7-56 per sign)
3. Samudaya Ashtakavarga - Combined total including Lagna
4. Trikona Shodhana - Triangular reduction for auspiciousness
5. Ekadhipatya Shodhana - Single lordship reduction

Reference: Brihat Parashara Hora Shastra, Chapters 63-71
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    LAGNA = "Lagna"

# Benefic/Malefic classification for Ashtakavarga
BENEFICS = {Planet.MERCURY, Planet.JUPITER, Planet.VENUS, Planet.MOON}
MALEFICS = {Planet.SUN, Planet.MARS, Planet.SATURN}

# ============================================================
# BHINNASHTAKAVARGA RULES — Each planet's benefic positions
# Based on BPHS Chapter 64-70
# ============================================================

# For each planet, which houses/signs (relative to the planet's position)
# give 1 Bindu (benefic point).
# Format: {planet: {relative_house: list_of_additional_planet_conditions}}

# Source-derived Bhinnashtakavarga bindu matrix.
# Each planet receives one bindu for every qualifying relative position
# of the seven planets and Ascendant.
BHINNA_RULES: Dict[Planet, Dict[str, List[int]]] = {
    Planet.SUN: {
        "Sun": [1,2,4,7,8,9,10,11], "Moon": [3,6,10,11],
        "Mars": [1,2,4,7,8,9,10,11], "Mercury": [3,5,6,9,10,11,12],
        "Jupiter": [5,6,9,11], "Venus": [6,7,12],
        "Saturn": [1,2,4,7,8,9,10,11], "Ascendant": [3,4,6,10,11,12]
    },
    Planet.MOON: {
        "Sun": [3,6,7,8,10,11], "Moon": [1,3,6,7,10,11],
        "Mars": [2,3,5,6,9,10,11], "Mercury": [1,3,4,5,7,8,10,11],
        "Jupiter": [1,4,7,8,10,11,12], "Venus": [3,4,5,7,9,10,11],
        "Saturn": [3,5,6,11], "Ascendant": [3,6,10,11]
    },
    Planet.MARS: {
        "Sun": [3,5,6,10,11], "Moon": [3,6,11],
        "Mars": [1,2,4,7,8,10,11], "Mercury": [3,5,6,11],
        "Jupiter": [6,10,11,12], "Venus": [6,8,11,12],
        "Saturn": [1,4,7,8,9,10,11], "Ascendant": [1,3,6,10,11]
    },
    Planet.MERCURY: {
        "Sun": [5,6,9,11,12], "Moon": [2,4,6,8,10,11],
        "Mars": [1,2,4,7,8,9,10,12], "Mercury": [1,3,5,6,9,10,11,12],
        "Jupiter": [6,8,11,12], "Venus": [1,2,3,4,5,8,9,11],
        "Saturn": [1,2,4,7,8,9,10,12], "Ascendant": [1,2,4,6,8,10,11]
    },
    Planet.JUPITER: {
        "Sun": [1,2,3,4,7,8,9,10,11], "Moon": [2,5,7,9,11],
        "Mars": [1,2,4,7,8,10,11], "Mercury": [1,2,4,5,6,9,10,11],
        "Jupiter": [1,2,3,4,7,8,10,11], "Venus": [2,5,6,9,10,11],
        "Saturn": [3,5,6,12], "Ascendant": [1,2,4,5,6,7,9,10,11]
    },
    Planet.VENUS: {
        "Sun": [8,11,12], "Moon": [1,2,3,4,5,8,9,11,12],
        "Mars": [3,4,6,9,11,12], "Mercury": [3,5,6,9,11],
        "Jupiter": [5,8,9,10,11], "Venus": [1,2,3,4,5,8,9,10,11],
        "Saturn": [3,4,5,8,9,10,11], "Ascendant": [1,2,3,4,5,8,9,11]
    },
    Planet.SATURN: {
        "Sun": [1,2,4,7,8,10,11], "Moon": [3,6,11],
        "Mars": [3,5,6,10,11,12], "Mercury": [6,8,9,10,11,12],
        "Jupiter": [5,6,11,12], "Venus": [6,11,12],
        "Saturn": [3,5,6,11], "Ascendant": [1,3,4,6,10,11]
    },
}


@dataclass
class AshtakavargaResult:
    """Complete Ashtakavarga calculation result."""
    # Sign index is 1-12 (Aries..Pisces), independent of natal Lagna.
    bhinnashtakavarga: Dict[str, Dict[int, int]]

    # Sarvashtakavarga: Dict[sign_index, total_bindus] (sum of 7 planets)
    sarvashtakavarga: Dict[int, int]

    # Samudaya Ashtakavarga (with Lagna): Dict[sign_index, total]
    samudaya: Dict[int, int]

    # Trikona Shodhana results
    trikona_shodhana: Dict[int, int]

    # Ekadhipatya Shodhana results
    ekadhipatya_shodhana: Dict[int, int]

    # Interpretation
    strongest_sign: int
    weakest_sign: int
    average_bindus: float

    def to_dict(self) -> dict:
        return {
            "bhinnashtakavarga": self.bhinnashtakavarga,
            "sarvashtakavarga": self.sarvashtakavarga,
            "samudaya": self.samudaya,
            "trikona_shodhana": self.trikona_shodhana,
            "ekadhipatya_shodhana": self.ekadhipatya_shodhana,
            "strongest_sign": self.strongest_sign,
            "weakest_sign": self.weakest_sign,
            "average_bindus": self.average_bindus
        }


class AshtakavargaEngine:
    """
    Master engine for calculating the complete Ashtakavarga system.

    Usage:
        engine = AshtakavargaEngine()
        result = engine.calculate(
            planet_positions={"Sun": {"sign": 4, "house": 5}, ...},
            ascendant_sign=0  # Aries
        )
    """

    @staticmethod
    def _get_relative_house(planet_house: int, target_house: int) -> int:
        """
        Calculate target house number relative to planet's position.
        Example: If planet is in house 5, target house 8 is 4th from it.
        """
        diff = ((target_house - planet_house) % 12) + 1
        return diff

    @staticmethod
    def _calculate_planet_bindu(
        planet: Planet,
        planet_house: int,
        all_planet_houses: Dict[str, int]
    ) -> Dict[int, int]:
        """
        Calculate Bhinnashtakavarga (individual bindu points) for one planet.

        For each of the 12 houses:
        - Start with base benefic houses from the planet itself
        - Add bindus where other benefic planets contribute
        - Subtract where malefic planets contribute negatively

        Returns: Dict[house_number, bindu_count (0-8)]
        """
        bindus = {h: 0 for h in range(1, 13)}
        rules = BHINNA_RULES.get(planet, {})

        # The eight reference points contribute independently. There is no
        # separate benefic addition or malefic subtraction phase.
        for reference_name, relative_houses in rules.items():
            if reference_name == "Ascendant":
                reference_house = 1
            else:
                reference_house = all_planet_houses.get(reference_name)
                if reference_house is None:
                    continue

            for relative_house in relative_houses:
                absolute_house = ((reference_house + relative_house - 2) % 12) + 1
                bindus[absolute_house] += 1

        return {house: min(8, points) for house, points in bindus.items()}

    @staticmethod
    def _calculate_lagna_bindu(
        ascendant_house: int,
        all_planet_houses: Dict[str, int]
    ) -> Dict[int, int]:
        """
        Calculate Lagna's contribution to Ashtakavarga.
        Lagna adds bindus based on benefic planets in specific houses from it.
        """
        bindus = {h: 0 for h in range(1, 13)}

        # Lagna base: Kendras (1,4,7,10) and Konas (5,9) from Lagna = benefic
        for rel_house in [1, 2, 4, 5, 7, 9, 10]:
            abs_h = ((ascendant_house + rel_house - 2) % 12) + 1
            bindus[abs_h] += 1

        # Benefics contribute additional bindus
        for benefic in [Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON]:
            if benefic.value in all_planet_houses:
                benefic_house = all_planet_houses[benefic.value]
                for rel_h in [2, 4, 5, 7, 9, 11]:
                    abs_h = ((benefic_house + rel_h - 2) % 12) + 1
                    if bindus.get(abs_h, 0) < 8:
                        bindus[abs_h] += 1

        for h in bindus:
            bindus[h] = max(0, min(8, bindus[h]))

        return bindus

    @staticmethod
    def calculate_sarvashtakavarga(
        bhinnashtakavarga: Dict[str, Dict[int, int]]
    ) -> Dict[int, int]:
        """
        Sum all 7 planets' Bhinnashtakavarga to get Sarvashtakavarga.
        Range: 0-56 points per house.
        """
        sarva = {h: 0 for h in range(1, 13)}
        for planet, bindu_dict in bhinnashtakavarga.items():
            if planet == "Lagna":
                continue
            for house, points in bindu_dict.items():
                sarva[house] += points
        return sarva

    @staticmethod
    def trikona_shodhana(sarvashtakavarga: Dict[int, int]) -> Dict[int, int]:
        """
        Trikona Shodhana (Triangular Purification).

        Groups houses into 4 trikona sets:
        - Dharma Trikona: 1, 5, 9
        - Artha Trikona: 2, 6, 10
        - Kama Trikona: 3, 7, 11
        - Moksha Trikona: 4, 8, 12

        If all houses in a trikona have equal or more bindus than the
        minimum, they're reduced to the minimum value.
        """
        trikona_groups = {
            "Dharma": [1, 5, 9],
            "Artha": [2, 6, 10],
            "Kama": [3, 7, 11],
            "Moksha": [4, 8, 12],
        }

        shodhana = {}
        for group_name, houses in trikona_groups.items():
            bindus = [sarvashtakavarga[h] for h in houses]
            min_bindu = min(bindus)
            # Remove the common minimum from all three signs.
            # The minimum therefore becomes zero after Shodhana.
            for h in houses:
                shodhana[h] = max(0, sarvashtakavarga[h] - min_bindu)

        return shodhana

    @staticmethod
    def ekadhipatya_shodhana(
        trikona_result: Dict[int, int],
        sarvashtakavarga: Dict[int, int]
    ) -> Dict[int, int]:
        """
        Ekadhipatya Shodhana (Single Lordship Reduction).

        For houses ruled by the same planet (e.g., Aries-Scorpio by Mars),
        if the sign with fewer bindus has fewer than the other, reduce
        the greater to match the lesser.

                Same-lordship pairs: (1,8)=Mars, (2,7)=Venus, (3,6)=Mercury,
                             (9,12)=Jupiter, (10,11)=Saturn.
        Sun and Moon each rule only one sign, so they form no pair.
        """
        # Lordship mapping (sign index 0-based → house numbers 1-12)
        # Aries(0)=1, Taurus(1)=2, Gemini(2)=3, Cancer(3)=4, Leo(4)=5,
        # Virgo(5)=6, Libra(6)=7, Scorpio(7)=8, Sagittarius(8)=9,
        # Capricorn(9)=10, Aquarius(10)=11, Pisces(11)=12

                # Pair only signs that are actually ruled by the same planet.
        lord_pairs = [
            (1, 8),   # Mars: Aries, Scorpio
            (2, 7),   # Venus: Taurus, Libra
            (3, 6),   # Mercury: Gemini, Virgo
            (9, 12),  # Jupiter: Sagittarius, Pisces
            (10, 11), # Saturn: Capricorn, Aquarius
        ]

        result = dict(trikona_result)

        for h1, h2 in lord_pairs:
            v1 = result.get(h1, sarvashtakavarga.get(h1, 0))
            v2 = result.get(h2, sarvashtakavarga.get(h2, 0))

            if v1 < v2:
                result[h2] = v1
            elif v2 < v1:
                result[h1] = v2

        return result

    @classmethod
    def calculate(
        cls,
        planet_positions: Dict[str, Dict[str, int]],
        ascendant_house: int = 1
    ) -> AshtakavargaResult:
        """
        Calculate complete Ashtakavarga for all planets + Lagna.

        Args:
            planet_positions: Dict like {"Sun": {"sign": 5}, ...}; 1=Aries..12=Pisces.
            ascendant_house: Legacy parameter name; pass the Lagna sign index (1-12).

        Returns:
            AshtakavargaResult with all components
        """
        # Extract house numbers for all planets
        all_planet_houses: Dict[str, int] = {}
        for p_name, data in planet_positions.items():
            if isinstance(data, dict):
                # Read legacy "house" as a compatibility fallback, but prefer
                # explicit zodiac-sign coordinates for all new callers.
                all_planet_houses[p_name] = data.get("sign", data.get("house", 1))
            else:
                all_planet_houses[p_name] = int(data)

        # 1. Bhinnashtakavarga for each of the 7 classical planets
        bhinnashtakavarga: Dict[str, Dict[int, int]] = {}

        for planet in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                        Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
            planet_name = planet.value
            if planet_name in all_planet_houses:
                planet_house = all_planet_houses[planet_name]
                bhinnashtakavarga[planet_name] = cls._calculate_planet_bindu(
                    planet, planet_house, all_planet_houses
                )

        # 2. Lagna bindu
        bhinnashtakavarga["Lagna"] = cls._calculate_lagna_bindu(
            ascendant_house, all_planet_houses
        )

        # 3. Sarvashtakavarga (sum of 7 planets)
        sarva = cls.calculate_sarvashtakavarga(bhinnashtakavarga)

        # 4. Samudaya Ashtakavarga (including Lagna)
        samudaya = {h: sarva[h] + bhinnashtakavarga["Lagna"].get(h, 0)
                    for h in range(1, 13)}

        # 5. Trikona Shodhana
        trikona = cls.trikona_shodhana(sarva)

        # 6. Ekadhipatya Shodhana
        ekadhipatya = cls.ekadhipatya_shodhana(trikona, sarva)

        # Find strongest and weakest
        # Indexing makes the key function's return type unambiguously ``int``;
        # ``dict.get`` is typed as potentially returning ``None`` by current
        # Python type checkers, even though every key is populated above.
        strongest = max(sarva, key=lambda house: sarva[house])
        weakest = min(sarva, key=lambda house: sarva[house])
        avg = sum(sarva.values()) / 12.0

        return AshtakavargaResult(
            bhinnashtakavarga=bhinnashtakavarga,
            sarvashtakavarga=sarva,
            samudaya=samudaya,
            trikona_shodhana=trikona,
            ekadhipatya_shodhana=ekadhipatya,
            strongest_sign=strongest,
            weakest_sign=weakest,
            average_bindus=round(avg, 2)
        )

    @classmethod
    def get_transit_effect(
        cls,
        ashtakavarga: AshtakavargaResult,
        transiting_planet: str,
        transiting_house: int
    ) -> str:
        """
        Assess a configured transit from the SAV bindus for a zodiac sign
        (1=Aries..12=Pisces); this is a geometric lookup, not a validated effect.

        - 0-2 bindus: Very malefic transit
        - 3-4 bindus: Neutral
        - 5-6 bindus: Benefic transit
        - 7-8 bindus: Very benefic transit
        """
        sarva = ashtakavarga.sarvashtakavarga
        bindu = sarva.get(transiting_house, 0)

        if bindu <= 18:
            return "Very Malefic"
        elif bindu <= 24:
            return "Malefic"
        elif bindu <= 30:
            return "Neutral"
        elif bindu <= 36:
            return "Benefic"
        else:
            return "Very Benefic"


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    engine = AshtakavargaEngine()

    # Test with sample positions
    test_positions = {
        "Sun": {"house": 5},
        "Moon": {"house": 1},
        "Mars": {"house": 9},
        "Mercury": {"house": 4},
        "Jupiter": {"house": 11},
        "Venus": {"house": 6},
        "Saturn": {"house": 2},
    }

    result = engine.calculate(test_positions, ascendant_house=1)

    print("=" * 60)
    print("ASHTAKAVARGA RESULTS")
    print("=" * 60)

    print("\nBhinnashtakavarga (Individual Planet Bindus):")
    for planet, bindus in result.bhinnashtakavarga.items():
        print(f"  {planet}: {dict(sorted(bindus.items()))}")

    print("\nSarvashtakavarga (Sum of 7 Planets):")
    for h in range(1, 13):
        bar = "█" * result.sarvashtakavarga[h]
        print(f"  House {h:2d}: {result.sarvashtakavarga[h]:2d} bindus |{bar}")

    print(f"\nStrongest House: {result.strongest_house} ({result.sarvashtakavarga[result.strongest_house]} bindus)")
    print(f"Weakest House: {result.weakest_house} ({result.sarvashtakavarga[result.weakest_house]} bindus)")
    print(f"Average Bindus: {result.average_bindus}")

    print("\nTrikona Shodhana:", dict(sorted(result.trikona_shodhana.items())))
    print("Ekadhipatya Shodhana:", dict(sorted(result.ekadhipatya_shodhana.items())))

    print("\n" + "=" * 60)
    print("TRANSIT EFFECT ASSESSMENT (Jupiter transiting House 5):")
    print(f"  Effect: {engine.get_transit_effect(result, 'Jupiter', 5)}")
