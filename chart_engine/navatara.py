"""
Navatara Chakra Engine — Phase 17 of KaalDrishti Chart Engine
=============================================================
Navatara Chakra (Nine-Star Wheel) classifies all 27 Nakshatras into 9 Taras
counted cyclically from the native's Janma (birth) Nakshatra.

The 9 Taras and their qualities:
  1. Janma     — Neutral   — Body/Birth energy
  2. Sampat    — Benefic   — Wealth & prosperity
  3. Vipat     — Malefic   — Danger, calamity
  4. Kshema    — Benefic   — Well-being, comfort
  5. Pratyak   — Malefic   — Obstacles, reversal
  6. Sadhaka   — Benefic   — Achievement, power
  7. Vadha     — Malefic   — Affliction, destruction
  8. Mitra     — Benefic   — Friends, allies
  9. Ati-Mitra — Benefic   — Great friends, maximum support

The cycle repeats: Nakshatra 28 maps back to Tara 1 (Janma), etc.

Two modes are computed:
  - Natal:   planet positions at birth vs Janma Nakshatra
  - Transit: current planet positions vs Janma Nakshatra (actionable)
"""

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

TARA_DATA = {
    1: {"name": "Janma",     "quality": "Neutral", "keyword": "Body/Birth",       "description": "The birth star itself. Represents the physical self and core identity. Transit planets here are personally significant."},
    2: {"name": "Sampat",    "quality": "Benefic", "keyword": "Wealth",           "description": "Prosperity and abundance. Planets transiting here or placed here natally support financial growth."},
    3: {"name": "Vipat",     "quality": "Malefic", "keyword": "Danger",           "description": "Calamity and obstacles. Malefic planets transiting Vipat Tara demand extra caution in actions."},
    4: {"name": "Kshema",    "quality": "Benefic", "keyword": "Well-being",       "description": "Comfort and health. Benefic influences here support physical and mental well-being."},
    5: {"name": "Pratyak",   "quality": "Malefic", "keyword": "Obstruction",      "description": "Reversal and blockage. Efforts made under Pratyak Tara influence often face unexpected reversals."},
    6: {"name": "Sadhaka",   "quality": "Benefic", "keyword": "Achievement",      "description": "Power and accomplishment. Actions initiated with planets in Sadhaka Tara carry strong momentum."},
    7: {"name": "Vadha",     "quality": "Malefic", "keyword": "Affliction",       "description": "Destruction and affliction. The most challenging Tara. Avoid major decisions when key planets occupy Vadha Tara."},
    8: {"name": "Mitra",     "quality": "Benefic", "keyword": "Friends",          "description": "Alliances and support. Relationships and partnerships formed under Mitra Tara are durable."},
    9: {"name": "Ati-Mitra", "quality": "Benefic", "keyword": "Great Friends",    "description": "Maximum harmony. The most auspicious external Tara. Planets here deliver outstanding support and results."},
}

QUALITY_ALERT = {"Malefic": "⚠️", "Benefic": "✅", "Neutral": "🔵"}

PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _nak_index(longitude: float) -> int:
    """Convert ecliptic longitude (0–360) to 0-based Nakshatra index (0–26)."""
    return int(longitude % 360 / (360.0 / 27.0)) % 27


