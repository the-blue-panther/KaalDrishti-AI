"""
Jaimini Chara Dasha (जैमिनी चर दशा) - Sign-based Progression
=============================================================

The most important Jaimini dasha system. Rashi-based, variable duration
calculated from the sign's position relative to its lord.

Rules (Jaimini Sutras, Chapter 1):
1. Chara dasha starts from the sign containing the Atmakaraka or Lagna
2. Duration of each sign = distance from the sign to its lord (in signs)
3. If lord is in the sign itself: 12 years
4. If lord is exalted: subtract 1 year (minimum 1)
5. If lord is debilitated: add 1 year
6. Direction: Forward for odd signs, Reverse for even signs (Savamya rule)
7. Total cycle = sum of all 12 sign durations

Reference: Jaimini Upadesha Sutras, Pada 1
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


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

SIGN_LORDS = {
    ZodiacSign.ARIES: "Mars", ZodiacSign.TAURUS: "Venus",
    ZodiacSign.GEMINI: "Mercury", ZodiacSign.CANCER: "Moon",
    ZodiacSign.LEO: "Sun", ZodiacSign.VIRGO: "Mercury",
    ZodiacSign.LIBRA: "Venus", ZodiacSign.SCORPIO: "Mars",
    ZodiacSign.SAGITTARIUS: "Jupiter", ZodiacSign.CAPRICORN: "Saturn",
    ZodiacSign.AQUARIUS: "Saturn", ZodiacSign.PISCES: "Jupiter",
}

EXALTATION = {
    "Sun": ZodiacSign.ARIES, "Moon": ZodiacSign.TAURUS,
    "Mars": ZodiacSign.CAPRICORN, "Mercury": ZodiacSign.VIRGO,
    "Jupiter": ZodiacSign.CANCER, "Venus": ZodiacSign.PISCES,
    "Saturn": ZodiacSign.LIBRA,
}

DEBILITATION = {
    "Sun": ZodiacSign.LIBRA, "Moon": ZodiacSign.SCORPIO,
    "Mars": ZodiacSign.CANCER, "Mercury": ZodiacSign.PISCES,
    "Jupiter": ZodiacSign.CAPRICORN, "Venus": ZodiacSign.VIRGO,
    "Saturn": ZodiacSign.ARIES,
}

# Odd signs = Movable/Fire/Air (forward direction)
ODD_SIGNS = {ZodiacSign.ARIES, ZodiacSign.GEMINI, ZodiacSign.LEO,
             ZodiacSign.LIBRA, ZodiacSign.SAGITTARIUS, ZodiacSign.AQUARIUS}


@dataclass
class CharaDashaPeriod:
    sign: str
    lord: str
    duration_years: float
    start_date: str
    end_date: str
    direction: str

    def to_dict(self) -> dict:
        return {
            "sign": self.sign, "lord": self.lord,
            "duration_years": self.duration_years,
            "start": self.start_date, "end": self.end_date,
            "direction": self.direction
        }


class JaiminiCharaDasha:

    @staticmethod
    def calculate_duration(sign: ZodiacSign, lord_planet: str,
                           planet_signs: Dict[str, int]) -> float:
        """Calculate sign duration based on distance to its lord."""
        sign_idx = ZODIAC_ORDER.index(sign)
        if lord_planet in planet_signs:
            lord_sign_idx = planet_signs[lord_planet]
        else:
            return 12.0

        diff = (lord_sign_idx - sign_idx) % 12
        duration = float(diff) if diff > 0 else 12.0

        lord_sign = ZODIAC_ORDER[lord_sign_idx]
        if EXALTATION.get(lord_planet) == lord_sign:
            duration = max(1.0, duration - 1)
        if DEBILITATION.get(lord_planet) == lord_sign:
            duration += 1

        return duration

    @classmethod
    def calculate_chara_dasha(cls, birth_datetime: datetime,
                              planet_signs: Dict[str, int],
                              start_sign: Optional[int] = None) -> List[CharaDashaPeriod]:
        """Calculate complete Chara Dasha timeline."""
        if start_sign is None:
            start_sign = 0  # Default: Aries (0)

        DAYS_IN_YEAR = 365.2425
        current_date = birth_datetime
        periods = []

        # Determine direction for each sign
        signs_direction = []
        for i in range(12):
            sign_idx = (start_sign + i) % 12
            sign = ZODIAC_ORDER[sign_idx]
            direction = "Forward" if sign in ODD_SIGNS else "Reverse"
            signs_direction.append((sign_idx, sign, direction))

        # Order: forward signs first, then reverse (following Savamya)
        ordered = sorted(signs_direction, key=lambda x: (0 if x[2] == "Forward" else 1, x[0]))

        for sign_idx, sign, direction in ordered:
            lord = SIGN_LORDS.get(sign, "Unknown")
            duration = cls.calculate_duration(sign, lord, planet_signs)
            end_date = current_date + timedelta(days=duration * DAYS_IN_YEAR)

            periods.append(CharaDashaPeriod(
                sign=sign.value, lord=lord, duration_years=duration,
                start_date=current_date.strftime("%d-%b, %Y"),
                end_date=end_date.strftime("%d-%b, %Y"),
                direction=direction
            ))
            current_date = end_date

        return periods

    @classmethod
    def get_current_period(cls, periods: List[CharaDashaPeriod],
                           target_date: datetime) -> Optional[CharaDashaPeriod]:
        """Find the active Chara Dasha period."""
        for p in periods:
            start = datetime.strptime(p.start_date, "%d-%b, %Y")
            end = datetime.strptime(p.end_date, "%d-%b, %Y")
            if start <= target_date <= end:
                return p
        return None


if __name__ == "__main__":
    test_signs = {"Sun": 4, "Moon": 3, "Mars": 9, "Mercury": 5,
                  "Jupiter": 11, "Venus": 6, "Saturn": 2}
    birth = datetime(1990, 12, 1, 10, 30)

    periods = JaiminiCharaDasha.calculate_chara_dasha(birth, test_signs)
    print("=" * 60)
    print("JAIMINI CHARA DASHA")
    print("=" * 60)
    for p in periods:
        print(f"  {p.sign} ({p.lord}): {p.duration_years:.1f}yr [{p.direction}] | {p.start_date} → {p.end_date}")

    current = JaiminiCharaDasha.get_current_period(periods, datetime(2026, 7, 19))
    if current:
        print(f"\n  Current: {current.sign} until {current.end_date}")
