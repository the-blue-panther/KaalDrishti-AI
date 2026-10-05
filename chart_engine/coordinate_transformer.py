from chart_engine.models import RawAstronomicalState, AstrologicalPosition, ZodiacSign, PlanetName

# Zodiac spans strictly 30 degree bounds sequentially from 0.0 to 360.0
ZODIAC_ORDER = [
    ZodiacSign.ARIES, ZodiacSign.TAURUS, ZodiacSign.GEMINI, ZodiacSign.CANCER,
    ZodiacSign.LEO, ZodiacSign.VIRGO, ZodiacSign.LIBRA, ZodiacSign.SCORPIO,
    ZodiacSign.SAGITTARIUS, ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS, ZodiacSign.PISCES
]

class CoordinateTransformer:
    @staticmethod
    def transform_to_astrological(raw_states: dict[PlanetName, RawAstronomicalState]) -> dict[PlanetName, AstrologicalPosition]:
        """
        Takes the strictly frozen mathematical 0-360 degree Ecliptic array and segments it
        into the structural Zodiac blocks (Signs, Nakshatras, and Padas).
        """
        positions = {}

        for name, state in raw_states.items():
            lon = state.longitude_ecliptic

            # 1. Segment Sign Boundary
            sign_index = int(lon // 30)
            sign = ZODIAC_ORDER[sign_index]

            # 2. Segment Nakshatra Boundary (13.333333... degrees per Nakshatra)
            nak_index = int(lon // (360.0 / 27.0))

            # 3. Segment Pada fractional block (3.333333... degrees per Pada)
            pada_index = int((lon % (360.0 / 27.0)) // (360.0 / 27.0 / 4.0)) + 1

            # 4. Check velocity physics for Retrograde status
            is_retro = state.speed < 0
            # Classical exception: Rahu and Ketu are permanently classified as Retrograde irrespective of mathematical wobble.
            if name in [PlanetName.RAHU, PlanetName.KETU]:
                is_retro = True

            positions[name] = AstrologicalPosition(
                name=name,
                longitude_ecliptic=lon,
                latitude=state.latitude,
                speed=state.speed,
                sign=sign,
                house_number=-1, # Delegated to AstrologicalDerivation for ascendant computation
                nakshatra_index=nak_index,
                nakshatra_pada=pada_index,
                is_retrograde=is_retro
            )

        return positions