def _tara_number(planet_nak: int, janma_nak: int) -> int:
    """
    Compute Tara number (1–9) for a planet nakshatra relative to Janma Nakshatra.
    Formula: ((planet_nak - janma_nak) % 27) // 3 + 1
    """
    offset = (planet_nak - janma_nak) % 27
    return (offset // 3) + 1


class NavataraChakra:
    """
    Computes the Navatara Chakra for natal and transit planet positions.
    """

    @staticmethod
    def _build_entry(planet_name: str, planet_lon: float, janma_nak: int) -> dict:
        """Build a single planet's Navatara entry."""
        nak_idx = _nak_index(planet_lon)
        tara_num = _tara_number(nak_idx, janma_nak)
        tara = TARA_DATA[tara_num]
        pada = int((planet_lon % (360.0 / 27.0)) // (360.0 / 27.0 / 4.0)) + 1
        return {
            "planet":       planet_name,
            "nakshatra":    NAKSHATRA_NAMES[nak_idx],
            "nakshatra_index": nak_idx,
            "nakshatra_pada": pada,
            "tara_number":  tara_num,
            "tara_name":    tara["name"],
            "quality":      tara["quality"],
            "keyword":      tara["keyword"],
            "description":  tara["description"],
            "alert":        QUALITY_ALERT[tara["quality"]],
        }

    @staticmethod
    def _build_summary(planet_entries: list[dict], mode: str) -> dict:
        """Summarise the Navatara matrix."""
        malefic_taras = [e for e in planet_entries if e["quality"] == "Malefic"]
        benefic_taras = [e for e in planet_entries if e["quality"] == "Benefic"]
        tara_counts   = {}
        for e in planet_entries:
            tara_counts[e["tara_name"]] = tara_counts.get(e["tara_name"], 0) + 1

        # Find which malefic Tara has the most planets (highest risk)
        critical = None
        for e in malefic_taras:
            if e["planet"] in ("Saturn", "Mars", "Rahu", "Ketu"):
                critical = e
                break
        if not critical and malefic_taras:
            critical = malefic_taras[0]

        return {
            "mode":              mode,
            "malefic_count":     len(malefic_taras),
            "benefic_count":     len(benefic_taras),
            "neutral_count":     len(planet_entries) - len(malefic_taras) - len(benefic_taras),
            "malefic_planets":   [e["planet"] for e in malefic_taras],
            "benefic_planets":   [e["planet"] for e in benefic_taras],
            "tara_distribution": tara_counts,
            "critical_alert":    critical["planet"] + " in " + critical["tara_name"] + " (" + critical["keyword"] + ")" if critical else None,
            "overall_strength":  "Challenging" if len(malefic_taras) >= 4 else "Mixed" if len(malefic_taras) >= 2 else "Favorable",
        }

    @staticmethod
    def calculate(
        moon_lon:      float,
        planet_lons:   dict,
        ascendant_lon: float,
        transit_lons:  dict | None = None,
    ) -> dict:
        """
        Compute the complete Navatara Chakra.

        Parameters
        ----------
        moon_lon       : Moon's natal ecliptic longitude (determines Janma Nakshatra)
        planet_lons    : Dict of planet_name → natal ecliptic longitude
        ascendant_lon  : Natal Ascendant longitude
        transit_lons   : Dict of planet_name → current transit longitude (optional)

        Returns
        -------
        Full Navatara Chakra dict with natal, transit (if provided), and summaries.
        """
        janma_nak = _nak_index(moon_lon)
        janma_name = NAKSHATRA_NAMES[janma_nak]
        janma_pada = int((moon_lon % (360.0 / 27.0)) // (360.0 / 27.0 / 4.0)) + 1

        # --- Natal Navatara ---
        natal_planets = []
        # Planets in canonical order
        for planet in PLANET_ORDER:
            if planet in planet_lons:
                natal_planets.append(
                    NavataraChakra._build_entry(planet, planet_lons[planet], janma_nak)
                )
        # Ascendant Nakshatra
        natal_planets.append(
            NavataraChakra._build_entry("Ascendant", ascendant_lon, janma_nak)
        )

        natal_summary = NavataraChakra._build_summary(natal_planets, "Natal")

        result = {
            "janma_nakshatra":       janma_name,
            "janma_nakshatra_index": janma_nak,
            "janma_nakshatra_pada":  janma_pada,
            "natal": {
                "planets": natal_planets,
                "summary": natal_summary,
            },
        }

        # --- Transit Navatara (if transit longitudes provided) ---
        if transit_lons:
            transit_planets = []
            for planet in PLANET_ORDER:
                if planet in transit_lons:
                    transit_planets.append(
                        NavataraChakra._build_entry(planet, transit_lons[planet], janma_nak)
                    )
            transit_summary = NavataraChakra._build_summary(transit_planets, "Transit")
            result["transit"] = {
                "planets": transit_planets,
                "summary": transit_summary,
            }

        return result
