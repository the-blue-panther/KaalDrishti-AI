# Ensures config initializes Lahiri sidereal mode strictly before any imports
import chart_engine.core_config
import swisseph as swe
from datetime import datetime, timezone
import math
import platform
import pytz
from chart_engine.time_converter import TimeConverter
from chart_engine.astronomy_core import AstronomyCore
from chart_engine.coordinate_transformer import CoordinateTransformer, ZODIAC_ORDER
from chart_engine.astrological_derivation import AstrologicalDerivation
from chart_engine.models import PlanetName, ZodiacSign
from chart_engine.chart_state import BirthContext, ChartMetadata, ChartState


def _ephemeris_source(raw_states, swiss_ephemeris) -> str:
    sources = set()
    for state in raw_states.values():
        flags = state.ephemeris_flags
        if flags & swiss_ephemeris.FLG_JPLEPH:
            sources.add("JPL")
        elif flags & swiss_ephemeris.FLG_SWIEPH:
            sources.add("Swiss Ephemeris")
        elif flags & swiss_ephemeris.FLG_MOSEPH:
            sources.add("Moshier")
        else:
            sources.add("unknown")
    if "unknown" in sources:
        return "mixed_or_unknown"
    if sources == {"Moshier", "Swiss Ephemeris"}:
        return "Moshier planets + Swiss Ephemeris mean node"
    return " + ".join(sorted(sources))

