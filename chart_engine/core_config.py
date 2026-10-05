import swisseph as swe

def init_astronomy_engine():
    """
    Globally configures the PySwissEph engine for Vedic Astrology mechanics.
    Enforces the Lahiri Ayanamsa sidereal calculation for all downstream geometry.
    This prevents any downstream system from defaulting to Western Tropical geometry.
    """
    swe.set_ephe_path('') # Defaults to built-in ephemerides
    swe.set_sid_mode(swe.SIDM_LAHIRI)

# Automatically execute upon import to mathematically lock backend state
init_astronomy_engine()
