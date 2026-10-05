from chart_engine.models import AstrologicalPosition, ZodiacSign, PlanetName
from chart_engine.coordinate_transformer import ZODIAC_ORDER
import swisseph as swe
import math

# Traditional Vedic Lookup Tables
TITHI_NAMES = [
    "Prathama", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashti", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima / Amavasya"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]



VAAR_NAMES = ["Ravivar (Sunday)", "Somvar (Monday)", "Mangalvar (Tuesday)", "Budhvar (Wednesday)", "Guruvar (Thursday)", "Shukravar (Friday)", "Shanivar (Saturday)"]

# 11 Karanas — seven movable Karanas repeat; four are fixed.
#
# The canonical 60 half-tithi positions are intentionally represented below
# instead of inferred from a tithi number.  Position 0 (0° <= Moon-Sun < 6°)
# is Kimstughna, positions 1..56 are eight cycles of the seven movable
# Karanas, and positions 57..59 are Shakuni, Chatushpada, and Naga.  This is
# a deterministic Panchang rule (category A); interpretations of a Karana are
# outside this calculation.
KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]
MOVABLE_KARANAS = KARANA_NAMES[:7]
KARANA_SEQUENCE_60 = (
    "Kimstughna",
    *(MOVABLE_KARANAS * 8),
    "Shakuni",
    "Chatushpada",
    "Naga",
)

# 27 Yogas (based on Sun + Moon longitude sum)
YOGA_NAMES = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya",
    "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

