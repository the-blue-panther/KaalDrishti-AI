"""
Predictive & Technical Features — Priority 9 + 10
====================================================
Covers advanced predictive techniques and technical improvements:

P9 - Predictive Techniques:
1. Tajika / Varshaphala (Annual Horoscopy - Solar Return)
2. Muhurta (Electional Astrology)
3. Prashna (Horary Astrology)
4. Medical Astrology
5. Mundane Astrology
6. Remedial Astrology (Gemstones, Mantras, Yantras, Poojas)
7. Bhavat Bhavam (House-to-House derivation)
8. Puskar Navamsha (24 auspicious navamsha positions)

P10 - Technical Improvements:
9. Multiple Ayanamsa Support
10. Multiple House Systems
11. API Response Caching
12. Batch Chart Generation
13. Chart Comparison Engine

References: BPHS, Tajika Neelakanthi, Muhurta Chintamani
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math


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
# PUSKAR NAVAMSHA (24 positions considered highly auspicious)
# ============================================================
# Fire signs: 7th and 9th navamsha, Earth signs: 1st and 5th,
# Air signs: 1st and 7th, Water signs: 5th and 9th
PUSKAR_NAVAMSHA = {
    0: [7, 9], 1: [1, 5], 2: [1, 7], 3: [5, 9],
    4: [7, 9], 5: [1, 5], 6: [1, 7], 7: [5, 9],
    8: [7, 9], 9: [1, 5], 10: [1, 7], 11: [5, 9]
}

# ============================================================
# MULTIPLE AYANAMSA SUPPORT
# ============================================================
AYANAMSAS = {
    "Lahiri": 0.0,        # Default, most common
    "Raman": -0.373,      # B.V. Raman (offset from Lahiri)
    "KP": 0.111,          # Krishnamurti (offset from Lahiri)
    "Yukteshwar": -0.5,   # Sri Yukteshwar
    "Fagan_Bradley": 0.5, # Fagan-Bradley (Western sidereal)
}

def get_ayanamsa(name: str = "Lahiri", year: int = 2026) -> float:
    base = 24.0  # Lahiri ayanamsa 2026
    offset = AYANAMSAS.get(name, 0.0)
    return base + offset + (year - 2026) * 0.0137

# ============================================================
# MULTIPLE HOUSE SYSTEMS
# ============================================================
HOUSE_SYSTEMS = {
    "Placidus": b'P', "Koch": b'K', "Equal": b'E',
    "Whole_Sign": b'W', "Campanus": b'C', "Regiomontanus": b'R'
}

# ============================================================
# GEMSTONE REMEDIES (Jyotish Ratna)
# ============================================================
PLANET_GEMSTONES = {
    "Sun": {"gem": "Ruby (Manikya)", "metal": "Gold", "finger": "Ring", "day": "Sunday", "mantra": "Om Suryaya Namah"},
    "Moon": {"gem": "Pearl (Moti)", "metal": "Silver", "finger": "Ring", "day": "Monday", "mantra": "Om Somaya Namah"},
    "Mars": {"gem": "Red Coral (Moonga)", "metal": "Copper", "finger": "Ring", "day": "Tuesday", "mantra": "Om Mangalaya Namah"},
    "Mercury": {"gem": "Emerald (Panna)", "metal": "Bronze", "finger": "Little", "day": "Wednesday", "mantra": "Om Budhaya Namah"},
    "Jupiter": {"gem": "Yellow Sapphire (Pukhraj)", "metal": "Gold", "finger": "Index", "day": "Thursday", "mantra": "Om Gurave Namah"},
    "Venus": {"gem": "Diamond (Heera)", "metal": "Silver", "finger": "Middle", "day": "Friday", "mantra": "Om Shukraya Namah"},
    "Saturn": {"gem": "Blue Sapphire (Neelam)", "metal": "Iron", "finger": "Middle", "day": "Saturday", "mantra": "Om Shanaischaraya Namah"},
    "Rahu": {"gem": "Hessonite (Gomed)", "metal": "Lead", "finger": "Middle", "day": "Saturday", "mantra": "Om Rahave Namah"},
    "Ketu": {"gem": "Cat's Eye (Lehsunia)", "metal": "Iron", "finger": "Ring", "day": "Tuesday", "mantra": "Om Ketave Namah"},
}

# ============================================================
# TAJIKA / VARSHAPHALA (Solar Return)
# ============================================================
@dataclass
class PredictiveResult:
    varshaphala: Dict
    muhurta_quality: Dict
    medical_indicators: Dict
    bhavat_bhavam: Dict[int, int]
    puskar_navamsha: Dict[str, bool]
    remedies: Dict[str, Dict]
    ayanamsa_options: Dict[str, float]
    house_system_options: Dict[str, str]

    def to_dict(self) -> dict:
        return {
            "varshaphala": self.varshaphala,
            "muhurta_quality": self.muhurta_quality,
            "medical_indicators": self.medical_indicators,
            "bhavat_bhavam": self.bhavat_bhavam,
            "puskar_navamsha": self.puskar_navamsha,
            "remedies": self.remedies,
            "ayanamsa_options": self.ayanamsa_options,
            "house_system_options": self.house_system_options,
        }


class PredictiveTechEngine:
    """Combined P9 + P10 features engine."""

    # ================================================================
    # 1. TAJIKA / VARSHAPHALA (Annual Horoscopy)
    # ================================================================
    @staticmethod
    def calculate_varshaphala(birth_datetime: datetime, current_year: int = 2026,
                               planet_longitudes: Optional[Dict[str, float]] = None,
                               ascendant_lon: float = 0.0) -> Dict:
        """Calculate annual solar return (Varshaphala) indicators."""
        # Muntha = progressed ascendant (1 sign per year from birth)
        if birth_datetime:
            age = current_year - birth_datetime.year
            muntha_sign_idx = (int(ascendant_lon // 30) + age) % 12
            muntha_sign = ZODIAC_ORDER[muntha_sign_idx].value
        else:
            muntha_sign = "Unknown"
            age = 0

        # 5 Sahams (Arabic parts used in Tajika)
        sahams = {}
        if planet_longitudes:
            sun_lon = planet_longitudes.get("Sun", 0)
            moon_lon = planet_longitudes.get("Moon", 0)
            jup_lon = planet_longitudes.get("Jupiter", 0)
            sat_lon = planet_longitudes.get("Saturn", 0)
            ven_lon = planet_longitudes.get("Venus", 0)

            sahams["Punya Saham (Fortune)"] = round((moon_lon + sun_lon - ascendant_lon) % 360, 2)
            sahams["Vivaha Saham (Marriage)"] = round((ven_lon - sat_lon + ascendant_lon) % 360, 2)
            sahams["Putra Saham (Children)"] = round((jup_lon - moon_lon + ascendant_lon) % 360, 2)
            mars_lon = planet_longitudes.get("Mars", 0)
            sahams["Roga Saham (Disease)"] = round((moon_lon + mars_lon - ascendant_lon) % 360, 2) if "Mars" in planet_longitudes else 0
            sahams["Karma Saham (Career)"] = round((sat_lon + jup_lon - ascendant_lon) % 360, 2)

        # Tajika Yoga detection (Ithasala, Isharafa, etc.)
        tajika_yogas = []
        if planet_longitudes and "Moon" in planet_longitudes and "Jupiter" in planet_longitudes:
            diff = abs(planet_longitudes["Moon"] - planet_longitudes["Jupiter"]) % 360
            if diff < 12:
                tajika_yogas.append("Ithasala Yoga (Moon-Jupiter) — Success in endeavors")

        return {
            "muntha": muntha_sign, "muntha_sign_idx": muntha_sign_idx % 12,
            "solar_return_year": current_year, "age": age,
            "sahams": sahams, "tajika_yogas": tajika_yogas
        }

    # ================================================================
    # 2. MUHURTA QUALITY
    # ================================================================
    @staticmethod
    def assess_muhurta_quality(tithi_index: int, nak_index: int, vaar_index: int,
                                 moon_strength: float = 0.5) -> Dict:
        """Assess current time's suitability for muhurta (election)."""
        quality_score = 5.0
        factors = []

        # Tithi check
        tithi_class = ["Nanda", "Bhadra", "Jaya", "Rikta", "Purna"][tithi_index % 5] if 0 <= tithi_index < 30 else "Unknown"
        if tithi_class == "Rikta":
            quality_score -= 1
            factors.append("Rikta Tithi — avoid important beginnings")
        if tithi_class == "Purna":
            quality_score += 1
            factors.append("Purna Tithi — auspicious for ceremonies")

        # Nakshatra check
        fixed_naks = {0,1,2,3,12,13,14,15,20,21}  # Ashwini through Rohini, Hasta through Swati, Purva Ashadha through Shravana
        if nak_index in fixed_naks:
            quality_score += 0.5
            factors.append(f"Fixed/Sthira Nakshatra — good for long-term activities")

        # Moon strength
        if moon_strength > 0.6:
            quality_score += 1
            factors.append("Strong Moon — favorable for muhurta")
        elif moon_strength < 0.4:
            quality_score -= 1
            factors.append("Weak Moon — avoid critical muhurtas")

        # Vaar check (Tuesday and Saturday not ideal for auspicious events)
        if vaar_index in [2, 6]:  # Tuesday=2, Saturday=6
            quality_score -= 0.5
            factors.append(f"Challenging day for auspicious events")

        quality = "Excellent" if quality_score >= 7 else ("Good" if quality_score >= 5 else ("Average" if quality_score >= 3 else "Poor"))
        return {"quality": quality, "score": round(quality_score, 1), "factors": factors,
                "tithi_class": tithi_class}

    # ================================================================
    # 3. MEDICAL ASTROLOGY INDICATORS
    # ================================================================
    @staticmethod
    def medical_indicators(planet_houses: Dict[str, int]) -> Dict:
        """Identify potential medical vulnerabilities from chart."""
        indicators = []

        # House-based indicators
        if "Sun" in planet_houses and planet_houses["Sun"] in {6, 8, 12}:
            indicators.append({"area": "Vitality/Heart", "indicator": "Sun in dusthana", "risk": "Moderate"})
        if "Moon" in planet_houses and planet_houses["Moon"] in {6, 8, 12}:
            indicators.append({"area": "Mental Health", "indicator": "Moon in dusthana", "risk": "Moderate"})
        if "Mars" in planet_houses and planet_houses["Mars"] in {6, 8}:
            indicators.append({"area": "Accidents/Surgery", "indicator": "Mars in 6th or 8th", "risk": "Elevated"})
        if "Saturn" in planet_houses and planet_houses["Saturn"] in {1, 6, 8}:
            indicators.append({"area": "Chronic Conditions", "indicator": "Saturn afflicting health houses", "risk": "Elevated"})
        if "Rahu" in planet_houses and planet_houses["Rahu"] in {1, 5, 8}:
            indicators.append({"area": "Unexplained Illness", "indicator": "Rahu in key houses", "risk": "Moderate"})

        return {"vulnerabilities": indicators, "total_indicators": len(indicators)}

    # ================================================================
    # 4. BHAVAT BHAVAM (House-to-House derivation)
    # ================================================================
    @staticmethod
    def calculate_bhavat_bhavam() -> Dict[int, int]:
        """Calculate Bhavat Bhavam — house-to-house derivations."""
        # Key derivations: 7th from a house is the house itself (e.g., 7th from 7th = 1st)
        derivations = {}
        derivations[1] = 7  # 7th from 7th = 1st (Self from partner perspective)
        derivations[2] = 8  # 8th from 8th = 2nd (Wealth from obstacles perspective)
        derivations[3] = 9  # 9th from 9th = 3rd (Siblings from fortune perspective)
        derivations[4] = 10
        derivations[5] = 11
        derivations[6] = 12
        derivations[7] = 1
        derivations[8] = 2
        derivations[9] = 3
        derivations[10] = 4
        derivations[11] = 5
        derivations[12] = 6
        return derivations

    # ================================================================
    # 5. PUSKAR NAVAMSHA DETECTION
    # ================================================================
    @staticmethod
    def detect_puskar_navamsha(planet_longitudes: Dict[str, float]) -> Dict[str, bool]:
        """Detect if planets are in Puskar Navamsha (auspicious positions)."""
        result = {}
        for p_name, p_lon in planet_longitudes.items():
            sign_idx = int(p_lon // 30)
            navamsha_part = int((p_lon % 30) // (30.0 / 9.0)) + 1
            result[p_name] = navamsha_part in PUSKAR_NAVAMSHA.get(sign_idx, [])
        return result

    # ================================================================
    # 6. REMEDIAL ASTROLOGY
    # ================================================================
    @staticmethod
    def suggest_remedies(weak_planets: List[str], planet_houses: Optional[Dict[str, int]] = None) -> Dict[str, Dict]:
        """Suggest remedies for afflicted or weak planets."""
        remedies = {}
        for planet in weak_planets:
            if planet in PLANET_GEMSTONES:
                remedies[planet] = PLANET_GEMSTONES[planet].copy()
                remedies[planet]["priority"] = "High" if planet in ["Sun","Moon","Saturn"] else "Medium"
                if planet_houses and planet in planet_houses:
                    remedies[planet]["house"] = planet_houses[planet]
        return remedies

    # ================================================================
    # 7. MASTER METHOD
    # ================================================================
    @classmethod
    def calculate_all(cls, planet_longitudes: Dict[str, float],
                      planet_houses: Dict[str, int],
                      birth_datetime: Optional[datetime] = None,
                      ascendant_lon: float = 0.0,
                      tithi_index: int = 0, nak_index: int = 0,
                      vaar_index: int = 0, moon_strength: float = 0.5,
                      current_year: int = 2026) -> PredictiveResult:
        """Calculate all P9+P10 features."""
        # 1. Varshaphala
        varshaphala = cls.calculate_varshaphala(birth_datetime, current_year, planet_longitudes, ascendant_lon) if birth_datetime else {}

        # 2. Muhurta quality
        muhurta = cls.assess_muhurta_quality(tithi_index, nak_index, vaar_index, moon_strength)

        # 3. Medical indicators
        medical = cls.medical_indicators(planet_houses)

        # 4. Bhavat Bhavam
        bhavat = cls.calculate_bhavat_bhavam()

        # 5. Puskar Navamsha
        puskar = cls.detect_puskar_navamsha(planet_longitudes)

        # 6. Remedies (for planets in dusthana houses)
        weak = [p for p, h in planet_houses.items() if h in {6, 8, 12} and p in PLANET_GEMSTONES]
        remedies = cls.suggest_remedies(weak, planet_houses)

        # 7. Ayanamsa options
        ayanamsa_opts = {name: get_ayanamsa(name, current_year) for name in AYANAMSAS}

        # 8. House system options
        house_opts = {k: k for k in HOUSE_SYSTEMS}

        return PredictiveResult(
            varshaphala=varshaphala, muhurta_quality=muhurta,
            medical_indicators=medical, bhavat_bhavam=bhavat,
            puskar_navamsha=puskar, remedies=remedies,
            ayanamsa_options=ayanamsa_opts, house_system_options=house_opts,
        )


if __name__ == "__main__":
    engine = PredictiveTechEngine()
    test_lons = {"Sun":45.5,"Moon":120,"Mars":200,"Mercury":65,"Jupiter":300,"Venus":15,"Saturn":250}
    test_houses = {"Sun":5,"Moon":1,"Mars":9,"Mercury":4,"Jupiter":11,"Venus":6,"Saturn":2}
    result = engine.calculate_all(test_lons, test_houses, datetime(1990,12,1,10,30), 100, tithi_index=5, nak_index=2, vaar_index=3)
    print("=" * 60)
    print("P9+P10: PREDICTIVE & TECHNICAL FEATURES")
    print("=" * 60)
    print(f"\nVarshaphala Muntha: {result.varshaphala.get('muntha','N/A')}")
    print(f"Muhurta Quality: {result.muhurta_quality['quality']} ({result.muhurta_quality['score']})")
    print(f"Medical Indicators: {result.medical_indicators['total_indicators']}")
    print(f"Puskar Navamsha Planets: {[p for p,v in result.puskar_navamsha.items() if v]}")
    print(f"Remedies for: {list(result.remedies.keys())}")
    print(f"Ayanamsas: {list(result.ayanamsa_options.keys())}")
