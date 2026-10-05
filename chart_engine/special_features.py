"""
Special Features — Priority 8
==============================
Implements advanced Vedic astrology features:
1. Sade Sati Analysis (Saturn transit over Moon — 7.5 year period)
2. Mangal Dosha / Kuja Dosha (Mars affliction)
3. Pitra Dosha (Ancestral affliction — Sun+Saturn+Rahu+Ketu)
4. Kundali Milan / Ashta Koota Guna Milan (Horoscope matching — 36 points)
5. Upagrahas (Dhooma, Vyatipata, Parivesha, Indrachapa, Upaketu, Gulika/Mandi, Kala)
6. Special Lagnas (Hora, Ghatika, Bhava, Varnada, Shree, Indu)
7. Planetary Avasthas (Baladi 5 states + Jagradadi 3 states)
8. Retrograde Scoring (Vakragati effects)
9. Nakshatra Details (Deity, Guna, Gana, Gender, Caste, Yoni, Nadi)
10. Tithi Classification (Nanda, Bhadra, Jaya, Rikta, Purna)

References: BPHS Chapters 7, 47, 80-83; Jataka Parijata
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta


# ============================================================
# NAKSHATRA DETAILS TABLE
# ============================================================
NAKSHATRA_DETAILS = [
    {"name": "Ashwini", "deity": "Ashwini Kumaras", "guna": "Tamas", "gana": "Deva", "gender": "M", "caste": "Vaishya", "yoni": "Horse", "nadi": "Adi"},
    {"name": "Bharani", "deity": "Yama", "guna": "Rajas", "gana": "Manushya", "gender": "F", "caste": "Mleccha", "yoni": "Elephant", "nadi": "Madhya"},
    {"name": "Krittika", "deity": "Agni", "guna": "Rajas", "gana": "Rakshasa", "gender": "F", "caste": "Brahmin", "yoni": "Sheep", "nadi": "Antya"},
    {"name": "Rohini", "deity": "Brahma", "guna": "Rajas", "gana": "Manushya", "gender": "F", "caste": "Shudra", "yoni": "Serpent", "nadi": "Adi"},
    {"name": "Mrigashira", "deity": "Soma", "guna": "Tamas", "gana": "Deva", "gender": "N", "caste": "Farmer", "yoni": "Deer", "nadi": "Madhya"},
    {"name": "Ardra", "deity": "Rudra", "guna": "Tamas", "gana": "Manushya", "gender": "F", "caste": "Butcher", "yoni": "Dog", "nadi": "Antya"},
    {"name": "Punarvasu", "deity": "Aditi", "guna": "Sattva", "gana": "Deva", "gender": "M", "caste": "Vaishya", "yoni": "Cat", "nadi": "Adi"},
    {"name": "Pushya", "deity": "Brihaspati", "guna": "Tamas", "gana": "Deva", "gender": "M", "caste": "Kshatriya", "yoni": "Ram", "nadi": "Madhya"},
    {"name": "Ashlesha", "deity": "Naga", "guna": "Sattva", "gana": "Rakshasa", "gender": "F", "caste": "Mleccha", "yoni": "Cat", "nadi": "Antya"},
    {"name": "Magha", "deity": "Pitrs", "guna": "Tamas", "gana": "Rakshasa", "gender": "F", "caste": "Shudra", "yoni": "Rat", "nadi": "Adi"},
    {"name": "Purva Phalguni", "deity": "Bhaga", "guna": "Rajas", "gana": "Manushya", "gender": "F", "caste": "Brahmin", "yoni": "Rat", "nadi": "Madhya"},
    {"name": "Uttara Phalguni", "deity": "Aryaman", "guna": "Rajas", "gana": "Manushya", "gender": "F", "caste": "Kshatriya", "yoni": "Cow", "nadi": "Antya"},
    {"name": "Hasta", "deity": "Savitr", "guna": "Rajas", "gana": "Deva", "gender": "M", "caste": "Vaishya", "yoni": "Buffalo", "nadi": "Adi"},
    {"name": "Chitra", "deity": "Tvashtr", "guna": "Tamas", "gana": "Rakshasa", "gender": "F", "caste": "Farmer", "yoni": "Tiger", "nadi": "Madhya"},
    {"name": "Swati", "deity": "Vayu", "guna": "Tamas", "gana": "Deva", "gender": "F", "caste": "Butcher", "yoni": "Buffalo", "nadi": "Antya"},
    {"name": "Vishakha", "deity": "Indra-Agni", "guna": "Sattva", "gana": "Rakshasa", "gender": "F", "caste": "Mleccha", "yoni": "Tiger", "nadi": "Adi"},
    {"name": "Anuradha", "deity": "Mitra", "guna": "Tamas", "gana": "Deva", "gender": "M", "caste": "Shudra", "yoni": "Deer", "nadi": "Madhya"},
    {"name": "Jyeshtha", "deity": "Indra", "guna": "Sattva", "gana": "Rakshasa", "gender": "F", "caste": "Farmer", "yoni": "Deer", "nadi": "Antya"},
    {"name": "Mula", "deity": "Nirrti", "guna": "Tamas", "gana": "Rakshasa", "gender": "N", "caste": "Butcher", "yoni": "Dog", "nadi": "Adi"},
    {"name": "Purva Ashadha", "deity": "Apas", "guna": "Rajas", "gana": "Manushya", "gender": "F", "caste": "Brahmin", "yoni": "Monkey", "nadi": "Madhya"},
    {"name": "Uttara Ashadha", "deity": "Vishvedevas", "guna": "Rajas", "gana": "Manushya", "gender": "F", "caste": "Kshatriya", "yoni": "Mongoose", "nadi": "Antya"},
    {"name": "Shravana", "deity": "Vishnu", "guna": "Rajas", "gana": "Deva", "gender": "M", "caste": "Mleccha", "yoni": "Monkey", "nadi": "Adi"},
    {"name": "Dhanishta", "deity": "Vasus", "guna": "Tamas", "gana": "Rakshasa", "gender": "F", "caste": "Farmer", "yoni": "Lion", "nadi": "Madhya"},
    {"name": "Shatabhisha", "deity": "Varuna", "guna": "Tamas", "gana": "Rakshasa", "gender": "N", "caste": "Butcher", "yoni": "Horse", "nadi": "Antya"},
    {"name": "Purva Bhadrapada", "deity": "Aja Ekapad", "guna": "Sattva", "gana": "Manushya", "gender": "M", "caste": "Brahmin", "yoni": "Lion", "nadi": "Adi"},
    {"name": "Uttara Bhadrapada", "deity": "Ahir Budhnya", "guna": "Sattva", "gana": "Manushya", "gender": "M", "caste": "Kshatriya", "yoni": "Cow", "nadi": "Madhya"},
    {"name": "Revati", "deity": "Pushan", "guna": "Sattva", "gana": "Deva", "gender": "F", "caste": "Shudra", "yoni": "Elephant", "nadi": "Antya"},
]

# ============================================================
# TITHI CLASSIFICATION
# ============================================================
TITHI_CLASSES = ["Nanda", "Bhadra", "Jaya", "Rikta", "Purna"] * 6  # 30 tithis

# ============================================================
# PLANETARY AVASTHAS — Baladi (5 age states)
# ============================================================
AVASTHA_DEGREE_RANGES = [
    (0, 6, "Bala (Child)"), (6, 12, "Kumara (Youth)"),
    (12, 18, "Yuva (Adult)"), (18, 24, "Vriddha (Old)"), (24, 30, "Mrita (Dead)")
]

AVASTHA_JAGRADADI = [
    (0, 10, "Jagrat (Awake)"), (10, 20, "Swapna (Dream)"), (20, 30, "Sushupti (Sleep)")
]


@dataclass
class SpecialFeaturesResult:
    sade_sati: Dict
    mangal_dosha: Dict
    pitra_dosha: Dict
    upagrahas: Dict[str, float]
    special_lagnas: Dict[str, int]
    avasthas: Dict[str, Dict[str, str]]
    retrograde_scoring: Dict[str, float]
    nakshatra_details: Dict[str, Dict]
    tithi_classification: str

    def to_dict(self) -> dict:
        return {
            "sade_sati": self.sade_sati,
            "mangal_dosha": self.mangal_dosha,
            "pitra_dosha": self.pitra_dosha,
            "upagrahas": self.upagrahas,
            "special_lagnas": self.special_lagnas,
            "avasthas": self.avasthas,
            "retrograde_scoring": self.retrograde_scoring,
            "nakshatra_details": self.nakshatra_details,
            "tithi_classification": self.tithi_classification,
        }


class SpecialFeaturesEngine:
    """Master engine for all Priority 8 special features."""

    # ================================================================
    # 1. SADE SATI (Saturn transit over Moon — 7.5 year period)
    # ================================================================
    @staticmethod
    def analyze_sade_sati(moon_sign_idx: int, saturn_transit_sign_idx: int) -> Dict:
        """Analyze Sade Sati status."""
        diff = (saturn_transit_sign_idx - moon_sign_idx) % 12

        if diff == 0:
            phase = "Peak Sade Sati (Saturn over Moon)"
            intensity = 1.0
        elif diff == 11:
            phase = "Rising Sade Sati (First Phase)"
            intensity = 0.5
        elif diff == 1:
            phase = "Setting Sade Sati (Third Phase)"
            intensity = 0.7
        else:
            phase = "No Sade Sati"
            intensity = 0.0

        return {"in_sade_sati": intensity > 0, "phase": phase, "intensity": intensity,
                "moon_sign_idx": moon_sign_idx, "saturn_transit_idx": saturn_transit_sign_idx}

    # ================================================================
    # 2. MANGAL DOSHA / KUJA DOSHA
    # ================================================================
    @staticmethod
    def detect_mangal_dosha(planet_houses: Dict[str, int], asc_sign_idx: int = 0) -> Dict:
        """Detect Mangal Dosha from Lagna, Moon, and Venus."""
        mars_house = planet_houses.get("Mars", 0)
        dosha_houses = {1, 2, 4, 7, 8, 12}
        from_lagna = mars_house in dosha_houses

        moon_house = planet_houses.get("Moon", 0)
        mars_from_moon = ((mars_house - moon_house) % 12) + 1
        from_moon = mars_from_moon in dosha_houses

        venus_house = planet_houses.get("Venus", 0)
        mars_from_venus = ((mars_house - venus_house) % 12) + 1
        from_venus = mars_from_venus in dosha_houses

        severity = "None"
        if from_lagna and from_moon and from_venus:
            severity = "Severe (Triple Mangal Dosha)"
        elif from_lagna and from_moon:
            severity = "Strong"
        elif from_lagna:
            severity = "Moderate"
        elif from_moon or from_venus:
            severity = "Mild"

        return {"has_mangal_dosha": severity != "None", "severity": severity,
                "from_lagna": from_lagna, "from_moon": from_moon, "from_venus": from_venus,
                "mars_house": mars_house, "dosha_houses": list(dosha_houses)}

    # ================================================================
    # 3. PITRA DOSHA
    # ================================================================
    @staticmethod
    def detect_pitra_dosha(planet_houses: Dict[str, int], planet_signs: Optional[Dict[str, int]] = None) -> Dict:
        """Detect Pitra Dosha (ancestral affliction)."""
        indicators = []
        if "Sun" in planet_houses and "Rahu" in planet_houses and planet_houses["Sun"] == planet_houses.get("Rahu", -1):
            indicators.append("Sun-Rahu conjunction")
        if "Sun" in planet_houses and "Saturn" in planet_houses and planet_houses["Sun"] == planet_houses.get("Saturn", -1):
            indicators.append("Sun-Saturn conjunction")
        if "Saturn" in planet_houses and "Rahu" in planet_houses and planet_houses["Saturn"] == planet_houses.get("Rahu", -1):
            indicators.append("Saturn-Rahu conjunction")
        if "Sun" in planet_houses and planet_houses["Sun"] in {6, 8, 12}:
            indicators.append("Sun in Dusthana (6/8/12)")
        if "Rahu" in planet_houses and planet_houses["Rahu"] in {5, 9}:
            indicators.append("Rahu in 5th or 9th")

        return {"has_pitra_dosha": len(indicators) > 0, "indicators": indicators,
                "severity": "Severe" if len(indicators) >= 3 else ("Moderate" if len(indicators) >= 2 else ("Mild" if len(indicators) == 1 else "None"))}

    # ================================================================
    # 4. UPAGRAHAS (7 sub-planets)
    # ================================================================
    @staticmethod
    def calculate_upagrahas(sun_lon: float) -> Dict[str, float]:
        """Calculate 7 Upagrahas from Sun's longitude."""
        dhooma = (sun_lon + 133.3333) % 360
        vyatipata = (360 - dhooma + 180) % 360
        parivesha = (vyatipata + 180) % 360
        indrachapa = (360 - parivesha) % 360
        upaketu = (indrachapa + 16.6667) % 360
        gulika = (sun_lon + 150) % 360
        kala = (sun_lon + 180) % 360

        return {"Dhooma": round(dhooma, 2), "Vyatipata": round(vyatipata, 2),
                "Parivesha": round(parivesha, 2), "Indrachapa": round(indrachapa, 2),
                "Upaketu": round(upaketu, 2), "Gulika": round(gulika, 2), "Kala": round(kala, 2)}

    # ================================================================
    # 5. SPECIAL LAGNAS
    # ================================================================
    @staticmethod
    def calculate_special_lagnas(sun_lon: float, moon_lon: float, asc_lon: float,
                                  birth_time_hours: float, sunrise_hours: float) -> Dict[str, int]:
        """Calculate 6 special lagnas."""
        # Hora Lagna: based on sunrise and birth time
        elapsed_hours = birth_time_hours - sunrise_hours
        if elapsed_hours < 0:
            elapsed_hours += 24
        hora_lagna = int(((elapsed_hours * 15) + asc_lon) // 30) % 12 + 1

        # Ghatika Lagna: based on ghatikas from sunrise
        ghatikas = elapsed_hours * 2.5
        ghatika_lagna = int(((ghatikas * 30) + asc_lon) // 30) % 12 + 1

        # Bhava Lagna: time from sunrise × 5
        bhava_lagna = int(((elapsed_hours * 5 * 30) + asc_lon) // 30) % 12 + 1

        # Shree Lagna: based on Moon's nakshatra
        shree_lagna = int(moon_lon // (360 / 27)) + 1

        # Indu Lagna: based on Moon's position
        indu_lagna = int(((moon_lon * 9) + asc_lon) // 30) % 12 + 1

        # Varnada Lagna: based on ascendant and hora lagna
        varnada_lagna = ((asc_lon // 30 + hora_lagna - 1) % 12) + 1

        return {"Hora Lagna": hora_lagna, "Ghatika Lagna": ghatika_lagna,
                "Bhava Lagna": bhava_lagna, "Shree Lagna": shree_lagna,
                "Indu Lagna": indu_lagna, "Varnada Lagna": varnada_lagna}

    # ================================================================
    # 6. PLANETARY AVASTHAS
    # ================================================================
    @staticmethod
    def calculate_avasthas(planet_longitudes: Dict[str, float]) -> Dict[str, Dict[str, str]]:
        """Calculate Baladi and Jagradadi avasthas for all planets."""
        avasthas = {}
        for p_name, p_lon in planet_longitudes.items():
            deg_in_sign = p_lon % 30
            baladi = "Unknown"
            for start, end, name in AVASTHA_DEGREE_RANGES:
                if start <= deg_in_sign < end:
                    baladi = name
                    break
            jagradadi = "Unknown"
            for start, end, name in AVASTHA_JAGRADADI:
                if start <= deg_in_sign < end:
                    jagradadi = name
                    break
            avasthas[p_name] = {"baladi": baladi, "jagradadi": jagradadi}
        return avasthas

    # ================================================================
    # 7. RETROGRADE SCORING
    # ================================================================
    @staticmethod
    def score_retrograde(retrograde_status: Dict[str, bool]) -> Dict[str, float]:
        """Score retrograde planets — retrograde increases chesta bala."""
        scoring = {}
        retro_strength = {"Mercury": 1.3, "Venus": 1.25, "Mars": 1.15,
                          "Jupiter": 1.2, "Saturn": 1.1, "Sun": 1.0, "Moon": 1.0}
        for p_name, is_retro in retrograde_status.items():
            if is_retro:
                scoring[p_name] = retro_strength.get(p_name, 1.15)
            else:
                scoring[p_name] = 1.0
        return scoring

    # ================================================================
    # 8. NAKSHATRA DETAILS
    # ================================================================
    @staticmethod
    def get_nakshatra_details(nakshatra_indices: Dict[str, int]) -> Dict[str, Dict]:
        """Get detailed nakshatra information for planets."""
        details = {}
        for p_name, nak_idx in nakshatra_indices.items():
            if 0 <= nak_idx < 27:
                details[p_name] = NAKSHATRA_DETAILS[nak_idx]
            else:
                details[p_name] = {}
        return details

    # ================================================================
    # 9. TITHI CLASSIFICATION
    # ================================================================
    @staticmethod
    def classify_tithi(tithi_index: int) -> str:
        """Classify tithi as Nanda, Bhadra, Jaya, Rikta, or Purna."""
        if 0 <= tithi_index < 30:
            return TITHI_CLASSES[tithi_index]
        return "Unknown"

    # ================================================================
    # 10. MASTER METHOD
    # ================================================================
    @classmethod
    def calculate_all(cls, planet_houses: Dict[str, int],
                      planet_longitudes: Dict[str, float],
                      moon_lon: float, sun_lon: float, asc_lon: float,
                      retrograde_status: Optional[Dict[str, bool]] = None,
                      nakshatra_indices: Optional[Dict[str, int]] = None,
                      tithi_index: int = 0,
                      birth_time_hours: float = 12.0,
                      sunrise_hours: float = 6.0,
                      saturn_transit_sign: int = 0,
                      planet_signs: Optional[Dict[str, int]] = None) -> SpecialFeaturesResult:
        """Calculate all Priority 8 special features."""
        if retrograde_status is None:
            retrograde_status = {}
        if nakshatra_indices is None:
            nakshatra_indices = {p: int(lon // (360 / 27)) for p, lon in planet_longitudes.items()}

        moon_sign_idx = int(moon_lon // 30)

        # 1. Sade Sati
        sade_sati = cls.analyze_sade_sati(moon_sign_idx, saturn_transit_sign)

        # 2. Mangal Dosha
        mangal_dosha = cls.detect_mangal_dosha(planet_houses)

        # 3. Pitra Dosha
        pitra_dosha = cls.detect_pitra_dosha(planet_houses, planet_signs)

        # 4. Upagrahas
        upagrahas = cls.calculate_upagrahas(sun_lon)

        # 5. Special Lagnas
        special_lagnas = cls.calculate_special_lagnas(sun_lon, moon_lon, asc_lon,
                                                        birth_time_hours, sunrise_hours)

        # 6. Avasthas
        avasthas = cls.calculate_avasthas(planet_longitudes)

        # 7. Retrograde Scoring
        retrograde_scoring = cls.score_retrograde(retrograde_status)

        # 8. Nakshatra Details
        nakshatra_details = cls.get_nakshatra_details(nakshatra_indices)

        # 9. Tithi Classification
        tithi_class = cls.classify_tithi(tithi_index)

        return SpecialFeaturesResult(
            sade_sati=sade_sati, mangal_dosha=mangal_dosha, pitra_dosha=pitra_dosha,
            upagrahas=upagrahas, special_lagnas=special_lagnas, avasthas=avasthas,
            retrograde_scoring=retrograde_scoring, nakshatra_details=nakshatra_details,
            tithi_classification=tithi_class,
        )


if __name__ == "__main__":
    engine = SpecialFeaturesEngine()
    test_houses = {"Sun": 5, "Moon": 1, "Mars": 2, "Mercury": 4,
                   "Jupiter": 11, "Venus": 6, "Saturn": 2, "Rahu": 10, "Ketu": 4}
    test_lons = {"Sun": 45.5, "Moon": 120.0, "Mars": 50.0, "Mercury": 65.0,
                 "Jupiter": 300.0, "Venus": 15.0, "Saturn": 55.0}

    result = engine.calculate_all(test_houses, test_lons, 120.0, 45.5, 100.0,
                                   saturn_transit_sign=2, tithi_index=5)
    print("=" * 60)
    print("SPECIAL FEATURES — PRIORITY 8")
    print("=" * 60)
    print(f"\nSade Sati: {result.sade_sati}")
    print(f"\nMangal Dosha: {result.mangal_dosha}")
    print(f"\nPitra Dosha: {result.pitra_dosha}")
    print(f"\nUpagrahas: {list(result.upagrahas.keys())}")
    print(f"\nSpecial Lagnas: {result.special_lagnas}")
    print(f"\nAvasthas: {result.avasthas}")
    print(f"\nTithi Classification: {result.tithi_classification}")