class AstroEngine:
    """
    The monolithic interface for Phase 5.
    Assembles Time, Astronomy, Coordinates, and Derivations into a master dictionary object.
    """
    def generate_chart(
        self,
        local_time: str,
        tz: str,
        lat: float,
        lon: float,
        *,
        julian_day_override: float | None = None,
        reference_time_utc: datetime | None = None,
    ) -> ChartState:
        # One reference instant anchors every time-dependent calculation in this chart.
        calculated_at_utc = datetime.now(timezone.utc)
        if not math.isfinite(float(lat)) or not -90.0 <= float(lat) <= 90.0:
            raise ValueError("latitude must be finite and in [-90, 90]")
        if not math.isfinite(float(lon)) or not -180.0 <= float(lon) <= 180.0:
            raise ValueError("longitude must be finite and in [-180, 180]")
        if reference_time_utc is None:
            reference_time_utc = calculated_at_utc
        elif reference_time_utc.tzinfo is None:
            raise ValueError("reference_time_utc must be timezone-aware")
        else:
            reference_time_utc = reference_time_utc.astimezone(timezone.utc)

        # 1. Time Layer
        # Research exports may provide an authoritative UT Julian day but no
        # IANA timezone for historical local civil time. In that case accept
        # the supplied canonical instant while retaining the source timestamp
        # in BirthContext for provenance.
        jd_ut = float(julian_day_override) if julian_day_override is not None else TimeConverter.local_to_jd(local_time, tz)
        if not math.isfinite(jd_ut):
            raise ValueError("Julian Day must be finite")

        # 2. Astronomy Layer (Immutable mathematical cache)
        raw_states = AstronomyCore.calculate_raw_state(jd_ut)

        # 3. Coordinate Layer
        astrological_positions = CoordinateTransformer.transform_to_astrological(raw_states)

        # 4. Derivation Layer (Houses & Vargas)
        ascendant_sign, ascendant_lon = AstrologicalDerivation.calculate_houses(jd_ut, lat, lon, astrological_positions, ZODIAC_ORDER)

        # Group Divisional Charts structurally by Varga name rather than Planet to ensure correct UI parsing
        vargas = {}
        # Pre-populate Ascendants for all D-Charts
        asc_vargas = AstrologicalDerivation.calculate_vargas(ascendant_lon, ZODIAC_ORDER)
        for v_name, v_sign in asc_vargas.items():
            if v_name not in vargas: vargas[v_name] = {}
            vargas[v_name]["Ascendant"] = v_sign

        for name, state in raw_states.items():
            planet_vargas = AstrologicalDerivation.calculate_vargas(state.longitude_ecliptic, ZODIAC_ORDER)
            for v_name, sign_val in planet_vargas.items():
                if v_name not in vargas:
                    vargas[v_name] = {}
                vargas[v_name][name.value] = sign_val

        # Assure the fundamental D1 Rashi grid is natively incorporated into the Varga container
        d1_matrix = {}
        for name, pos in astrological_positions.items():
            d1_matrix[name.value] = pos.sign.value if hasattr(pos.sign, "value") else str(pos.sign)
        d1_matrix["Ascendant"] = ascendant_sign.value
        vargas["D1_Main"] = d1_matrix

        # 5. Panchang Layer (Tithi, Paksha, Nakshatra, Vaar)
        panchang = AstrologicalDerivation.calculate_panchang(
            jd_ut,
            raw_states[PlanetName.SUN].longitude_ecliptic,
            raw_states[PlanetName.MOON].longitude_ecliptic,
            lat, lon
        )

        # Phase 5: Chronological Dasha Calculation
        from chart_engine.vimshottari_dasha import VimshottariDasha
        from chart_engine.yogini_dasha import YoginiDasha
        from chart_engine.ashtottari_dasha import AshtottariDasha
        # All planetary positions are calculated for jd_ut. Anchor every dasha
        # timeline to that same absolute instant (UTC), including when the caller
        # supplied an authoritative Julian Day override.
        b_dt = TimeConverter.julian_day_to_utc_datetime(jd_ut)
        birth_local_dt = TimeConverter.julian_day_to_local_datetime(jd_ut, tz)
        reference_local_dt = TimeConverter.utc_to_local_datetime(reference_time_utc, tz)
        vimshottari_timeline = VimshottariDasha.calculate_full_tree(raw_states[PlanetName.MOON].longitude_ecliptic, b_dt)
        yogini_timeline = YoginiDasha.calculate_dashas(raw_states[PlanetName.MOON].longitude_ecliptic, b_dt)
        ashtottari_timeline = AshtottariDasha.calculate_dashas(raw_states[PlanetName.MOON].longitude_ecliptic, b_dt)

        dasha_timeline = {
            "Vimshottari": vimshottari_timeline,
            "Yogini": yogini_timeline,
            "Ashtottari": ashtottari_timeline
        }

        # Phase 5b: Priority 2 — Additional Dasha Systems
        from chart_engine.jaimini_chara_dasha import JaiminiCharaDasha
        from chart_engine.kalachakra_dasha import KalachakraDasha
        from chart_engine.additional_dashas import AdditionalDashaSystems, DashaSandhiAnalyzer

        optional_dasha_status = {}

        # Extract planet sign indices for sign-based dashas
        planet_signs = {}
        for name, pos in astrological_positions.items():
            sign_str = pos.sign.value if hasattr(pos.sign, "value") else str(pos.sign)
            from chart_engine.models import ZodiacSign as ZS
            try:
                sign_idx = list(ZS).index(ZS(sign_str))
            except (ValueError, IndexError):
                sign_idx = 0
            planet_signs[name.value] = sign_idx

        asc_sign_idx = list(ZodiacSign).index(ZodiacSign(ascendant_sign.value)) if hasattr(ascendant_sign, "value") else 0
        moon_lon = raw_states[PlanetName.MOON].longitude_ecliptic

        # Jaimini Chara Dasha
        try:
            chara_timeline = JaiminiCharaDasha.calculate_chara_dasha(b_dt, planet_signs, asc_sign_idx)
            dasha_timeline["Jaimini_Chara"] = [p.to_dict() for p in chara_timeline]
            optional_dasha_status["jaimini_dasha"] = "calculated; experimental; sequence/reference validation pending"
        except Exception as exc:
            dasha_timeline["Jaimini_Chara"] = []
            optional_dasha_status["jaimini_dasha"] = f"calculation_failed:{type(exc).__name__}"

        # Kalachakra Dasha
        try:
            kalachakra_timeline = KalachakraDasha.calculate(moon_lon, b_dt)
            dasha_timeline["Kalachakra"] = [p.to_dict() for p in kalachakra_timeline]
            optional_dasha_status["kalachakra_dasha"] = "calculated; experimental; external validation pending"
        except Exception as exc:
            dasha_timeline["Kalachakra"] = []
            optional_dasha_status["kalachakra_dasha"] = f"calculation_failed:{type(exc).__name__}"

        # All Additional Dasha Systems (8 systems)
        try:
            additional = AdditionalDashaSystems.calculate_all(b_dt, moon_lon, asc_sign_idx, planet_signs)
            for sys_name, periods in additional.items():
                dasha_timeline[sys_name] = [p.to_dict() for p in periods]
            optional_dasha_status["additional_dashas"] = "calculated; experimental; external validation pending"
        except Exception as exc:
            optional_dasha_status["additional_dashas"] = f"calculation_failed:{type(exc).__name__}"

        # Dasha Sandhi Analysis
        try:
            sandhi_result = DashaSandhiAnalyzer.analyze(dasha_timeline, b_dt, reference_time_utc.replace(tzinfo=None))
            dasha_timeline["dasha_sandhi"] = sandhi_result.to_dict()
            optional_dasha_status["dasha_sandhi"] = "calculated"
        except Exception as exc:
            dasha_timeline["dasha_sandhi"] = {"sandhi_periods": [], "critical_periods": []}
            optional_dasha_status["dasha_sandhi"] = f"calculation_failed:{type(exc).__name__}"

        # Phase 6: Transit Overlays
        from chart_engine.transits import TransitEngine
        transit_snapshot = TransitEngine.get_current_transit_snapshot(reference_time_utc)
        current_transits = transit_snapshot["signs"]
        transit_longitudes = transit_snapshot["longitudes"]
        natal_ascendant_index = ZODIAC_ORDER.index(ascendant_sign)
        current_transit_houses = {
            planet: (ZODIAC_ORDER.index(ZodiacSign(sign)) - natal_ascendant_index) % 12 + 1
            for planet, sign in current_transits.items()
        }

        # Phase 7: Uncertainty Quantification (Monte Carlo +/- 5 mins)
        # We test if the D1 or D9 Ascendant changes with a 5 minute drift
        jd_minus_5 = jd_ut - (5.0 / 1440.0)
        jd_plus_5 = jd_ut + (5.0 / 1440.0)

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        aya_minus = swe.get_ayanamsa_ut(jd_minus_5)
        ascmc_minus = swe.houses(jd_minus_5, lat, lon, b'P')[1]
        asc_lon_minus = (ascmc_minus[0] - aya_minus) % 360.0
        asc_sign_minus = ZODIAC_ORDER[int(asc_lon_minus // 30)]
        d9_minus = AstrologicalDerivation.calculate_vargas(asc_lon_minus, ZODIAC_ORDER).get("D9_Navamsha", "")

        aya_plus = swe.get_ayanamsa_ut(jd_plus_5)
        ascmc_plus = swe.houses(jd_plus_5, lat, lon, b'P')[1]
        asc_lon_plus = (ascmc_plus[0] - aya_plus) % 360.0
        asc_sign_plus = ZODIAC_ORDER[int(asc_lon_plus // 30)]
        d9_plus = AstrologicalDerivation.calculate_vargas(asc_lon_plus, ZODIAC_ORDER).get("D9_Navamsha", "")

        d1_stable = (asc_sign_minus == ascendant_sign) and (asc_sign_plus == ascendant_sign)
        d9_stable = (d9_minus == vargas.get("D9_Navamsha", {}).get("Ascendant")) and (d9_plus == vargas.get("D9_Navamsha", {}).get("Ascendant"))

        uncertainty_score = 0.0
        if not d1_stable: uncertainty_score += 0.6
        if not d9_stable: uncertainty_score += 0.4

        # Phase 8: Shadbala (6-fold Planetary Strength) — NEW
        from chart_engine.shadbala import ShadbalaEngine
        planet_lons = {name.value: pos.longitude_ecliptic for name, pos in raw_states.items()}
        planet_speeds = {name.value: state.speed for name, state in raw_states.items()}
        retro_status = {name.value: pos.is_retrograde for name, pos in astrological_positions.items()}
        shadbala_results = ShadbalaEngine.calculate_all(
            planet_longitudes=planet_lons,
            ascendant_lon=ascendant_lon,
            vargas=vargas,
            planet_speeds=planet_speeds,
            retrograde_status=retro_status
        )
        shadbala_summary = ShadbalaEngine.get_strength_summary(shadbala_results)
        shadbala_data = {k: v.to_dict() for k, v in shadbala_results.items()}

        # Phase 9: Ashtakavarga (8-fold Point System) — NEW
        from chart_engine.ashtakavarga import AshtakavargaEngine
        # Ashtakavarga's fixed lordship pairs are zodiac-sign coordinates, not
        # natal houses. Keep the traditional 1..12 indexing (Aries..Pisces).
        planet_signs_for_av = {
            name.value: int(pos.longitude_ecliptic // 30.0) + 1
            for name, pos in astrological_positions.items()
        }
        ashtakavarga_result = AshtakavargaEngine.calculate(
            planet_positions={k: {"sign": v} for k, v in planet_signs_for_av.items()},
            ascendant_house=int(ascendant_lon // 30.0) + 1
        )

        # Phase 10: Graha Drishti (Planetary Aspects) — NEW
        from chart_engine.graha_drishti import GrahaDrishtiEngine
        planet_houses_for_av = {name.value: pos.house_number for name, pos in astrological_positions.items()}
        aspect_result = GrahaDrishtiEngine.calculate_aspect_matrix(planet_houses_for_av)
        drik_bala_from_aspects = GrahaDrishtiEngine.get_drik_bala_contribution(planet_houses_for_av)

        # Phase 11: Combustion + Planetary War — NEW
        from chart_engine.combustion import CombustionEngine
        planet_lats = {name.value: state.latitude for name, state in raw_states.items()}
        combustion_result = CombustionEngine.full_analysis(
            planet_lons, retro_status, planet_latitudes=planet_lats
        )

        # Phase 12: Jaimini System (Chara Karaka, Arudha, Rashi Drishti, Argala) — NEW
        from chart_engine.jaimini_system import JaiminiSystem
        sign_lords_map = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        house_lords_for_jaimini = {}
        for h_num in range(1, 13):
            sign_name = ZODIAC_ORDER[(asc_sign_idx + h_num - 1) % 12].value
            house_lords_for_jaimini[h_num] = sign_lords_map.get(sign_name, "Unknown")
        jaimini_result = JaiminiSystem.calculate_all(
            planet_lons, planet_houses_for_av, asc_sign_idx, house_lords_for_jaimini
        )

        # Phase 13: KP System (Sub-Lords, Cuspal Sub-Lords, Ruling Planets, Significators) — NEW
        from chart_engine.kp_system import KPSystem
        kp_result = KPSystem.calculate_all(
            planet_lons, planet_houses_for_av, ascendant_lon,
            query_datetime=reference_local_dt,
            day_of_week=reference_local_dt.weekday(),
            year=reference_local_dt.year,
        )

        # Phase 14: Vargottama Detection (D1 sign = D9 sign) — NEW
        vargottama_result = AstrologicalDerivation.detect_vargottama(vargas)

        # Phase 15: Special Features (Sade Sati, Mangal Dosha, Upagrahas, Avasthas, etc.) — NEW
        from chart_engine.special_features import SpecialFeaturesEngine
        moon_lon = raw_states[PlanetName.MOON].longitude_ecliptic
        sun_lon = raw_states[PlanetName.SUN].longitude_ecliptic
        saturn_transit_sign_idx = current_transits.get("Saturn", "Aries")
        try:
            saturn_sign_idx = ZODIAC_ORDER.index(ZodiacSign(saturn_transit_sign_idx))
        except (ValueError, IndexError):
            saturn_sign_idx = 0
        nakshatra_indices = {name.value: pos.nakshatra_index for name, pos in astrological_positions.items()}
        tithi_index = panchang.get("tithi_index", 0)
        special_features_result = SpecialFeaturesEngine.calculate_all(
            planet_houses_for_av, planet_lons, moon_lon, sun_lon, ascendant_lon,
            retrograde_status=retro_status, nakshatra_indices=nakshatra_indices,
            tithi_index=tithi_index, saturn_transit_sign=saturn_sign_idx,
            planet_signs={name.value: int(raw_states[name].longitude_ecliptic // 30) for name in [PlanetName.SUN, PlanetName.MOON, PlanetName.MARS, PlanetName.MERCURY, PlanetName.JUPITER, PlanetName.VENUS, PlanetName.SATURN]}
        )
        # Phase 16: Predictive & Technical Features (Varshaphala, Muhurta, Medical, Remedies, Ayanamsa) — NEW
        from chart_engine.predictive_tech import PredictiveTechEngine
        predictive_tech_result = PredictiveTechEngine.calculate_all(
            planet_lons, planet_houses_for_av, birth_local_dt, ascendant_lon,
            tithi_index=tithi_index, nak_index=nakshatra_indices.get("Moon", 0),
            vaar_index=birth_local_dt.weekday(), current_year=reference_local_dt.year,
        )

        # Phase 17: Navatara Chakra (Nine-Star Compatibility Wheel) — NEW
        from chart_engine.navatara import NavataraChakra
        navatara_result = NavataraChakra.calculate(
            moon_lon=raw_states[PlanetName.MOON].longitude_ecliptic,
            planet_lons=planet_lons,
            ascendant_lon=ascendant_lon,
            transit_lons=transit_longitudes if transit_longitudes else None,
        )

        # 5. Materialize the single canonical backend state.
        # All downstream layers should consume this state or an explicit projection.
        return ChartState(
            birth=BirthContext(
                local_time=local_time,
                timezone=tz,
                latitude=lat,
                longitude=lon,
            ),
            metadata=ChartMetadata(
                calculated_at_utc=calculated_at_utc,
                reference_time_utc=reference_time_utc,
                julian_day=jd_ut,
                sidereal_mode="Lahiri",
                ephemeris_source=_ephemeris_source(raw_states, swe),
                ephemeris_version=str(swe.version),
                timezone_data_version=pytz.__version__,
                python_version=platform.python_version(),
                component_status={
                    "sidereal_positions": "partial_reference_verified:Delhi_Sydney_Toronto_Nairobi_cross_engine_plus_one_JPL_Mars_vector; same_Swiss_family_for_chart_fixtures",
                    "whole_sign_houses": "partial_reference_verified:three_multi_region_cross_engine_fixtures; boundary_cases_pending",
                    "divisional_charts": "partial_reference_verified:14_of_19_supported_vargas_on_Delhi_plus_D3_D9_D30_D60_in_three_historical_zone_charts; D2_convention_differs; D5_D6_D8_D11_pending",
                    "panchang": "partial_reference_verified:historical_Delhi_limb_labels_and_transition_windows; sunrise_vaar_and_karana_boundaries; multi_source_convention_matrix_pending",
                    "vimshottari": "partial_reference_verified:9_MD_81_AD_729_PD_internal_tiling_duration_and_replay_checks; one_MD_reference_with_60min_ceiling; independent_AD_PD_vectors_pending; year=365.2425d",
                    "yogini_dasha": "experimental; external validation pending",
                    "ashtottari_dasha": "approximate; exclude from reliability scoring",
                    **optional_dasha_status,
                    "ashtakavarga_bhinna_sarva": "experimental; sign_indexed; 337_checksum_only; cell_tables_unreconciled; excluded_from_reliability_and_ML",
                    "ashtakavarga_shodhana": "experimental; zero_and_planet_occupancy_rules_missing; excluded_from_reliability_and_ML",
                    "shadbala": "approximate; several components use defaults/simplifications",
                    "kp_system": "approximate; KP ayanamsa/cusps not reference-verified",
                    "graha_drishti_strength": "heuristic interpolation; school-specific",
                    "combustion_and_planetary_war": "threshold_and_latitude_wiring_tested; combustion thresholds school-specific; severity_penalty heuristic",
                    "special_predictive_features": "heuristic; not outcome-validated",
                    "transits": "historically_replayable; sidereal_longitudes_and_natal_whole_sign_houses_exposed; ingress_timing_available; astrological_effect_rules_not_validated",
                    "uncertainty_score": "5-minute ascendant sensitivity only; not a probability",
                },
                ayanamsa=swe.get_ayanamsa_ut(jd_ut),
                house_system="Whole Sign",
                ascendant=ascendant_sign,
                ascendant_longitude=ascendant_lon,
                uncertainty_score=uncertainty_score,
                d1_stable_5min=d1_stable,
                d9_stable_5min=d9_stable,
            ),
            raw_astronomical_state=raw_states,
            planetary_positions=astrological_positions,
            divisional_charts=vargas,
            dasha_timeline=dasha_timeline,
            panchang=panchang,
            current_transits=current_transits,
            current_transit_longitudes=transit_longitudes,
            current_transit_latitudes=transit_snapshot["latitudes"],
            current_transit_speeds=transit_snapshot["speeds"],
            current_transit_ephemeris_flags=transit_snapshot["ephemeris_flags"],
            current_transit_houses=current_transit_houses,
            shadbala=shadbala_data,
            shadbala_summary=shadbala_summary,
            ashtakavarga=ashtakavarga_result.to_dict(),
            graha_drishti=aspect_result.to_dict(),
            combustion=combustion_result.to_dict(),
            jaimini_system=jaimini_result.to_dict(),
            kp_system=kp_result.to_dict(),
            vargottama=vargottama_result,
            special_features=special_features_result.to_dict(),
            predictive_tech=predictive_tech_result.to_dict(),
            navatara_chakra=navatara_result,
        )

if __name__ == "__main__":
    engine = AstroEngine()
    print("Testing Central Chart Engine Initialization...")

    # Test data: Dec 1, 1990, 10:30 AM, Longitude/Latitude for London (51.5, -0.1)
    chart = engine.generate_chart("1990-12-01 10:30:00", "Europe/London", 51.5072, -0.1276)

    import json
    # print(json.dumps(chart, indent=2))

    print("\nRunning Phase 6: Semantic Feature Extraction...")
    from feature_extraction.extractor import FeatureExtractor
    features = FeatureExtractor.generate_features(chart)
    print(features.model_dump_json(indent=2))

    print("\nRunning Phase 7: Quantitative Scoring & Divisional Validation...")
    from intelligence_layer.ase import AstrologicalScoringEngine
    from intelligence_layer.dis import DivisionalIntelligenceSystem

    base_career = AstrologicalScoringEngine.score_career(features)
    final_output = DivisionalIntelligenceSystem.validate_career_d10(features, base_career, chart)

    print(json.dumps(final_output, indent=2))

    print("\nRunning Phase 8: Neo4j RAG Context Compiler...")
    from rag_bridge.graph_query_builder import RAGCompiler
    compiler = RAGCompiler()
    context_payload = compiler.fetch_all_context(features.model_dump())

    # We display a summarized version to prove it executed correctly.
    print(f"Successfully retrieved {len(context_payload['house_effects'])} Planet-House semantic paragraphs from Neo4j.")
    print(f"Dasha Evolution Layer Retrieved: {len(context_payload['dasha_effects'])} characters.")
    print(f"Master Prompt Frameworks Fetched: {len(context_payload['system_prompts'])}")

    # Show partial preview of the Sun's retrieved text dynamically mapped to its house placement.
    sun_text = context_payload['house_effects'].get('Sun', 'Not Found')
    print(f"\nExample Neo4j Yield (Sun): {sun_text[:150]}...")

    print("\nRunning Phase 9: AI Agent Master Prompt Compilation...")
    from agent_inference.core import AstroAgentCore
    agent = AstroAgentCore()

    dummy_query = "What is the primary psychological driver of my career based on my deterministic math and Neo4j context?"
    final_prompt = agent.generate_response(
        user_query=dummy_query,
        chart=chart,
        features=features.model_dump(),
        quantitative_scores=final_output,
        neo4j_context=context_payload,
    )

    print("\n--- FINAL LLM PAYLOAD PREVIEW ---")
    print(final_prompt[:1200] + "\n...[PAYLOAD TRUNCATED FOR TERMINAL DISPLAY]...")
