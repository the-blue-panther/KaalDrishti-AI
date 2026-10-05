from chart_engine.models import ZodiacSign, PlanetName
from typing import Dict, List, Optional

# ============================================================
# LORDSHIP & DIGNITY MAPS
# ============================================================

# Planetary Lordship map
SIGN_LORDS = {
    ZodiacSign.ARIES: PlanetName.MARS,
    ZodiacSign.TAURUS: PlanetName.VENUS,
    ZodiacSign.GEMINI: PlanetName.MERCURY,
    ZodiacSign.CANCER: PlanetName.MOON,
    ZodiacSign.LEO: PlanetName.SUN,
    ZodiacSign.VIRGO: PlanetName.MERCURY,
    ZodiacSign.LIBRA: PlanetName.VENUS,
    ZodiacSign.SCORPIO: PlanetName.MARS,
    ZodiacSign.SAGITTARIUS: PlanetName.JUPITER,
    ZodiacSign.CAPRICORN: PlanetName.SATURN,
    ZodiacSign.AQUARIUS: PlanetName.SATURN,
    ZodiacSign.PISCES: PlanetName.JUPITER
}

# Dignity System
EXALTATION = {
    PlanetName.SUN: ZodiacSign.ARIES,
    PlanetName.MOON: ZodiacSign.TAURUS,
    PlanetName.MARS: ZodiacSign.CAPRICORN,
    PlanetName.MERCURY: ZodiacSign.VIRGO,
    PlanetName.JUPITER: ZodiacSign.CANCER,
    PlanetName.VENUS: ZodiacSign.PISCES,
    PlanetName.SATURN: ZodiacSign.LIBRA,
}

DEBILITATION = {
    PlanetName.SUN: ZodiacSign.LIBRA,
    PlanetName.MOON: ZodiacSign.SCORPIO,
    PlanetName.MARS: ZodiacSign.CANCER,
    PlanetName.MERCURY: ZodiacSign.PISCES,
    PlanetName.JUPITER: ZodiacSign.CAPRICORN,
    PlanetName.VENUS: ZodiacSign.VIRGO,
    PlanetName.SATURN: ZodiacSign.ARIES,
}

# Moolatrikona Signs (Root Trine) — Each planet has a specific sign + degree range
MOOLATRIKONA = {
    PlanetName.SUN: (ZodiacSign.LEO, 0.0, 20.0),
    PlanetName.MOON: (ZodiacSign.TAURUS, 4.0, 30.0),
    PlanetName.MARS: (ZodiacSign.ARIES, 0.0, 12.0),
    PlanetName.MERCURY: (ZodiacSign.VIRGO, 16.0, 20.0),
    PlanetName.JUPITER: (ZodiacSign.SAGITTARIUS, 0.0, 10.0),
    PlanetName.VENUS: (ZodiacSign.LIBRA, 0.0, 5.0),
    PlanetName.SATURN: (ZodiacSign.AQUARIUS, 0.0, 20.0),
}

# Own Signs (Swakshetra) — multi-sign for Mars, Mercury, Jupiter, Venus, Saturn
OWN_SIGNS: Dict[PlanetName, List[ZodiacSign]] = {
    PlanetName.SUN: [ZodiacSign.LEO],
    PlanetName.MOON: [ZodiacSign.CANCER],
    PlanetName.MARS: [ZodiacSign.ARIES, ZodiacSign.SCORPIO],
    PlanetName.MERCURY: [ZodiacSign.GEMINI, ZodiacSign.VIRGO],
    PlanetName.JUPITER: [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES],
    PlanetName.VENUS: [ZodiacSign.TAURUS, ZodiacSign.LIBRA],
    PlanetName.SATURN: [ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS],
}

# ============================================================
# NAISARGIKA (PERMANENT/NATURAL) PLANETARY RELATIONSHIPS
# Based on BPHS Chapter 3, Shloka 55-58
# ============================================================