class AstrologicalDerivation:
    @staticmethod
    def _partition_index(value: float, total_span: float, divisions: int) -> int:
        """Return a half-open equal-part index with normalized-edge tolerance."""
        scaled = value * divisions / total_span
        nearest = round(scaled)
        # Modulo after an absolute longitude can lose several ulps at repeated
        # boundaries (notably 30/11-degree varga edges).
        boundary_tolerance = 16.0 * math.ulp(total_span) * divisions / total_span
        if abs(scaled - nearest) <= boundary_tolerance:
            scaled = float(nearest)
        return min(divisions - 1, int(math.floor(scaled)))

    @staticmethod
    def _equal_division_index(degree_in_sign: float, divisions: int) -> int:
        return AstrologicalDerivation._partition_index(degree_in_sign, 30.0, divisions)

    @staticmethod
    def calculate_karana(lunar_elongation: float) -> tuple[str, int, int]:
        """Return Karana name, legacy name index, and canonical half-tithi position.

        ``lunar_elongation`` is the normalized Moon-minus-Sun angle.  A
        Karana occupies a half tithi (6 degrees), and interval ownership is
        half-open: [start, end).  Normalisation makes 360 degrees identical
        to 0 degrees and avoids a position-60 indexing error.
        """
        normalized = lunar_elongation % 360.0
        half_tithi_position = AstrologicalDerivation._partition_index(normalized, 360.0, 60)
        karana_name = KARANA_SEQUENCE_60[half_tithi_position]
        return karana_name, KARANA_NAMES.index(karana_name), half_tithi_position

    @staticmethod
    def calculate_houses(jd_ut: float, lat: float, lon_geo: float, positions: dict[PlanetName, AstrologicalPosition], zodiac_order: list[ZodiacSign]) -> ZodiacSign:
        """
        Generates the mathematical Ascendant (Lagna) and applies the Vedic Whole-Sign House paradigm.
        """
        # Calculate houses using Placidus ('P') mathematically for the cusps, but explicitly extract Ascendant
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        ayanamsa = swe.get_ayanamsa_ut(jd_ut)
        cusps, ascmc = swe.houses(jd_ut, lat, lon_geo, b'P')
        ascendant_longitude = (ascmc[0] - ayanamsa) % 360.0 # The exact Ecliptic intersection Ascendant shifted to Sidereal Lahiri

        asc_sign_index = int(ascendant_longitude // 30)
        ascendant_sign = zodiac_order[asc_sign_index]

                # Apply Vedic Whole-Sign geometric shifting without mutating the
        # upstream positional models. The returned mapping is the derived
        # positional state owned by the chart computation.
        positioned = {}
        for name, pos in positions.items():
            planet_sign_index = zodiac_order.index(pos.sign)
            # 1st house is strictly the Ascendant's sign block
            house_num = ((planet_sign_index - asc_sign_index) % 12) + 1
            positioned[name] = pos.model_copy(update={"house_number": house_num})

        positions.clear()
        positions.update(positioned)
        return ascendant_sign, ascendant_longitude


    @staticmethod
    def calculate_vargas(lon: float, zodiac_order: list[ZodiacSign]) -> dict[str, str]:
        """
        Sub-divides the Ecliptic longitudes into deep karmic Varga metrics.
        Implements 19 Vargas: D1-D60 including D5, D6, D8, D11, D16, D20, D24, D27, D30, D40, D45.
        """
        if not math.isfinite(lon) or not 0.0 <= lon < 360.0:
            raise ValueError("Varga longitude must be finite and in [0, 360)")
        if len(zodiac_order) != 12:
            raise ValueError("zodiac_order must contain exactly 12 signs")
        vargas = {}
        sign_index = int(lon // 30)
        degree_in_sign = lon % 30
        is_odd_sign = (sign_index % 2 == 0) # 0=Aries (odd), 1=Taurus (even)

        # 1. D2 - Hora (Wealth)
        if is_odd_sign:
            d2_index = 4 if degree_in_sign < 15.0 else 3 # Leo or Cancer
        else:
            d2_index = 3 if degree_in_sign < 15.0 else 4 # Cancer or Leo
        vargas['D2_Hora'] = zodiac_order[d2_index].value

        # 2. D3 - Drekkana (Siblings)
        d3_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 3)
        if d3_part == 0: d3_index = sign_index
        elif d3_part == 1: d3_index = (sign_index + 4) % 12 # 5th from it
        else: d3_index = (sign_index + 8) % 12 # 9th from it
        vargas['D3_Drekkana'] = zodiac_order[d3_index].value

        # 3. D4 - Chaturthamsha (Luck/Property)
        d4_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 4)
        d4_start_indices = [sign_index, (sign_index + 3) % 12, (sign_index + 6) % 12, (sign_index + 9) % 12]
        vargas['D4_Chaturthamsha'] = zodiac_order[d4_start_indices[d4_part]].value

        # 4. D7 - Saptamsha (Progeny)
        d7_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 7)
        d7_start = sign_index if is_odd_sign else (sign_index + 6) % 12
        vargas['D7_Saptamsha'] = zodiac_order[(d7_start + d7_part) % 12].value

        # 5. D9 - Navamsha (Spouse/Dharma)
        d9_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 9)
        element = sign_index % 4 # 0=Fire, 1=Earth, 2=Air, 3=Water
        if element == 0: d9_start = 0     # Aries
        elif element == 1: d9_start = 9   # Capricorn
        elif element == 2: d9_start = 6   # Libra
        else: d9_start = 3                # Cancer
        vargas['D9_Navamsha'] = zodiac_order[(d9_start + d9_part) % 12].value

        # 6. D10 - Dashamsha (Profession)
        d10_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 10)
        d10_start = sign_index if is_odd_sign else (sign_index + 8) % 12
        vargas['D10_Dashamsha'] = zodiac_order[(d10_start + d10_part) % 12].value

        # 7a. D5 - Panchamsha (Fame/Power) — 5 divisions per sign
        d5_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 5)
        d5_start = sign_index if is_odd_sign else (sign_index + 4) % 12
        vargas['D5_Panchamsha'] = zodiac_order[(d5_start + d5_part) % 12].value

        # 7b. D6 - Shashthamsha (Health/Disease) — 6 divisions per sign
        d6_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 6)
        d6_start = sign_index if is_odd_sign else (sign_index + 5) % 12
        vargas['D6_Shashthamsha'] = zodiac_order[(d6_start + d6_part) % 12].value

        # 7c. D8 - Ashtamsha (Longevity/Obstacles) — 8 divisions per sign
        d8_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 8)
        d8_start = sign_index if is_odd_sign else (sign_index + 4) % 12
        vargas['D8_Ashtamsha'] = zodiac_order[(d8_start + d8_part) % 12].value

        # 7d. D11 - Ekadashamsha (Gains/Income) — 11 divisions per sign
        d11_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 11)
        d11_start = sign_index if is_odd_sign else (sign_index + 5) % 12
        vargas['D11_Ekadashamsha'] = zodiac_order[(d11_start + d11_part) % 12].value

        # 7e. D27 - Saptavimshamsha: the start signs cycle by natal sign
        # position: Aries, Cancer, Libra, Capricorn, then repeat (BPHS rule).
        d27_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 27)
        d27_start = (0, 3, 6, 9)[sign_index % 4]
        vargas['D27_Nakshatramsha'] = zodiac_order[(d27_start + d27_part) % 12].value

        # 7f. D40 - Khavedamsha (Auspicious/Inauspicious) — 40 divisions per sign
        d40_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 40)
        # Khavedamsha starts from Aries in odd signs and Libra in even signs.
        d40_start = 0 if is_odd_sign else 6
        vargas['D40_Khavedamsha'] = zodiac_order[(d40_start + d40_part) % 12].value

        # 7. D12 - Dwadashamsha (Parents)
        d12_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 12)
        vargas['D12_Dwadashamsha'] = zodiac_order[(sign_index + d12_part) % 12].value

        # 8. D20 - Vimshamsha (Spiritual)
        d20_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 20)
        modality = sign_index % 3 # 0=Movable, 1=Fixed, 2=Dual
        if modality == 0: d20_start = 0 # Aries
        elif modality == 1: d20_start = 8 # Sagittarius
        else: d20_start = 4 # Leo
        vargas['D20_Vimshamsha'] = zodiac_order[(d20_start + d20_part) % 12].value

        # 9. D24 - Chaturvimshamsha (Education)
        d24_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 24)
        d24_start = 4 if is_odd_sign else 3 # Leo if odd sign, Cancer if even sign
        vargas['D24_Chaturvimshamsha'] = zodiac_order[(d24_start + d24_part) % 12].value

        # 10. D30 - Trimshamsha (Misfortune/Health)
        if is_odd_sign:
            if degree_in_sign < 5.0: d30_index = 0     # Aries
            elif degree_in_sign < 10.0: d30_index = 10 # Aquarius
            elif degree_in_sign < 18.0: d30_index = 8  # Sagittarius
            elif degree_in_sign < 25.0: d30_index = 2  # Gemini
            else: d30_index = 6                        # Libra
        else:
            if degree_in_sign < 5.0: d30_index = 1     # Taurus
            elif degree_in_sign < 12.0: d30_index = 5  # Virgo
            elif degree_in_sign < 20.0: d30_index = 11 # Pisces
            elif degree_in_sign < 25.0: d30_index = 9  # Capricorn
            else: d30_index = 7                        # Scorpio
        vargas['D30_Trimshamsha'] = zodiac_order[d30_index].value

        # 11. D16 - Shodashamsha (Vehicles/Happiness)
        d16_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 16)
        d16_start = [0, 4, 8][sign_index % 3] # Movable->Aries, Fixed->Leo, Dual->Sagittarius
        vargas['D16_Shodashamsha'] = zodiac_order[(d16_start + d16_part) % 12].value

        # 12. D45 - Akshavedamsha (General Well-being)
        d45_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 45)
        d45_start = [0, 4, 8][sign_index % 3]
        vargas['D45_Akshavedamsha'] = zodiac_order[(d45_start + d45_part) % 12].value

        # 13. D60 - Shashtiamsha (Karma/Past lives)
        # D60's sign mapping counts forward from the natal sign in both odd
        # and even signs. The classical reverse rule applies to the D60 deity
        # sequence, not to divisional sign assignment.
        d60_part = AstrologicalDerivation._equal_division_index(degree_in_sign, 60)
        d60_index = (sign_index + d60_part) % 12
        vargas['D60_Shashtiamsha'] = zodiac_order[d60_index].value

        return vargas

    @staticmethod
    def detect_vargottama(vargas: dict[str, dict[str, str]]) -> dict:
        """
        Detect Vargottama planets (same sign in D1 and D9 Navamsha).
        Vargottama planets are considered especially strong.
        """
        d1 = vargas.get("D1_Main", {})
        d9 = vargas.get("D9_Navamsha", {})
        vargottama = {}
        for planet, d1_sign in d1.items():
            if planet == "Ascendant":
                continue
            d9_sign = d9.get(planet, "")
            vargottama[planet] = (d1_sign == d9_sign)
        # Also check Ascendant
        if "Ascendant" in d1 and "Ascendant" in d9:
            vargottama["Ascendant"] = (d1["Ascendant"] == d9["Ascendant"])
        return vargottama

    @staticmethod
    def calculate_panchang(jd_ut: float, sun_lon: float, moon_lon: float, lat: float, lon_geo: float) -> dict:
        """
        Derives the 5 limbs (Panchang) of time: Tithi, Vaar, Nakshatra, Yoga, Karana.
        Focuses on Tithi, Paksha, and Sunrise-aware Vaar as requested.
        """
        # 1. Tithi & Paksha
        sun_lon = sun_lon % 360.0
        moon_lon = moon_lon % 360.0
        diff = (moon_lon - sun_lon) % 360.0
        tithi_index = AstrologicalDerivation._partition_index(diff, 360.0, 30)
        paksha = "Shukla (Waxing)" if diff < 180.0 else "Krishna (Waning)"

        tithi_num = (tithi_index % 15) + 1
        tithi_name = TITHI_NAMES[tithi_num - 1]
        if tithi_num == 15:
            tithi_name = "Purnima" if diff < 180.0 else "Amavasya"

        # 2. Vaar (Vedic Day) - Accurate to Sunrise
        # Find sunrise before/after JD
        sunrise_status = "swisseph_rise_trans"
        try:
            # PySwissEph's current API is (jd, body, rsmi, geopos, ...).
            # The former six-positional-argument call used the legacy C API
            # order and raised TypeError, silently triggering the fallback.
            res = swe.rise_trans(
                jd_ut - 1.0, swe.SUN, swe.CALC_RISE, (lon_geo, lat, 0),
                flags=swe.FLG_SWIEPH,
            )
            if res[0] != 0:
                raise ValueError("sunrise not found for location/date")
            sunrise_jd = res[1][0]

            # If current JD is before today's sunrise, it's technically the previous Vedic day
            if jd_ut < sunrise_jd:
                # Check sunrise of the day before
                res_prev = swe.rise_trans(
                    jd_ut - 1.5, swe.SUN, swe.CALC_RISE, (lon_geo, lat, 0),
                    flags=swe.FLG_SWIEPH,
                )
                if res_prev[0] != 0:
                    raise ValueError("previous sunrise not found for location/date")
                sunrise_jd = res_prev[1][0]
        except Exception:
            # Preserve a result, but expose that sunrise-based weekday could
            # not be calculated (e.g. circumpolar Sun or ephemeris error).
            sunrise_jd = jd_ut
            sunrise_status = "fallback_birth_jd"

        # Day of week (0=Sun, 1=Mon...)
        day_index = int(math.floor(sunrise_jd + 1.5) % 7) # 0=Sunday, 1=Monday...
        vaar = VAAR_NAMES[day_index]

        # 3. Nakshatra (Moon's Nakshatra)
        nak_index = AstrologicalDerivation._partition_index(moon_lon, 360.0, 27)
        nak_name = NAKSHATRA_NAMES[nak_index]
        nakshatra_span = 360.0 / 27.0
        pada_offset = moon_lon % nakshatra_span
        pada = AstrologicalDerivation._partition_index(pada_offset, nakshatra_span, 4) + 1

        # 4. Karana: use the explicit 60 half-tithi sequence.  The legacy
        # 0..10 name index is retained for API compatibility; the canonical
        # position is included so clients can distinguish repeated Karanas.
        karana_name, karana_index, karana_position = AstrologicalDerivation.calculate_karana(diff)

        # 5. Yoga (27 Yogas — based on Sun+Moon longitude sum)
        sun_moon_sum = (sun_lon + moon_lon) % 360.0
        yoga_index = AstrologicalDerivation._partition_index(sun_moon_sum, 360.0, 27)
        yoga_name = YOGA_NAMES[yoga_index]

        return {
            "tithi": f"{tithi_name} ({tithi_num})",
            "tithi_index": tithi_index,
            "paksha": paksha,
            "vaar": vaar,
            "sunrise_jd_ut": sunrise_jd,
            "sunrise_status": sunrise_status,
            "nakshatra": f"{nak_name} (Pada {pada})",
            "nakshatra_index": nak_index,
            "moon_rashi": ZODIAC_ORDER[int(moon_lon // 30)].value,
            "karana": karana_name,
            "karana_index": karana_index,
            "karana_half_tithi_position": karana_position,
            "yoga": yoga_name,
            "yoga_index": yoga_index,
        }
