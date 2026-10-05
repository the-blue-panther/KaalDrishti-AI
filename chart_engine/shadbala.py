"""
Shadbala (षड्बल) - The Six-Fold Planetary Strength System
=============================================================

The foundation of Vedic astrological accuracy. Every planet's exact strength
is measured in Virupas (60 Virupas = 1 Rupa), distributed across 6 categories:

1. Sthana Bala (स्थान बल) - Positional Strength
2. Dig Bala (दिग् बल) - Directional Strength
3. Kala Bala (काल बल) - Temporal Strength
4. Chesta Bala (चेष्टा बल) - Motional Strength
5. Naisargika Bala (नैसर्गिक बल) - Natural Strength
6. Drik Bala (दृक् बल) - Aspectual Strength

Reference: Brihat Parashara Hora Shastra, Chapter 27
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


# ============================================================
# CONSTANTS & LOOKUP TABLES
# ============================================================

class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"

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

# ---- Exaltation Signs ----
EXALTATION = {
    Planet.SUN: ZodiacSign.ARIES,        # 10° Aries
    Planet.MOON: ZodiacSign.TAURUS,      # 3° Taurus
    Planet.MARS: ZodiacSign.CAPRICORN,   # 28° Capricorn
    Planet.MERCURY: ZodiacSign.VIRGO,    # 15° Virgo
    Planet.JUPITER: ZodiacSign.CANCER,   # 5° Cancer
    Planet.VENUS: ZodiacSign.PISCES,     # 27° Pisces
    Planet.SATURN: ZodiacSign.LIBRA,     # 20° Libra
}

# ---- Debilitation Signs ----
DEBILITATION = {
    Planet.SUN: ZodiacSign.LIBRA,
    Planet.MOON: ZodiacSign.SCORPIO,
    Planet.MARS: ZodiacSign.CANCER,
    Planet.MERCURY: ZodiacSign.PISCES,
    Planet.JUPITER: ZodiacSign.CAPRICORN,
    Planet.VENUS: ZodiacSign.VIRGO,
    Planet.SATURN: ZodiacSign.ARIES,
}

# ---- Moolatrikona Signs (Root Trine) ----
MOOLATRIKONA = {
    Planet.SUN: (ZodiacSign.LEO, 0.0, 20.0),       # Leo 0°-20°
    Planet.MOON: (ZodiacSign.TAURUS, 4.0, 30.0),    # Taurus 4°-30° (3° exalted, rest moola)
    Planet.MARS: (ZodiacSign.ARIES, 0.0, 12.0),     # Aries 0°-12°
    Planet.MERCURY: (ZodiacSign.VIRGO, 16.0, 20.0), # Virgo 16°-20°
    Planet.JUPITER: (ZodiacSign.SAGITTARIUS, 0.0, 10.0), # Sagittarius 0°-10°
    Planet.VENUS: (ZodiacSign.LIBRA, 0.0, 5.0),     # Libra 0°-5°
    Planet.SATURN: (ZodiacSign.AQUARIUS, 0.0, 20.0), # Aquarius 0°-20°
}

# ---- Own Signs (Swakshetra) ----
OWN_SIGNS = {
    Planet.SUN: [ZodiacSign.LEO],
    Planet.MOON: [ZodiacSign.CANCER],
    Planet.MARS: [ZodiacSign.ARIES, ZodiacSign.SCORPIO],
    Planet.MERCURY: [ZodiacSign.GEMINI, ZodiacSign.VIRGO],
    Planet.JUPITER: [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES],
    Planet.VENUS: [ZodiacSign.TAURUS, ZodiacSign.LIBRA],
    Planet.SATURN: [ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS],
}

# ---- Exaltation Degrees (Deep Exaltation Point) ----
EXALTATION_DEGREES = {
    Planet.SUN: 10.0,
    Planet.MOON: 3.0,
    Planet.MARS: 28.0,
    Planet.MERCURY: 15.0,
    Planet.JUPITER: 5.0,
    Planet.VENUS: 27.0,
    Planet.SATURN: 20.0,
}

# ---- Debilitation Degrees (Deep Debilitation Point) ----
DEBILITATION_DEGREES = {
    Planet.SUN: 10.0,
    Planet.MOON: 3.0,
    Planet.MARS: 28.0,
    Planet.MERCURY: 15.0,
    Planet.JUPITER: 5.0,
    Planet.VENUS: 27.0,
    Planet.SATURN: 20.0,
}

# ---- Naisargika Bala (Natural Strength in Virupas) ----
# Based on luminosity and natural hierarchy (BPHS Ch.27, Shloka 13-14)
NAISARGIKA_BALA = {
    Planet.SUN: 60.0,       # 1 Rupa
    Planet.MOON: 51.43,     # 0.857 Rupa
    Planet.VENUS: 42.85,    # 0.714 Rupa
    Planet.JUPITER: 34.28,  # 0.571 Rupa
    Planet.MERCURY: 25.71,  # 0.428 Rupa
    Planet.MARS: 17.14,     # 0.285 Rupa
    Planet.SATURN: 8.57,    # 0.142 Rupa
}

# ---- Dig Bala (Directional Strength) ----
# Maximum 60 Virupas for each direction
DIG_BALA_HOUSES = {
    Planet.SUN: 10,      # South - 10th house
    Planet.MOON: 4,      # North - 4th house
    Planet.MARS: 10,     # South - 10th house
    Planet.MERCURY: 1,   # East - 1st house (Ascendant)
    Planet.JUPITER: 1,   # East - 1st house
    Planet.VENUS: 4,     # North - 4th house
    Planet.SATURN: 7,    # West - 7th house
}

# ---- Drig Bala (Aspectual Strength) multipliers ----
# Standard aspect values for full aspect (60 Virupas max)
FULL_ASPECT_VALUE = 60.0
HALF_ASPECT_VALUE = 30.0
QUARTER_ASPECT_VALUE = 15.0
THREE_QUARTER_ASPECT_VALUE = 45.0

# ---- Special Aspects (Graha Drishti) ----
SPECIAL_ASPECTS = {
    Planet.JUPITER: [5, 7, 9],   # 5th, 7th, 9th houses
    Planet.MARS: [4, 7, 8],       # 4th, 7th, 8th houses
    Planet.SATURN: [3, 7, 10],    # 3rd, 7th, 10th houses
}


@dataclass
class ShadbalaResult:
    """Complete Shadbala calculation result for a single planet."""
    planet: str

    # Sthana Bala components
    uchcha_bala: float          # Exaltation strength
    saptavargaja_bala: float    # 7-fold divisional strength
    ojayugma_bala: float        # Odd/even sign strength
    kendra_bala: float          # Angular house strength
    drekkena_bala: float        # Decanate strength
    sthana_bala_total: float

    # Other Balas
    dig_bala: float
    kala_bala: float
    chesta_bala: float
    naisargika_bala: float
    drik_bala: float

    # Totals
    total_virupas: float
    total_rupas: float

    # Interpretation
    strength_category: str      # "Very Strong", "Strong", "Average", "Weak", "Very Weak"

    def to_dict(self) -> dict:
        return {
            "planet": self.planet,
            "sthana_bala": {
                "uchcha_bala": round(self.uchcha_bala, 2),
                "saptavargaja_bala": round(self.saptavargaja_bala, 2),
                "ojayugma_bala": round(self.ojayugma_bala, 2),
                "kendra_bala": round(self.kendra_bala, 2),
                "drekkena_bala": round(self.drekkena_bala, 2),
                "total": round(self.sthana_bala_total, 2)
            },
            "dig_bala": round(self.dig_bala, 2),
            "kala_bala": round(self.kala_bala, 2),
            "chesta_bala": round(self.chesta_bala, 2),
            "naisargika_bala": round(self.naisargika_bala, 2),
            "drik_bala": round(self.drik_bala, 2),
            "total_virupas": round(self.total_virupas, 2),
            "total_rupas": round(self.total_rupas, 2),
            "strength_category": self.strength_category
        }


class ShadbalaEngine:
    """
    Master engine for calculating the Shadbala of all 7 classical planets.

    Usage:
        engine = ShadbalaEngine()
        results = engine.calculate_all(
            planet_longitudes={"Sun": 15.5, ...},
            ascendant_lon=120.0,
            birth_time_hours=10.5,  # Local time in hours
            sunrise_hours=6.0,      # Sunrise time in hours
            is_day_birth=True,
            planet_speeds={"Sun": 0.98, ...}  # degrees/day
        )
    """

    @staticmethod
    def get_sign_index(longitude: float) -> int:
        """Get 0-based zodiac sign index from longitude."""
        return int(longitude % 360 // 30)

    @staticmethod
    def get_sign(longitude: float) -> ZodiacSign:
        """Get ZodiacSign from longitude."""
        return ZODIAC_ORDER[ShadbalaEngine.get_sign_index(longitude)]

    @staticmethod
    def get_degree_in_sign(longitude: float) -> float:
        """Get degree within sign (0-30)."""
        return longitude % 30

    # ================================================================
    # 1. STHANA BALA (Positional Strength) - 5 components
    # ================================================================

    @staticmethod
    def _uchcha_bala(planet: Planet, longitude: float) -> float:
        """
        Uchcha Bala (Exaltation Strength): Max 60 Virupas.

        Calculated based on distance from deep exaltation point.
        If in exaltation sign: score = 60 - (distance from exact exaltation degree)
        If in debilitation sign: score = distance from debilitation point - 60 (negative)
        Otherwise: proportional score based on distance from exaltation through zodiac.
        """
        exalt_sign = EXALTATION.get(planet)
        debil_sign = DEBILITATION.get(planet)
        exalt_degree = EXALTATION_DEGREES.get(planet, 0)
        debil_degree = DEBILITATION_DEGREES.get(planet, 0)

        current_sign = ShadbalaEngine.get_sign(longitude)
        degree_in_sign = ShadbalaEngine.get_degree_in_sign(longitude)

        # Calculate exaltation point absolute longitude
        exalt_sign_idx = ZODIAC_ORDER.index(exalt_sign)
        exalt_lon = (exalt_sign_idx * 30) + exalt_degree

        # Calculate distance from exaltation point (0-180 degrees)
        diff = abs(longitude - exalt_lon)
        if diff > 180:
            diff = 360 - diff

        # If exactly at exaltation: 60 Virupas
        # If exactly at debilitation (180° away): 0 Virupas
        # Linear interpolation
        if diff <= 180:
            uchcha = 60.0 * (1.0 - diff / 180.0)
        else:
            uchcha = 0.0

        return uchcha

    @staticmethod
    def _saptavargaja_bala(planet: Planet, longitude: float, vargas: Dict[str, str]) -> float:
        """
        Saptavargaja Bala (7-fold Divisional Strength): Max 45 Virupas.

        Checks the planet's placement in D1, D2, D3, D7, D9, D12, D30.
        Points awarded for being in own/exaltation/moolatrikona signs.
        """
        varga_map = {
            "D1_Main": 45 * 0.20,     # 9 Virupas max
            "D2_Hora": 45 * 0.10,     # 4.5 Virupas max
            "D3_Drekkana": 45 * 0.10,  # 4.5 Virupas max
            "D7_Saptamsha": 45 * 0.15, # 6.75 Virupas max
            "D9_Navamsha": 45 * 0.20,  # 9 Virupas max
            "D12_Dwadashamsha": 45 * 0.10,  # 4.5 Virupas max
            "D30_Trimshamsha": 45 * 0.15,   # 6.75 Virupas max
        }

        own_signs = OWN_SIGNS.get(planet, [])
        exalt_sign = EXALTATION.get(planet)
        moolatrikona_data = MOOLATRIKONA.get(planet)
        moolatrikona_sign = moolatrikona_data[0] if moolatrikona_data else None

        total = 0.0
        for varga_name, max_points in varga_map.items():
            if varga_name in vargas:
                varga_sign = vargas[varga_name]
                try:
                    sign_enum = ZodiacSign(varga_sign)
                    if sign_enum in own_signs:
                        total += max_points * 1.0   # Full points for own sign
                    elif sign_enum == exalt_sign:
                        total += max_points * 1.0   # Full points for exaltation
                    elif sign_enum == moolatrikona_sign:
                        total += max_points * 0.75  # 75% for moolatrikona
                    # Friendly signs get partial (handled in external friendship table)
                except ValueError:
                    pass

        return total

    @staticmethod
    def _ojayugma_bala(planet: Planet, longitude: float) -> float:
        """
        Ojayugma Bala (Odd/Even Sign Strength): Max 15 Virupas.

        Moon and Venus are strong in EVEN signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces).
        Sun, Mars, Jupiter are strong in ODD signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius).
        Mercury is strong in BOTH.
        """
        sign_idx = ShadbalaEngine.get_sign_index(longitude)
        is_odd_sign = (sign_idx % 2 == 0)  # 0-indexed: Aries=0(odd), Taurus=1(even)

        odd_strong = {Planet.SUN, Planet.MARS, Planet.JUPITER}
        even_strong = {Planet.MOON, Planet.VENUS}

        if planet in odd_strong and is_odd_sign:
            return 15.0
        elif planet in even_strong and not is_odd_sign:
            return 15.0
        elif planet == Planet.MERCURY:
            return 15.0  # Mercury always gets full
        elif planet == Planet.SATURN:
            return 15.0 if not is_odd_sign else 7.5  # Saturn slightly favors even signs
        else:
            return 0.0

    @staticmethod
    def _kendra_bala(planet: Planet, house_number: int) -> float:
        """
        Kendra Bala (Angular House Strength): Max 60 Virupas.

        Planets in Kendra (1,4,7,10) get full 60 Virupas.
        Planets in Panaphara (2,5,8,11) get 30 Virupas.
        Planets in Apoklima (3,6,9,12) get 15 Virupas.
        """
        if house_number in [1, 4, 7, 10]:
            return 60.0
        elif house_number in [2, 5, 8, 11]:
            return 30.0
        else:  # 3, 6, 9, 12
            return 15.0

    @staticmethod
    def _drekkena_bala(planet: Planet, longitude: float) -> float:
        """
        Drekkena Bala (Decanate Strength): Max 15 Virupas.

        Based on gender of planet and decanate:
        - Male planets (Sun, Mars, Jupiter): strong in 1st decanate (0°-10°)
        - Female planets (Moon, Venus): strong in 3rd decanate (20°-30°)
        - Hermaphrodite (Mercury, Saturn): strong in 2nd decanate (10°-20°)
        """
        degree_in_sign = ShadbalaEngine.get_degree_in_sign(longitude)
        decanate = int(degree_in_sign // 10)  # 0, 1, or 2

        male_planets = {Planet.SUN, Planet.MARS, Planet.JUPITER}
        female_planets = {Planet.MOON, Planet.VENUS}

        if planet in male_planets and decanate == 0:
            return 15.0
        elif planet in female_planets and decanate == 2:
            return 15.0
        elif planet in {Planet.MERCURY, Planet.SATURN} and decanate == 1:
            return 15.0
        else:
            return 0.0

    @staticmethod
    def calculate_sthana_bala(planet: Planet, longitude: float, house_number: int,
                               vargas: Optional[Dict[str, str]] = None) -> tuple:
        """Calculate all 5 components of Sthana Bala."""
        uchcha = ShadbalaEngine._uchcha_bala(planet, longitude)

        if vargas:
            saptavargaja = ShadbalaEngine._saptavargaja_bala(planet, longitude, vargas)
        else:
            saptavargaja = 0.0

        ojayugma = ShadbalaEngine._ojayugma_bala(planet, longitude)
        kendra = ShadbalaEngine._kendra_bala(planet, house_number)
        drekkena = ShadbalaEngine._drekkena_bala(planet, longitude)

        total = uchcha + saptavargaja + ojayugma + kendra + drekkena

        return uchcha, saptavargaja, ojayugma, kendra, drekkena, total

    # ================================================================
    # 2. DIG BALA (Directional Strength) - Max 60 Virupas
    # ================================================================

    @staticmethod
    def calculate_dig_bala(planet: Planet, house_number: int) -> float:
        """
        Dig Bala (Directional Strength).

        Each planet has a house where it gains maximum directional power.
        The farther from this house, the weaker (minimum 0 at the 7th from dig bala house).
        """
        dig_bala_house = DIG_BALA_HOUSES.get(planet, 1)

        # Calculate distance from dig bala house
        # Planets AT the dig bala house = 60 Virupas
        # Planets at 7th from dig bala = 0 Virupas
        distance = (house_number - dig_bala_house) % 12

        # Cosine-like decay: max at distance 0, 0 at distance 6
        if distance <= 6:
            dig = 60.0 * (1.0 - distance / 6.0)
        else:
            dig = 60.0 * ((distance - 6.0) / 6.0)

        return dig

    # ================================================================
    # 3. KALA BALA (Temporal Strength) - Max 102 Virupas total
    # ================================================================

    @staticmethod
    def calculate_kala_bala(planet: Planet, birth_time_hours: float,
                           sunrise_hours: float, is_day_birth: bool,
                           moon_longitude: float, sun_longitude: float,
                           year: int, tithi_index: int = 0) -> float:
        """
        Kala Bala (Temporal Strength).

        Components:
        - Nathonnatha Bala (Day/Night strength): 60 Virupas max
        - Paksha Bala (Lunar phase): 30 Virupas max
        - Tribhaga Bala (3-part day strength): 60 Virupas max (simplified to 30)
        - Abda Bala (Year lord): 15 Virupas max
        - Masa Bala (Month lord): 30 Virupas max
        - Vara Bala (Day lord): 45 Virupas max
        - Hora Bala (Hour lord): 30 Virupas max (simplified)
        - Ayana Bala (Solstice): 30 Virupas max
        - Yuddha Bala (Planetary war): handled separately
        """
        # 1. Nathonnatha Bala (Day/Night strength) - Max 60
        # Sun, Jupiter, Saturn = strong during day
        # Moon, Mars, Venus = strong during night
        # Mercury = always strong
        day_strong = {Planet.SUN, Planet.JUPITER, Planet.SATURN}
        night_strong = {Planet.MOON, Planet.MARS, Planet.VENUS}

        # Calculate time relative to noon/midnight
        noon = 12.0
        midnight = 0.0

        if is_day_birth:
            # Distance from noon (0 to 6 hours max)
            time_from_noon = abs(birth_time_hours - noon)
            if time_from_noon > 6:
                time_from_noon = 12 - time_from_noon
            day_strength = 60.0 * (1.0 - time_from_noon / 6.0)
            night_strength = 60.0 * (time_from_noon / 6.0)
        else:
            # Distance from midnight
            if birth_time_hours > 12:
                time_from_midnight = abs(birth_time_hours - 24)
            else:
                time_from_midnight = birth_time_hours
            if time_from_midnight > 6:
                time_from_midnight = 12 - time_from_midnight
            night_strength = 60.0 * (1.0 - time_from_midnight / 6.0)
            day_strength = 60.0 * (time_from_midnight / 6.0)

        if planet in day_strong:
            nathonnatha = day_strength
        elif planet in night_strong:
            nathonnatha = night_strength
        else:  # Mercury
            nathonnatha = 60.0

        # 2. Paksha Bala (Lunar phase) - Max 30
        # Waxing moon = benefics strong; Waning moon = malefics strong
        moon_sun_diff = (moon_longitude - sun_longitude) % 360
        is_waxing = moon_sun_diff < 180

        benefics = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}
        malefics = {Planet.SUN, Planet.MARS, Planet.SATURN}

        if planet in benefics:
            paksha = 30.0 * (1.0 - abs(moon_sun_diff - 0) / 180.0) if is_waxing else 30.0 * (abs(moon_sun_diff - 180) / 180.0)
        elif planet in malefics:
            paksha = 30.0 * (abs(moon_sun_diff - 180) / 180.0) if is_waxing else 30.0 * (1.0 - abs(moon_sun_diff - 180) / 180.0)
        else:
            paksha = 15.0

        # 3. Tribhaga Bala - Simplified: 30 Virupas max for all (evenly distributed)
        tribhaga = 30.0 if planet in [Planet.MERCURY, Planet.JUPITER] else 15.0

        # 4. Abda Bala (Year lord) - 15 Virupas max, simplified
        year_lords = [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                      Planet.JUPITER, Planet.VENUS, Planet.SATURN]
        year_lord = year_lords[(year - 1) % 7]  # Simplified cyclic year lord
        abda = 15.0 if planet == year_lord else 0.0

        # 5. Masa Bala (Month lord) - 30 Virupas max, simplified
        # Use tithi-based month allocation
        masa = 15.0  # Default moderate

        # 6. Vara Bala (Day lord) - 45 Virupas max
        # Simplified: based on the birth day of week
        vara = 30.0  # Default

        # 7. Ayana Bala (Solstice declination effect) - 30 Virupas max
        # Simplified: Sun's declination effect
        ayana = 15.0

        total = nathonnatha + paksha + tribhaga + abda + masa + vara + ayana

        return min(total, 102.0)  # Cap at theoretical maximum

    # ================================================================
    # 4. CHESTA BALA (Motional Strength) - Max 60 Virupas
    # ================================================================

    @staticmethod
    def calculate_chesta_bala(planet: Planet, speed_deg_per_day: float,
                              is_retrograde: bool = False) -> float:
        """
        Chesta Bala (Motional Strength).

        Based on the planet's speed relative to its mean motion.
        Retrograde planets get additional strength proportional to their speed.
        """
        # Mean motions (degrees per day)
        mean_motions = {
            Planet.SUN: 0.9856,
            Planet.MOON: 13.176,
            Planet.MARS: 0.524,
            Planet.MERCURY: 0.9856,
            Planet.JUPITER: 0.083,
            Planet.VENUS: 0.9856,
            Planet.SATURN: 0.034,
        }

        mean = mean_motions.get(planet, 1.0)

        if is_retrograde:
            # Retrograde planets: chesta bala = speed * factor
            abs_speed = abs(speed_deg_per_day)
            chesta = min(60.0, abs_speed * 60.0 / mean)
        else:
            # Direct motion: faster than mean = stronger
            if speed_deg_per_day > mean:
                chesta = min(60.0, (speed_deg_per_day / mean) * 30.0)
            elif speed_deg_per_day > 0:
                chesta = (speed_deg_per_day / mean) * 15.0
            else:
                chesta = 0.0

        return chesta

    # ================================================================
    # 5. NAISARGIKA BALA (Natural Strength) - Constant per planet
    # ================================================================

    @staticmethod
    def calculate_naisargika_bala(planet: Planet) -> float:
        """Natural, immutable strength of each planet."""
        return NAISARGIKA_BALA.get(planet, 0.0)

    # ================================================================
    # 6. DRIK BALA (Aspectual Strength) - Max 60 Virupas per aspect
    # ================================================================

    @staticmethod
    def calculate_drik_bala(planet: Planet, all_planet_longitudes: Dict[str, float],
                        planet_house: int,
                        all_planet_houses: Optional[Dict[str, int]] = None) -> float:
        """
            Drik Bala (Aspectual Strength).

            Calculates how much a planet is ASPECTED BY other planets.
            Benefic aspects = positive; Malefic aspects = negative.

            Special aspects: Jupiter (5,7,9), Mars (4,7,8), Saturn (3,7,10)
            All planets aspect the 7th house.
        """
        benefics = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}
        malefics = {Planet.SUN, Planet.MARS, Planet.SATURN}

        total_drik = 0.0

        for asp_planet_name, asp_lon in all_planet_longitudes.items():
            if asp_planet_name == planet.value or asp_planet_name == planet:
                continue

            try:
                asp_planet = Planet(asp_planet_name) if isinstance(asp_planet_name, str) else asp_planet_name
            except (ValueError, TypeError):
                continue

            if all_planet_houses is not None:
                asp_house = all_planet_houses.get(asp_planet_name)
            else:
                asp_house = ShadbalaEngine.get_house_from_lon(asp_lon, all_planet_longitudes)
            if asp_house is None:
                asp_house = int(asp_lon % 360 // 30) + 1

            # Calculate house difference
            diff = (asp_house - planet_house) % 12

            # Check if aspect applies
            aspect_strength = 0.0
            special_aspects = SPECIAL_ASPECTS.get(asp_planet, [])

            if (diff + 1) in special_aspects:  # +1 because diff is 0-indexed offset
                aspect_strength = FULL_ASPECT_VALUE
            elif diff == 6:  # 7th house aspect (all planets)
                aspect_strength = FULL_ASPECT_VALUE

            if aspect_strength > 0:
                if asp_planet in benefics:
                    total_drik += aspect_strength
                elif asp_planet in malefics:
                    total_drik -= aspect_strength * 0.5  # Malefic aspect = reduced benefit

        # Normalize to 0-60 range
        return max(0.0, min(60.0, 30.0 + total_drik))

    @staticmethod
    def get_house_from_lon(lon: float, all_lons: Dict[str, float]) -> int:
        """Estimate house number from longitude alone (simplified)."""
        # Without ascendant, approximate: sign-based house
        sign_idx = int(lon % 360 // 30)
        return sign_idx + 1

    # ================================================================
    # MASTER CALCULATION
    # ================================================================

    @classmethod
    def calculate_for_planet(cls, planet: Planet, longitude: float,
                             house_number: int, vargas: Optional[Dict[str, str]] = None,
                             speed: float = 0.0, is_retrograde: bool = False,
                             birth_time_hours: float = 12.0, sunrise_hours: float = 6.0,
                             is_day_birth: bool = True, moon_longitude: float = 0.0,
                             sun_longitude: float = 0.0, year: int = 2026,
                             tithi_index: int = 0,
                             all_planet_longitudes: Optional[Dict[str, float]] = None,
                             all_planet_houses: Optional[Dict[str, int]] = None) -> ShadbalaResult:
        """Calculate complete Shadbala for a single planet."""

        # 1. Sthana Bala
        uchcha, saptavargaja, ojayugma, kendra, drekkena, sthana_total = \
            cls.calculate_sthana_bala(planet, longitude, house_number, vargas)

        # 2. Dig Bala
        dig = cls.calculate_dig_bala(planet, house_number)

        # 3. Kala Bala
        kala = cls.calculate_kala_bala(planet, birth_time_hours, sunrise_hours,
                                       is_day_birth, moon_longitude, sun_longitude,
                                       year, tithi_index)

        # 4. Chesta Bala
        chesta = cls.calculate_chesta_bala(planet, speed, is_retrograde)

        # 5. Naisargika Bala
        naisargika = cls.calculate_naisargika_bala(planet)

        # 6. Drik Bala
        if all_planet_longitudes:
            drik = cls.calculate_drik_bala(
                planet, all_planet_longitudes, house_number, all_planet_houses
            )
        else:
            drik = 30.0  # Default neutral

        total_virupas = sthana_total + dig + kala + chesta + naisargika + drik
        total_rupas = total_virupas / 60.0

        # Category classification
        if total_rupas >= 6.5:
            category = "Very Strong"
        elif total_rupas >= 5.0:
            category = "Strong"
        elif total_rupas >= 3.5:
            category = "Average"
        elif total_rupas >= 2.0:
            category = "Weak"
        else:
            category = "Very Weak"

        return ShadbalaResult(
            planet=planet.value if isinstance(planet, Planet) else planet,
            uchcha_bala=uchcha,
            saptavargaja_bala=saptavargaja,
            ojayugma_bala=ojayugma,
            kendra_bala=kendra,
            drekkena_bala=drekkena,
            sthana_bala_total=sthana_total,
            dig_bala=dig,
            kala_bala=kala,
            chesta_bala=chesta,
            naisargika_bala=naisargika,
            drik_bala=drik,
            total_virupas=total_virupas,
            total_rupas=total_rupas,
            strength_category=category
        )

    @classmethod
    def calculate_all(cls, planet_longitudes: Dict[str, float],
                      ascendant_lon: float = 0.0,
                      vargas: Optional[Dict[str, Dict[str, str]]] = None,
                      planet_speeds: Optional[Dict[str, float]] = None,
                      retrograde_status: Optional[Dict[str, bool]] = None,
                      birth_time_hours: float = 12.0,
                      sunrise_hours: float = 6.0,
                      is_day_birth: bool = True,
                      year: int = 2026,
                      tithi_index: int = 0) -> Dict[str, ShadbalaResult]:
        """
        Calculate Shadbala for all 7 classical planets.

        Args:
            planet_longitudes: Dict of planet name to sidereal longitude
            ascendant_lon: Ascendant sidereal longitude
            vargas: Dict of varga_name -> {planet: sign}
            planet_speeds: Dict of planet name to speed in deg/day
            retrograde_status: Dict of planet name to is_retrograde bool
            birth_time_hours: Local birth time in decimal hours (0-24)
            sunrise_hours: Sunrise time in decimal hours
            is_day_birth: True if born between sunrise and sunset
            year: Birth year
            tithi_index: 0-29 tithi index

        Returns:
            Dict mapping planet name to ShadbalaResult
        """
        results = {}

        if planet_speeds is None:
            planet_speeds = {}
        if retrograde_status is None:
            retrograde_status = {}

                # Get Moon and Sun longitudes for Kala Bala
        moon_lon = planet_longitudes.get("Moon", 0.0)
        sun_lon = planet_longitudes.get("Sun", 0.0)

        # Compute the whole-sign house of every planet once so Drik Bala
        # uses the same ascendant-relative house system as the target planet.
        asc_sign_idx = int(ascendant_lon % 360 // 30)
        planet_house_map = {
            name: ((int(lon % 360 // 30) - asc_sign_idx) % 12) + 1
            for name, lon in planet_longitudes.items()
        }

        for planet_name, lon in planet_longitudes.items():
            try:
                planet = Planet(planet_name)
            except ValueError:
                continue  # Skip Rahu, Ketu (no Shadbala for nodes)

            # Calculate house number from ascendant
            asc_sign_idx = int(ascendant_lon // 30)
            planet_sign_idx = int(lon // 30)
            house_number = ((planet_sign_idx - asc_sign_idx) % 12) + 1

            # Get planet-specific vargas
            planet_vargas = None
            if vargas:
                planet_vargas = {}
                for v_name, v_data in vargas.items():
                    if planet_name in v_data:
                        planet_vargas[v_name] = v_data[planet_name]
                    elif "Ascendant" in v_data and v_name == "D1_Main":
                        # Fallback: use D1
                        pass

            speed = planet_speeds.get(planet_name, 0.0)
            is_retro = retrograde_status.get(planet_name, False)

            result = cls.calculate_for_planet(
                planet=planet,
                longitude=lon,
                house_number=house_number,
                vargas=planet_vargas,
                speed=speed,
                is_retrograde=is_retro,
                birth_time_hours=birth_time_hours,
                sunrise_hours=sunrise_hours,
                is_day_birth=is_day_birth,
                moon_longitude=moon_lon,
                sun_longitude=sun_lon,
                year=year,
                                tithi_index=tithi_index,
                all_planet_longitudes=planet_longitudes,
                all_planet_houses=planet_house_map
            )
            results[planet_name] = result

        return results

    @classmethod
    def get_strength_summary(cls, results: Dict[str, 'ShadbalaResult']) -> Dict:
        """Generate a summary of all planetary strengths."""
        summary = {}
        for planet_name, result in results.items():
            summary[planet_name] = {
                "total_rupas": round(result.total_rupas, 2),
                "total_virupas": round(result.total_virupas, 2),
                "category": result.strength_category,
                "sthana_bala": round(result.sthana_bala_total, 2),
                "dig_bala": round(result.dig_bala, 2),
                "kala_bala": round(result.kala_bala, 2),
                "chesta_bala": round(result.chesta_bala, 2),
                "naisargika_bala": round(result.naisargika_bala, 2),
                "drik_bala": round(result.drik_bala, 2),
            }

        # Sort by strength
        sorted_planets = sorted(summary.items(), key=lambda x: x[1]["total_rupas"], reverse=True)

        return {
            "planets": dict(sorted_planets),
            "strongest_planet": sorted_planets[0][0] if sorted_planets else None,
            "weakest_planet": sorted_planets[-1][0] if sorted_planets else None,
        }


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    engine = ShadbalaEngine()

    # Test with sample planetary positions
    test_longitudes = {
        "Sun": 45.5,      # 15°30' Taurus
        "Moon": 120.0,    # 0° Leo
        "Mars": 200.0,    # 20° Libra
        "Mercury": 65.0,  # 5° Gemini
        "Jupiter": 300.0, # 0° Aquarius
        "Venus": 15.0,    # 15° Aries
        "Saturn": 250.0,  # 10° Sagittarius
    }

    test_speeds = {
        "Sun": 0.98, "Moon": 13.5, "Mars": 0.52,
        "Mercury": 1.2, "Jupiter": 0.08, "Venus": 1.1, "Saturn": 0.03
    }

    results = engine.calculate_all(
        planet_longitudes=test_longitudes,
        ascendant_lon=100.0,
        planet_speeds=test_speeds,
        birth_time_hours=10.5,
        sunrise_hours=6.0,
        is_day_birth=True,
        year=1990
    )

    print("=" * 60)
    print("SHADBALA RESULTS (in Virupas / Rupas)")
    print("=" * 60)

    for planet, result in results.items():
        print(f"\n{planet}:")
        print(f"  Sthana Bala: {result.sthana_bala_total:.1f} Virupas")
        print(f"    - Uchcha: {result.uchcha_bala:.1f}, Saptavargaja: {result.saptavargaja_bala:.1f}")
        print(f"    - Ojayugma: {result.ojayugma_bala:.1f}, Kendra: {result.kendra_bala:.1f}, Drekkena: {result.drekkena_bala:.1f}")
        print(f"  Dig Bala: {result.dig_bala:.1f}")
        print(f"  Kala Bala: {result.kala_bala:.1f}")
        print(f"  Chesta Bala: {result.chesta_bala:.1f}")
        print(f"  Naisargika Bala: {result.naisargika_bala:.1f}")
        print(f"  Drik Bala: {result.drik_bala:.1f}")
        print(f"  TOTAL: {result.total_virupas:.1f} Virupas = {result.total_rupas:.2f} Rupas")
        print(f"  Category: {result.strength_category}")

    print("\n" + "=" * 60)
    summary = engine.get_strength_summary(results)
    print(f"Strongest: {summary['strongest_planet']}")
    print(f"Weakest: {summary['weakest_planet']}")
