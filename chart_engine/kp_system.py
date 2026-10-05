"""
KP System (कृष्णमूर्ति पद्धति) - Krishnamurti Paddhati
=============================================================

Implements the complete KP (Krishnamurti Paddhati) astrology system:

1. Sub-Lords (249 sub-divisions of Vimshottari Dasha within each star)
2. Cuspal Sub-Lords (House cusp exact sub-lord calculation)
3. Ruling Planets (Day lord, Moon star lord, Moon sign lord, Ascendant star lord)
4. KP Ayanamsa (Newcomb/Wilkins/KP ayanamsa)

Reference: KP Readers 1-6 by K.S. Krishnamurti
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


# Vimshottari Dasha lords (9) with their years
DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]

# 27 Nakshatras
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Approximate KP ayanamsa reference for 2026.
# This module uses a simplified linear model; exact KP ayanamsa is date-dependent.
KP_AYANAMSA_2026 = 24.12  # degrees


@dataclass
class SubLord:
    """Represents a sub-lord (sub-division of a nakshatra pada)."""
    nakshatra: str
    nakshatra_index: int
    pada: int
    vimshottari_lord: str
    sub_lord: str
    sub_lord_span: float  # degrees
    sub_lord_start: float  # absolute longitude start

    def to_dict(self) -> dict:
        return {
            "nakshatra": self.nakshatra, "nakshatra_index": self.nakshatra_index,
            "pada": self.pada, "vimshottari_lord": self.vimshottari_lord,
            "sub_lord": self.sub_lord, "sub_lord_span": round(self.sub_lord_span, 4),
            "sub_lord_start": round(self.sub_lord_start, 4)
        }


@dataclass
class KPResult:
    """Complete KP system analysis."""
    # Sub-lords for all planets
    planet_sub_lords: Dict[str, SubLord]
    # Cuspal sub-lords for all 12 houses
    cuspal_sub_lords: Dict[int, SubLord]
    # Ruling planets at query time
    ruling_planets: Dict[str, str]
    # KP Ayanamsa used
    kp_ayanamsa: float
    # KP significators (houses signified by each planet)
    significators: Dict[str, List[int]]

    def to_dict(self) -> dict:
        return {
            "planet_sub_lords": {k: v.to_dict() for k, v in self.planet_sub_lords.items()},
            "cuspal_sub_lords": {str(k): v.to_dict() for k, v in self.cuspal_sub_lords.items()},
            "ruling_planets": self.ruling_planets,
            "kp_ayanamsa": self.kp_ayanamsa,
            "significators": self.significators,
        }


class KPSystem:
    """Complete KP (Krishnamurti Paddhati) system implementation."""

    # ================================================================
    # 1. KP AYANAMSA
    # ================================================================
    @staticmethod

    def get_kp_ayanamsa(year: int = 2026) -> float:
        """Return the module's approximate KP ayanamsa for a calendar year.

        The implementation is anchored to the module's explicit 2026 reference
        and applies a simplified precession rate for other years.
        """
        annual_rate = 0.0137  # approximate degrees/year
        return KP_AYANAMSA_2026 + (year - 2026) * annual_rate

    @staticmethod
    def convert_to_kp_sidereal(tropical_lon: float, year: int = 2026) -> float:
        """Convert tropical longitude to KP sidereal."""
        ayanamsa = KPSystem.get_kp_ayanamsa(year)
        return (tropical_lon - ayanamsa) % 360.0

    # ================================================================
    # 2. SUB-LORDS (249 divisions of Vimshottari within each star)
    # ================================================================
    @classmethod
    def get_sub_lord(cls, longitude: float) -> SubLord:
        """Calculate the KP sub-lord for a given sidereal longitude."""
        NAKSHATRA_SPAN = 360.0 / 27.0  # 13.3333... degrees per nakshatra

        nak_idx = int(longitude // NAKSHATRA_SPAN)
        nak_name = NAKSHATRAS[nak_idx]
        vimshottari_lord = DASHA_LORDS[nak_idx % 9]

        # Pada (4 padas per nakshatra)
        pada_span = NAKSHATRA_SPAN / 4.0
        pada = int((longitude % NAKSHATRA_SPAN) // pada_span)

                # Sub-lord calculation: the sub-lord sequence starts with the
        # Nakshatra's own Vimshottari lord, then advances cyclically through
        # the Vimshottari sequence. Each sub-period is proportional to its
        # lord's standard Vimshottari duration.
        total_years = sum(DASHA_YEARS)
        nak_start = nak_idx * NAKSHATRA_SPAN
        pos_in_nak = longitude - nak_start
        start_idx = nak_idx % 9

        cumulative = 0.0
        sub_lord = DASHA_LORDS[start_idx]
        sub_span = 0.0
        sub_start = nak_start

        for i in range(9):
            idx = (start_idx + i) % 9
            sub_duration = (DASHA_YEARS[idx] / total_years) * NAKSHATRA_SPAN
            if pos_in_nak < cumulative + sub_duration:
                sub_lord = DASHA_LORDS[idx]
                sub_span = sub_duration
                sub_start = nak_start + cumulative
                break
            cumulative += sub_duration

        return SubLord(
            nakshatra=nak_name, nakshatra_index=nak_idx, pada=pada + 1,
            vimshottari_lord=vimshottari_lord, sub_lord=sub_lord,
            sub_lord_span=sub_span, sub_lord_start=sub_start
        )

    # ================================================================
    # 3. CUSPAL SUB-LORDS
    # ================================================================
    @classmethod
    def calculate_cuspal_sub_lords(cls, cusp_longitudes: Dict[int, float]) -> Dict[int, SubLord]:
        """Calculate sub-lords for all 12 house cusps."""
        cuspal = {}
        for house_num, lon in cusp_longitudes.items():
            cuspal[house_num] = cls.get_sub_lord(lon % 360.0)
        return cuspal

    # ================================================================
    # 4. RULING PLANETS
    # ================================================================
    @classmethod
    def calculate_ruling_planets(cls, planet_longitudes: Dict[str, float],
                                  ascendant_lon: float,
                                  query_datetime: Optional[datetime] = None,
                                  day_of_week: int = 0) -> Dict[str, str]:
        """Calculate the 4 ruling planets at query time."""
        ruling = {}

                # 1. Day Lord (Vara lord)
        # `datetime.weekday()` uses Monday=0 ... Sunday=6.
        day_lords = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
        ruling["day_lord"] = day_lords[day_of_week % 7]

        # 2. Moon's star lord
        moon_lon = planet_longitudes.get("Moon", 0.0)
        moon_sub = cls.get_sub_lord(moon_lon)
        ruling["moon_star_lord"] = moon_sub.vimshottari_lord
        ruling["moon_sub_lord"] = moon_sub.sub_lord

        # 3. Moon's sign lord
        moon_sign_idx = int(moon_lon // 30)
        sign_lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
                      "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
        ruling["moon_sign_lord"] = sign_lords[moon_sign_idx]

        # 4. Ascendant star lord
        asc_sub = cls.get_sub_lord(ascendant_lon)
        ruling["ascendant_star_lord"] = asc_sub.vimshottari_lord
        ruling["ascendant_sub_lord"] = asc_sub.sub_lord

        return ruling

    # ================================================================
    # 5. KP SIGNIFICATORS
    # ================================================================
    @classmethod
    def calculate_significators(cls, planet_houses: Dict[str, int],
                                 cuspal_sub_lords: Dict[int, SubLord],
                                 planet_sub_lords: Dict[str, SubLord]) -> Dict[str, List[int]]:
        """Calculate KP significators (houses ruled by each planet via star/sub lordship)."""
        significators = {p: [] for p in planet_houses}

        # House signified by a planet = house where its star lord sits
        for planet, house in planet_houses.items():
            if planet in planet_sub_lords:
                star_lord = planet_sub_lords[planet].vimshottari_lord
                if star_lord in planet_houses:
                    sig_house = planet_houses[star_lord]
                    if sig_house not in significators[planet]:
                        significators[planet].append(sig_house)

                sub_lord = planet_sub_lords[planet].sub_lord
                if sub_lord in planet_houses:
                    sig_house = planet_houses[sub_lord]
                    if sig_house not in significators[planet]:
                        significators[planet].append(sig_house)

            # Planet also signifies the house it occupies
            if house not in significators[planet]:
                significators[planet].append(house)

        return significators

    # ================================================================
    # 6. MASTER METHOD
    # ================================================================
    @classmethod
    def calculate_all(cls, planet_longitudes: Dict[str, float],
                      planet_houses: Dict[str, int],
                      ascendant_lon: float = 0.0,
                      cusp_longitudes: Optional[Dict[int, float]] = None,
                      query_datetime: Optional[datetime] = None,
                      day_of_week: int = 0,
                      year: int = 2026) -> KPResult:
        """Calculate complete KP system analysis."""
        # Sub-lords for all planets
        planet_sub_lords = {}
        for p_name, p_lon in planet_longitudes.items():
            planet_sub_lords[p_name] = cls.get_sub_lord(p_lon % 360.0)

        # Cuspal sub-lords (if cusp longitudes provided)
        if cusp_longitudes is None:
            cusp_longitudes = {h: (ascendant_lon + (h - 1) * 30) % 360.0 for h in range(1, 13)}
        cuspal_sub_lords = cls.calculate_cuspal_sub_lords(cusp_longitudes)

        # Ruling planets
        ruling_planets = cls.calculate_ruling_planets(
            planet_longitudes, ascendant_lon, query_datetime, day_of_week
        )

        # Significators
        significators = cls.calculate_significators(
            planet_houses, cuspal_sub_lords, planet_sub_lords
        )

        return KPResult(
            planet_sub_lords=planet_sub_lords,
            cuspal_sub_lords=cuspal_sub_lords,
            ruling_planets=ruling_planets,
            kp_ayanamsa=cls.get_kp_ayanamsa(year),
            significators=significators,
        )


if __name__ == "__main__":
    kp = KPSystem()

    test_lons = {"Sun": 45.5, "Moon": 120.0, "Mars": 200.0, "Mercury": 65.0,
                 "Jupiter": 300.0, "Venus": 15.0, "Saturn": 250.0}
    test_houses = {"Sun": 5, "Moon": 1, "Mars": 9, "Mercury": 4,
                   "Jupiter": 11, "Venus": 6, "Saturn": 2}

    result = kp.calculate_all(test_lons, test_houses, ascendant_lon=100.0)

    print("=" * 60)
    print("KP SYSTEM — COMPLETE ANALYSIS")
    print("=" * 60)

    print(f"\nKP Ayanamsa (2026): {result.kp_ayanamsa:.2f}°")

    print("\nRULING PLANETS:")
    for k, v in result.ruling_planets.items():
        print(f"  {k}: {v}")

    print("\nPLANET SUB-LORDS:")
    for p, s in result.planet_sub_lords.items():
        print(f"  {p}: {s.nakshatra} (Pada {s.pada}) → Star Lord: {s.vimshottari_lord} → Sub Lord: {s.sub_lord}")

    print("\nCUSPAL SUB-LORDS:")
    for h, s in list(result.cuspal_sub_lords.items())[:4]:
        print(f"  House {h}: {s.nakshatra} → Sub Lord: {s.sub_lord}")

    print("\nSIGNIFICATORS:")
    for p, sigs in result.significators.items():
        print(f"  {p}: houses {sigs}")