# Natural Friends: Planets that are permanently friendly
NAISARGIKA_FRIENDS: Dict[PlanetName, List[PlanetName]] = {
    PlanetName.SUN: [PlanetName.MOON, PlanetName.MARS, PlanetName.JUPITER],
    PlanetName.MOON: [PlanetName.SUN, PlanetName.MERCURY],
    PlanetName.MARS: [PlanetName.SUN, PlanetName.MOON, PlanetName.JUPITER],
    PlanetName.MERCURY: [PlanetName.SUN, PlanetName.VENUS],
    PlanetName.JUPITER: [PlanetName.SUN, PlanetName.MOON, PlanetName.MARS],
    PlanetName.VENUS: [PlanetName.MERCURY, PlanetName.SATURN],
    PlanetName.SATURN: [PlanetName.MERCURY, PlanetName.VENUS],
}

# Natural Enemies: Planets that are permanently hostile
NAISARGIKA_ENEMIES: Dict[PlanetName, List[PlanetName]] = {
    PlanetName.SUN: [PlanetName.VENUS, PlanetName.SATURN],
    PlanetName.MOON: [],  # Moon has no natural enemies
    PlanetName.MARS: [PlanetName.MERCURY],
    PlanetName.MERCURY: [PlanetName.MOON],
    PlanetName.JUPITER: [PlanetName.MERCURY, PlanetName.VENUS],
    PlanetName.VENUS: [PlanetName.SUN, PlanetName.MOON],
    PlanetName.SATURN: [PlanetName.SUN, PlanetName.MOON, PlanetName.MARS],
}

# Natural Neutrals: All others not in friends or enemies lists
# Derived from friends/enemies automatically below


def get_naisargika_relationship(planet: PlanetName, relative_to: PlanetName) -> str:
    """
    Returns Naisargika (permanent) relationship: 'Friend', 'Enemy', or 'Neutral'.
    """
    if planet == relative_to:
        return "Own"
    if relative_to in NAISARGIKA_FRIENDS.get(planet, []):
        return "Friend"
    if relative_to in NAISARGIKA_ENEMIES.get(planet, []):
        return "Enemy"
    return "Neutral"


# ============================================================
# TATKALIKA (TEMPORARY) PLANETARY RELATIONSHIPS
# Based on BPHS Chapter 3, Shloka 59-61
# Planets in 2nd, 3rd, 4th, 10th, 11th, 12th from a planet are temporary friends
# Planets in 1st, 5th, 6th, 7th, 8th, 9th from a planet are temporary enemies
# ============================================================

TATKALIKA_FRIEND_HOUSES = [2, 3, 4, 10, 11, 12]  # Houses from planet
TATKALIKA_ENEMY_HOUSES = [1, 5, 6, 7, 8, 9]     # Houses from planet (1st = conjunction)


def get_tatkalika_relationship(planet_house: int, relative_planet_house: int) -> str:
    """
    Returns Tatkalika (temporary) relationship based on house positions.
    Calculates house difference: (relative_house - planet_house + 12) % 12 + 1
    """
    diff = ((relative_planet_house - planet_house) % 12) + 1
    if diff in TATKALIKA_FRIEND_HOUSES:
        return "Friend"
    elif diff in TATKALIKA_ENEMY_HOUSES:
        return "Enemy"
    return "Neutral"


# ============================================================
# PANCHADHA MAITRI (5-TIER COMPOUND RELATIONSHIP)
# Combines Naisargika (permanent) + Tatkalika (temporary)
# Produces: Adhimitra (Great Friend), Mitra (Friend), Sama (Neutral),
#           Shatru (Enemy), Adhishatru (Great Enemy)
# ============================================================

