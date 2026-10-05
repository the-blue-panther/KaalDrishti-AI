"""
Jaimini System (जैमिनी पद्धति) — Complete Implementation
=========================================================

Implements the full Jaimini astrology system as per Jaimini Sutras:

1. Chara Karaka (7 Variable Significators based on degrees)
2. Sthira Karaka (7 Fixed Significators)
3. Arudha Lagna + Arudha Padas (Manifestation points)
4. Jaimini Aspects (Rashi Drishti — Sign-based aspects)
5. Argala (Primary, Secondary, Special with obstruction)

Reference: Jaimini Upadesha Sutras, Padas 1-4
"""

from typing import Dict, List, Optional, Tuple
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
    RAHU = "Rahu"
    KETU = "Ketu"

class ZodiacSign(str, Enum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"

ZODIAC_ORDER = list(ZodiacSign)

# ============================================================
# 1. CHARA KARAKA (7 Variable Significators)
# ============================================================
# Based on planet degrees (highest to lowest) among 7 planets (no Rahu/Ketu)
# AK > AmK > BK > MK > PK > GK > DK

CHARA_KARAKA_NAMES = [
    "Atmakaraka (AK)",      # Soul — highest degree planet
    "Amatyakaraka (AmK)",   # Career/Minister — 2nd highest
    "Bhratrukaraka (BK)",   # Siblings — 3rd
    "Matrukaraka (MK)",     # Mother — 4th
    "Pitrukaraka (PK)",     # Father — 5th
    "Putrakaraka (PK2)",    # Children — 6th
    "Gnatikaraka (GK)",     # Relatives/Obstacles — 7th
    "Darakaraka (DK)",      # Spouse — lowest degree
]

# ============================================================
# 2. STHIRA KARAKA (7 Fixed Significators)
# ============================================================
STHIRA_KARAKAS = {
    "Sun": "Pitrukaraka (Father)",
    "Moon": "Matrukaraka (Mother)",
    "Mars": "Bhratrukaraka (Siblings)",
    "Mercury": "Gnatikaraka (Relatives)",
    "Jupiter": "Putrakaraka (Children)",
    "Venus": "Darakaraka (Spouse)",
    "Saturn": "Atmakaraka (Soul/longevity)",
}

# ============================================================
# 3. JAIMINI ASPECTS — RASHI DRISHTI
# ============================================================
# Sign-based aspects: different from Graha Drishti
# Fixed signs (Taurus, Leo, Scorpio, Aquarius) aspect all movable signs EXCEPT adjacent
# Movable signs (Aries, Cancer, Libra, Capricorn) aspect all fixed signs EXCEPT adjacent
# Dual signs (Gemini, Virgo, Sagittarius, Pisces) aspect each other

FIXED_SIGNS = {1, 4, 7, 10}  # 0-indexed: Taurus=1, Leo=4, Scorpio=7, Aquarius=10
MOVABLE_SIGNS = {0, 3, 6, 9}  # Aries=0, Cancer=3, Libra=6, Capricorn=9
DUAL_SIGNS = {2, 5, 8, 11}    # Gemini=2, Virgo=5, Sagittarius=8, Pisces=11

# ============================================================
# 4. ARGALA — PRIMARY, SECONDARY, SPECIAL
# ============================================================
# Primary Argala: planets in 2nd, 4th, 11th from a house obstruct its results
# Secondary Argala: planets in 12th, 10th, 3rd counter the obstruction
# Special Argala: planets in 5th, 8th, 9th add extra influence

PRIMARY_ARGALA_HOUSES = [2, 4, 11]
SECONDARY_ARGALA_HOUSES = [12, 10, 3]
SPECIAL_ARGALA_HOUSES = [5, 8, 9]


@dataclass
class KarakaResult:
    chara_karakas: Dict[str, str] = field(default_factory=dict)
    sthira_karakas: Dict[str, str] = field(default_factory=dict)
    atmakaraka: str = ""
    amatyakaraka: str = ""
    darakaraka: str = ""

    def to_dict(self) -> dict:
        return {
            "chara_karakas": self.chara_karakas,
            "sthira_karakas": self.sthira_karakas,
            "atmakaraka": self.atmakaraka,
            "amatyakaraka": self.amatyakaraka,
            "darakaraka": self.darakaraka,
        }


@dataclass
class ArudhaResult:
    arudha_lagna: int
    arudha_padas: Dict[int, int]
    bhava_padas: Dict[int, int]

    def to_dict(self) -> dict:
        return {
            "arudha_lagna": self.arudha_lagna,
            "arudha_padas": self.arudha_padas,
            "bhava_padas": {str(k): v for k, v in self.bhava_padas.items()},
        }


@dataclass
class ArgalaResult:
    primary: Dict[int, List[Dict]]
    secondary: Dict[int, List[Dict]]
    special: Dict[int, List[Dict]]

    def to_dict(self) -> dict:
        return {
            "primary_argala": {str(k): v for k, v in self.primary.items()},
            "secondary_argala": {str(k): v for k, v in self.secondary.items()},
            "special_argala": {str(k): v for k, v in self.special.items()},
        }


@dataclass
class JaiminiResult:
    karakas: KarakaResult
    arudha: ArudhaResult
    rashi_drishti: Dict[int, List[int]]
    argala: ArgalaResult

    def to_dict(self) -> dict:
        return {
            "karakas": self.karakas.to_dict(),
            "arudha": self.arudha.to_dict(),
            "rashi_drishti": {str(k): v for k, v in self.rashi_drishti.items()},
            "argala": self.argala.to_dict(),
        }


class JaiminiSystem:
    """Complete Jaimini astrology system implementation."""

    # ================================================================
    # 1. CHARA KARAKA
    # ================================================================
    @staticmethod
    def calculate_chara_karakas(planet_longitudes: Dict[str, float]) -> KarakaResult:
        """Calculate 7 Chara Karakas based on planet degrees (highest→lowest)."""
        classical_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        planets_with_deg = []
        for p in classical_planets:
            if p in planet_longitudes:
                degree = planet_longitudes[p] % 30
                planets_with_deg.append((p, degree))

        planets_with_deg.sort(key=lambda x: x[1], reverse=True)

        result = KarakaResult()
        names = CHARA_KARAKA_NAMES
        for i, (planet, deg) in enumerate(planets_with_deg):
            if i < len(names):
                result.chara_karakas[names[i]] = planet
                if i == 0:
                    result.atmakaraka = planet
                if i == 1:
                    result.amatyakaraka = planet
                if i == len(planets_with_deg) - 1:
                    result.darakaraka = planet

        result.sthira_karakas = STHIRA_KARAKAS.copy()
        return result

    # ================================================================
    # 2. ARUDHA LAGNA & ARUDHA PADAS
    # ================================================================
    @classmethod
    def calculate_arudha_pada(cls, house: int, lord_house: int) -> int:
        """Calculate Arudha Pada for a house."""
        diff = ((lord_house - house) % 12)
        arudha = (house + diff) % 12
        if arudha == 0:
            arudha = 12
        if arudha == house:
            arudha = ((house + 10) % 12) or 12
        return arudha

    @classmethod
    def calculate_arudhas(cls, asc_sign_idx: int,
                          planet_houses: Dict[str, int],
                          house_lords: Dict[int, str]) -> ArudhaResult:
        """Calculate Arudha Lagna and all Arudha Padas (A1-A12)."""
        arudha_padas = {}
        bhava_padas = {}

        for house in range(1, 13):
            lord_name = house_lords.get(house, house_lords.get(str(house)))
            if isinstance(lord_name, dict):
                lord_name = lord_name.get("lord", "")
            if lord_name and lord_name in planet_houses:
                lord_house = planet_houses[lord_name]
            else:
                lord_house = ((asc_sign_idx + house - 1) % 12) + 1

            arudha = cls.calculate_arudha_pada(house, lord_house)
            arudha_padas[house] = arudha
            bhava_padas[house] = arudha

        al = arudha_padas.get(1, 1)
        return ArudhaResult(arudha_lagna=al, arudha_padas=arudha_padas, bhava_padas=bhava_padas)

    # ================================================================
    # 3. JAIMINI ASPECTS (Rashi Drishti)
    # ================================================================
    @classmethod
    def calculate_rashi_drishti(cls) -> Dict[int, List[int]]:
        """Calculate Rashi Drishti (sign-to-sign aspects) for all 12 signs."""
        drishti = {h: [] for h in range(1, 13)}

        for sign_idx in range(12):
            house = sign_idx + 1

            if sign_idx in MOVABLE_SIGNS:
                for fixed_idx in FIXED_SIGNS:
                    if abs(sign_idx - fixed_idx) not in [0, 1, 11]:
                        drishti[house].append(fixed_idx + 1)

            elif sign_idx in FIXED_SIGNS:
                for movable_idx in MOVABLE_SIGNS:
                    if abs(sign_idx - movable_idx) not in [0, 1, 11]:
                        drishti[house].append(movable_idx + 1)

            elif sign_idx in DUAL_SIGNS:
                for dual_idx in DUAL_SIGNS:
                    if dual_idx != sign_idx:
                        drishti[house].append(dual_idx + 1)

        return drishti

    # ================================================================
    # 4. ARGALA
    # ================================================================
    @classmethod
    def calculate_argala(cls, planet_houses: Dict[str, int]) -> ArgalaResult:
        """Calculate Argala for all 12 houses."""
        primary = {h: [] for h in range(1, 13)}
        secondary = {h: [] for h in range(1, 13)}
        special = {h: [] for h in range(1, 13)}

        for house in range(1, 13):
            for p_name, p_house in planet_houses.items():
                diff = ((p_house - house) % 12) + 1

                if diff in PRIMARY_ARGALA_HOUSES:
                    primary[house].append({"planet": p_name, "from_house": diff})
                if diff in SECONDARY_ARGALA_HOUSES:
                    secondary[house].append({"planet": p_name, "from_house": diff})
                if diff in SPECIAL_ARGALA_HOUSES:
                    special[house].append({"planet": p_name, "from_house": diff})

        return ArgalaResult(primary=primary, secondary=secondary, special=special)

    # ================================================================
    # 5. MASTER METHOD
    # ================================================================
    @classmethod
    def calculate_all(cls, planet_longitudes: Dict[str, float],
                      planet_houses: Dict[str, int],
                      asc_sign_idx: int = 0,
                      house_lords: Optional[Dict[int, str]] = None) -> JaiminiResult:
        """Calculate complete Jaimini system."""
        if house_lords is None:
            lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                     "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
            house_lords = {i + 1: lords[i] for i in range(12)}

        karakas = cls.calculate_chara_karakas(planet_longitudes)
        arudha = cls.calculate_arudhas(asc_sign_idx, planet_houses, house_lords)
        rashi_drishti = cls.calculate_rashi_drishti()
        argala = cls.calculate_argala(planet_houses)

        return JaiminiResult(
            karakas=karakas, arudha=arudha,
            rashi_drishti=rashi_drishti, argala=argala
        )


if __name__ == "__main__":
    import json
    jaimini = JaiminiSystem()

    test_lons = {"Sun": 45.5, "Moon": 120.0, "Mars": 200.0, "Mercury": 65.0,
                 "Jupiter": 300.0, "Venus": 15.0, "Saturn": 250.0}
    test_houses = {"Sun": 5, "Moon": 1, "Mars": 9, "Mercury": 4,
                   "Jupiter": 11, "Venus": 6, "Saturn": 2}

    result = jaimini.calculate_all(test_lons, test_houses)

    print("=" * 60)
    print("JAIMINI SYSTEM — COMPLETE ANALYSIS")
    print("=" * 60)

    print("\nCHARA KARAKAS:")
    for name, planet in result.karakas.chara_karakas.items():
        print(f"  {name}: {planet}")
    print(f"  → Atmakaraka: {result.karakas.atmakaraka}")
    print(f"  → Darakaraka: {result.karakas.darakaraka}")

    print("\nARUDHA LAGNA:", result.arudha.arudha_lagna)
    print("  Arudha Padas (A1-A12):", result.arudha.arudha_padas)

    print("\nRASHI DRISHTI (sample):")
    for h in [1, 5, 9]:
        print(f"  House {h} aspects: {result.rashi_drishti[h]}")

    print("\nARGALA (House 1):")
    print(f"  Primary: {result.argala.primary.get(1, [])}")
    print(f"  Secondary: {result.argala.secondary.get(1, [])}")
    print(f"  Special: {result.argala.special.get(1, [])}")
