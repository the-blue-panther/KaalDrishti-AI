"""
Kalachakra Dasha (कालचक्र दशा) - Wheel of Time
================================================

Complex nakshatra-based dasha system with 85+ year cycle.
Each nakshatra pada maps to a specific sign and dasha lord.

Reference: Brihat Parashara Hora Shastra, Chapters 48-54
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


# Classical Kalachakra tables: four nakshatra groups, each with four
# pada-specific 9-sign dasha sequences.
KALACHAKRA_GROUPS = {
    "Savya-I": {"Ashwini", "Krittika", "Punarvasu", "Ashlesha", "Hasta", "Swati", "Mula", "Uttara Ashadha", "Purva Bhadrapada", "Revati"},
    "Savya-II": {"Bharani", "Pushya", "Chitra", "Purva Ashadha", "Uttara Bhadrapada"},
    "Apasavya-I": {"Rohini", "Magha", "Vishakha", "Shravana"},
    "Apasavya-II": {"Mrigashira", "Ardra", "Purva Phalguni", "Uttara Phalguni", "Anuradha", "Jyeshtha", "Dhanishtha", "Shatabhisha"},
}

KALACHAKRA_SEQUENCES = {
    "Savya-I": [
        ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"],
        ["Capricorn", "Aquarius", "Pisces", "Scorpio", "Libra", "Virgo", "Cancer", "Leo", "Gemini"],
        ["Taurus", "Aries", "Pisces", "Aquarius", "Capricorn", "Sagittarius", "Aries", "Taurus", "Gemini"],
        ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
    ],
    "Savya-II": [
        ["Scorpio", "Libra", "Virgo", "Cancer", "Leo", "Gemini", "Taurus", "Aries", "Pisces"],
        ["Aquarius", "Capricorn", "Sagittarius", "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"],
        ["Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Scorpio", "Libra", "Virgo"],
        ["Cancer", "Leo", "Gemini", "Taurus", "Aries", "Pisces", "Aquarius", "Capricorn", "Sagittarius"],
    ],
    "Apasavya-I": [
        ["Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini", "Leo", "Cancer"],
        ["Virgo", "Libra", "Scorpio", "Pisces", "Aquarius", "Capricorn", "Sagittarius", "Scorpio", "Libra"],
        ["Virgo", "Leo", "Cancer", "Gemini", "Taurus", "Aries", "Sagittarius", "Capricorn", "Aquarius"],
        ["Pisces", "Aries", "Taurus", "Gemini", "Leo", "Cancer", "Virgo", "Libra", "Scorpio"],
    ],
    "Apasavya-II": [
        ["Pisces", "Aquarius", "Capricorn", "Sagittarius", "Scorpio", "Libra", "Virgo", "Leo", "Cancer"],
        ["Gemini", "Taurus", "Aries", "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus"],
        ["Gemini", "Leo", "Cancer", "Virgo", "Libra", "Scorpio", "Pisces", "Aquarius", "Capricorn"],
        ["Sagittarius", "Scorpio", "Libra", "Virgo", "Leo", "Cancer", "Gemini", "Taurus", "Aries"],
    ],
}

KALACHAKRA_PARAMAYUSH = {
    "Savya-I": [100, 85, 83, 86],
    "Savya-II": [100, 85, 83, 86],
    "Apasavya-I": [86, 83, 85, 100],
    "Apasavya-II": [86, 83, 85, 100],
}

KALACHAKRA_SIGN_YEARS = {
    "Aries": 7, "Taurus": 16, "Gemini": 9, "Cancer": 21,
    "Leo": 5, "Virgo": 9, "Libra": 16, "Scorpio": 7,
    "Sagittarius": 10, "Capricorn": 4, "Aquarius": 4, "Pisces": 10,
}

KALACHAKRA_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}


@dataclass
class KalachakraPeriod:
    nakshatra_index: int
    pada: int
    sign: str
    lord: str
    duration_years: int
    start_date: str
    end_date: str

    def to_dict(self) -> dict:
        return {"nakshatra": self.nakshatra_index, "pada": self.pada,
                "sign": self.sign, "lord": self.lord,
                "duration_years": self.duration_years,
                "start": self.start_date, "end": self.end_date}


class KalachakraDasha:

    @classmethod
    def calculate(cls, moon_lon: float, birth: datetime) -> List[KalachakraPeriod]:
        NAK_SPAN = 360.0 / 27.0
        if not 0 <= moon_lon < 360:
            moon_lon %= 360

                # Use exact rational scaling (27 nakshatras / 108 padas)
        # instead of repeated division by the approximate floating span.
        pada_position = (moon_lon * 108.0) / 360.0
        nearest_integer = round(pada_position)
        if abs(pada_position - nearest_integer) < 1e-10:
            pada_position = float(nearest_integer)

        if pada_position >= 108.0:
            pada_position = 0.0
            moon_lon = 0.0

        nak_idx = int(pada_position // 4.0)
        pada = int(pada_position % 4.0)

        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
            "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
            "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
            "Uttara Bhadrapada", "Revati",
        ]
        nakshatra = nakshatras[nak_idx]
        group = next(name for name, members in KALACHAKRA_GROUPS.items()
                     if nakshatra in members)

        sequence = KALACHAKRA_SEQUENCES[group][pada]
        paramayush = KALACHAKRA_PARAMAYUSH[group][pada]
        pada_position = (moon_lon * 108.0) / 360.0
        nearest_integer = round(pada_position)
        if abs(pada_position - nearest_integer) < 1e-10:
            pada_position = float(nearest_integer)
        elapsed_fraction = pada_position - int(pada_position)
        # Guard the exact end of a pada against floating-point spillover.
        elapsed_fraction = min(1.0 - 1e-12, max(0.0, elapsed_fraction))
        elapsed_years = elapsed_fraction * paramayush

        DAYS = 365.2425
        periods = []
        cumulative = 0.0

        for idx, sign in enumerate(sequence):
            duration = KALACHAKRA_SIGN_YEARS[sign]
            next_cumulative = cumulative + duration

            if elapsed_years >= next_cumulative:
                cumulative = next_cumulative
                continue

            remaining_first = next_cumulative - elapsed_years
            current = birth
            end = current + timedelta(days=remaining_first * DAYS)
            periods.append(KalachakraPeriod(
                nak_idx, pada, sign, KALACHAKRA_LORDS[sign], duration,
                current.strftime("%d-%b, %Y"), end.strftime("%d-%b, %Y")
            ))
            current = end

            for following_sign in sequence[idx + 1:]:
                duration = KALACHAKRA_SIGN_YEARS[following_sign]
                end = current + timedelta(days=duration * DAYS)
                periods.append(KalachakraPeriod(
                    -1, -1, following_sign, KALACHAKRA_LORDS[following_sign], duration,
                    current.strftime("%d-%b, %Y"), end.strftime("%d-%b, %Y")
                ))
                current = end

            return periods

        return []

    @classmethod
    def get_current(cls, periods: List[KalachakraPeriod],
                    target: datetime) -> Optional[KalachakraPeriod]:
        for p in periods:
            s = datetime.strptime(p.start_date, "%d-%b, %Y")
            e = datetime.strptime(p.end_date, "%d-%b, %Y")
            if s <= target < e:

                return p
        return None


if __name__ == "__main__":
    periods = KalachakraDasha.calculate(120.0, datetime(1990, 12, 1, 10, 30))
    print("KALACHAKRA DASHA")
    print("=" * 50)
    for p in periods[:10]:
        print(f"  {p.sign} ({p.lord}): {p.duration_years}yr | {p.start_date} → {p.end_date}")