def get_compound_relationship(
    planet: PlanetName,
    relative_to: PlanetName,
    planet_house: int,
    relative_house: int
) -> str:
    """
    Calculates the Panchadha Maitri (5-tier compound relationship).

    Matrix:
    - Permanent Friend + Temporary Friend = Adhimitra (Great Friend)
    - Permanent Friend + Temporary Enemy = Sama (Neutral)
    - Permanent Enemy + Temporary Friend = Sama (Neutral)
    - Permanent Enemy + Temporary Enemy = Adhishatru (Great Enemy)
    - Permanent Neutral + Temporary Friend = Mitra (Friend)
    - Permanent Neutral + Temporary Enemy = Shatru (Enemy)
    - Either Neutral + other Neutral = Sama (Neutral)
    """
    naisargika = get_naisargika_relationship(planet, relative_to)
    if naisargika == "Own":
        return "Adhimitra"

    tatkalika = get_tatkalika_relationship(planet_house, relative_house)

    # Compound matrix
    if naisargika == "Friend" and tatkalika == "Friend":
        return "Adhimitra"
    elif naisargika == "Friend" and tatkalika == "Enemy":
        return "Sama"
    elif naisargika == "Enemy" and tatkalika == "Friend":
        return "Sama"
    elif naisargika == "Enemy" and tatkalika == "Enemy":
        return "Adhishatru"
    elif naisargika == "Neutral" and tatkalika == "Friend":
        return "Mitra"
    elif naisargika == "Neutral" and tatkalika == "Enemy":
        return "Shatru"
    else:
        return "Sama"


# ============================================================
# DASHA LORDS
# ============================================================

# Vimshottari Dasha sequence strictly mapped by Nakshatra (0-26 mapped out)
# The sequence of 9 lords repeats 3 times across the 27 Nakshatras
DASHA_LORDS_ORDER = [
    PlanetName.KETU,
    PlanetName.VENUS,
    PlanetName.SUN,
    PlanetName.MOON,
    PlanetName.MARS,
    PlanetName.RAHU,
    PlanetName.JUPITER,
    PlanetName.SATURN,
    PlanetName.MERCURY
]


def get_dasha_lord(nakshatra_index: int) -> PlanetName:
    # nakshatra index is 0-26
    ruling_lord_index = nakshatra_index % 9
    return DASHA_LORDS_ORDER[ruling_lord_index]


# ============================================================
# FULL DIGNITY DETERMINATION (7-tier)
# Moolatrikona → Own → Great Friend → Friend → Neutral → Enemy → Debilitated
# ============================================================

def determine_full_dignity(
    planet: PlanetName,
    sign: ZodiacSign,
    degree_in_sign: float,
    planet_house: int,
    all_planet_houses: Optional[Dict[str, int]] = None
) -> str:
    """
    Determines the FULL 7-tier dignity for a planet in a given sign.

    Returns one of:
    - "Exalted"
    - "Moolatrikona"
    - "Own Sign"
    - "Great Friend" (Adhimitra)
    - "Friend" (Mitra)
    - "Neutral" (Sama)
    - "Enemy" (Shatru)
    - "Debilitated"
    - "Great Enemy" (Adhishatru)
    """
    # Check Exaltation first
    if EXALTATION.get(planet) == sign:
        return "Exalted"

    # Check Debilitation
    if DEBILITATION.get(planet) == sign:
        return "Debilitated"

    # Check Moolatrikona (sign + degree range)
    mt_data = MOOLATRIKONA.get(planet)
    if mt_data and mt_data[0] == sign and mt_data[1] <= degree_in_sign < mt_data[2]:
        return "Moolatrikona"

    # Check Own Sign
    own_signs = OWN_SIGNS.get(planet, [])
    if sign in own_signs:
        return "Own Sign"

    # For compound relationships, we need the lord of this sign and house positions
    sign_lord = SIGN_LORDS.get(sign)
    if sign_lord and all_planet_houses and sign_lord.value in all_planet_houses:
        lord_house = all_planet_houses[sign_lord.value]
        compound = get_compound_relationship(planet, sign_lord, planet_house, lord_house)
        return compound

    # Fallback: just use Naisargika relationship with sign lord
    if sign_lord:
        return get_naisargika_relationship(planet, sign_lord)

    return "Neutral"
