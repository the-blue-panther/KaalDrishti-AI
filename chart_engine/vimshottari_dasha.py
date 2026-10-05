from datetime import datetime, timedelta, timezone
import math

DAYS_IN_DASHA_YEAR = 365.2425

# Lord sequence and nominal Vimshottari durations in years (total = 120).
# This implementation uses a fixed 365.2425-day year for date conversion.
# Other calculators use 365.25 days or calendar years, so boundary dates differ.
DASHA_LORDS = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19),
    ("Mercury", 17)
]


def _utc_naive(value: datetime) -> datetime:
    """Normalize timeline instants to naive UTC for legacy ISO serialization."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _exact_iso(value: datetime) -> str:
    """Serialize every calculated boundary without truncating sub-second time."""
    return value.isoformat()

class VimshottariDasha:
    @staticmethod
    def calculate_mahadashas(moon_longitude_sidereal: float, birth_datetime: datetime) -> list[dict]:
        """
        Derives the 120-year chronological Vimshottari timeline strictly from the sidereal
        Ecliptic Nakshatra bounds and fractional birth balances.
        """
        if not 0.0 <= moon_longitude_sidereal < 360.0:
            raise ValueError("moon_longitude_sidereal must be in [0, 360)")
        if not isinstance(birth_datetime, datetime):
            raise TypeError("birth_datetime must be a datetime")
        birth_datetime = _utc_naive(birth_datetime)

        # Exact length of one Nakshatra
        NAKSHATRA_SPAN = 360.0 / 27.0

        # Work in scaled nakshatra coordinates to avoid a float-rounding
        # misclassification at exact boundaries (e.g. 24 * (360 / 27)).
        nakshatra_coordinate = moon_longitude_sidereal * 27.0 / 360.0
        nearest_boundary = round(nakshatra_coordinate)
        if math.isclose(nakshatra_coordinate, nearest_boundary, rel_tol=0.0, abs_tol=1e-12):
            nakshatra_coordinate = float(nearest_boundary)

        # 1. Determine which Nakshatra the Moon is in; intervals are [start, end).
        nakshatra_index = int(nakshatra_coordinate)

        # 2. Determine the ruling lord for this Nakshatra
        # The 27 Nakshatras are divided into 3 cycles of 9 lords
        lord_index = nakshatra_index % 9
        birth_lord, lord_years = DASHA_LORDS[lord_index]

        # 3. Calculate fraction of Nakshatra REMAINING
        degrees_elapsed_in_nakshatra = (nakshatra_coordinate - nakshatra_index) * NAKSHATRA_SPAN
        fraction_remaining = (NAKSHATRA_SPAN - degrees_elapsed_in_nakshatra) / NAKSHATRA_SPAN

        # 4. Convert fraction to fractional years of balance
        balance_years = fraction_remaining * lord_years

        timeline = []
        current_date = birth_datetime

        # The very first Dasha
        first_dasha_end = current_date + timedelta(days=balance_years * DAYS_IN_DASHA_YEAR)
        first_dasha_theoretical_start = first_dasha_end - timedelta(days=lord_years * DAYS_IN_DASHA_YEAR)

        timeline.append({
            "lord": birth_lord,
            "start": first_dasha_theoretical_start.strftime("%d-%b, %Y"),
            "end": first_dasha_end.strftime("%d-%b, %Y"),
            "start_exact": _exact_iso(first_dasha_theoretical_start),
            "end_exact": _exact_iso(first_dasha_end),
            "is_birth_dasha": True,
            "balance_years": balance_years
        })

        current_date = first_dasha_end

        # Cascade through the remaining 8 lords to complete the 120-year cycle
        for i in range(1, 9):
            next_lord_idx = (lord_index + i) % 9
            lord_name, duration = DASHA_LORDS[next_lord_idx]

            end_date = current_date + timedelta(days=duration * DAYS_IN_DASHA_YEAR)

            timeline.append({
                "lord": lord_name,
                "start": current_date.strftime("%d-%b, %Y"),
                "end": end_date.strftime("%d-%b, %Y"),
                "start_exact": _exact_iso(current_date),
                "end_exact": _exact_iso(end_date),
                "is_birth_dasha": False,
                "balance_years": 0.0
            })

            current_date = end_date

        return timeline

    @staticmethod
    def calculate_antardashas(maha_lord: str, start_date: datetime) -> list[dict]:
        """
        Calculates the 9 Antardashas (sub-periods) for a given Mahadasha.
        """
        start_date = _utc_naive(start_date)
        start_idx = next((i for i, (name, _) in enumerate(DASHA_LORDS) if name == maha_lord), None)
        if start_idx is None:
            raise ValueError(f"Unknown Vimshottari lord: {maha_lord}")
        maha_years = DASHA_LORDS[start_idx][1]

        antardashas = []
        current_date = start_date
        for i in range(9):
            idx = (start_idx + i) % 9
            antar_lord, antar_years = DASHA_LORDS[idx]

            # Sub-period duration in years = (Maha * Antar) / 120
            duration_years = (maha_years * antar_years) / 120.0
            end_date = current_date + timedelta(days=duration_years * DAYS_IN_DASHA_YEAR)

            antardashas.append({
                "lord": antar_lord,
                "start": current_date.strftime("%d-%b, %Y"),
                "end": end_date.strftime("%d-%b, %Y"),
                "start_exact": _exact_iso(current_date),
                "end_exact": _exact_iso(end_date)
            })
            current_date = end_date
        return antardashas

    @staticmethod
    def calculate_pratyantardashas(antar_lord: str, start_date: datetime, antar_duration_years: float) -> list[dict]:
        """
        Calculates the 9 Pratyantardashas (sub-sub-periods) for a given Antardasha.
        The duration scales exactly proportional to the sub-lord's standard weight out of 120.
        """
        start_date = _utc_naive(start_date)
        if not math.isfinite(antar_duration_years) or antar_duration_years < 0:
            raise ValueError("antar_duration_years must be finite and non-negative")
        start_idx = next((i for i, (name, _) in enumerate(DASHA_LORDS) if name == antar_lord), None)
        if start_idx is None:
            raise ValueError(f"Unknown Vimshottari lord: {antar_lord}")

        pratyantardashas = []
        current_date = start_date
        for i in range(9):
            idx = (start_idx + i) % 9
            prat_lord, prat_years_base = DASHA_LORDS[idx]

            # Sub-Sub-period duration = Antar Duration * (Pratyantar Lord Years / 120)
            duration_years = antar_duration_years * (prat_years_base / 120.0)
            end_date = current_date + timedelta(days=duration_years * DAYS_IN_DASHA_YEAR)

            pratyantardashas.append({
                "lord": prat_lord,
                "start": current_date.strftime("%d-%b, %Y"),
                "end": end_date.strftime("%d-%b, %Y"),
                "start_exact": _exact_iso(current_date),
                "end_exact": _exact_iso(end_date)
            })
            current_date = end_date
        return pratyantardashas

    @staticmethod
    def calculate_full_tree(moon_longitude_sidereal: float, birth_datetime: datetime) -> list[dict]:
        """
        Calculates the complete recursive 3-tier Vimshottari Tree (Maha -> Antar -> Pratyantar).
        Returns a rich nested dictionary array for the frontend visual renderer.
        """
        maha_timeline = VimshottariDasha.calculate_mahadashas(moon_longitude_sidereal, birth_datetime)

        full_tree = []
        for maha in maha_timeline:
            maha_node = dict(maha)

            try:
                m_start = datetime.fromisoformat(
                    maha_node.get("start_exact", maha_node["start"])
                ) if "start_exact" in maha_node else datetime.strptime(
                    maha_node["start"], "%d-%b, %Y"
                )
            except (TypeError, ValueError):
                full_tree.append(maha_node)
                continue

            antardashas = VimshottariDasha.calculate_antardashas(maha_node["lord"], m_start)
            antar_nodes = []

            for antar in antardashas:
                antar_node = dict(antar)
                a_start = datetime.fromisoformat(
                    antar_node.get("start_exact", antar_node["start"])
                ) if "start_exact" in antar_node else datetime.strptime(
                    antar_node["start"], "%d-%b, %Y"
                )
                a_end = datetime.fromisoformat(
                    antar_node.get("end_exact", antar_node["end"])
                ) if "end_exact" in antar_node else datetime.strptime(
                    antar_node["end"], "%d-%b, %Y"
                )

                a_dur = (a_end - a_start).total_seconds() / 86400.0 / DAYS_IN_DASHA_YEAR
                pratyantars = VimshottariDasha.calculate_pratyantardashas(antar_node["lord"], a_start, a_dur)

                antar_node["pratyantardashas"] = pratyantars
                antar_nodes.append(antar_node)

            maha_node["antardashas"] = antar_nodes
            full_tree.append(maha_node)

        return full_tree

    @staticmethod
    def get_current_dasha(timeline: list[dict], target_date: datetime) -> dict:
        """
        Identifies the active Mahadasha and Antardasha sequence.
        """
        target_date = _utc_naive(target_date)
        for d in timeline:
            start_dt = datetime.fromisoformat(d["start_exact"]) if "start_exact" in d else datetime.strptime(d["start"], "%d-%b, %Y")
            end_dt = datetime.fromisoformat(d["end_exact"]) if "end_exact" in d else datetime.strptime(d["end"], "%d-%b, %Y")
            start_dt, end_dt = _utc_naive(start_dt), _utc_naive(end_dt)
            maha_active = start_dt <= target_date < end_dt
            if maha_active:
                antardashas = VimshottariDasha.calculate_antardashas(d["lord"], start_dt)
                active_antar = "Unknown"
                active_pratyantar = "Unknown"
                pratyantar_end = "Unknown"
                pratyantar_end_exact = "Unknown"

                for a in antardashas:
                    a_start = datetime.fromisoformat(a["start_exact"]) if "start_exact" in a else datetime.strptime(a["start"], "%d-%b, %Y")
                    a_end = datetime.fromisoformat(a["end_exact"]) if "end_exact" in a else datetime.strptime(a["end"], "%d-%b, %Y")
                    a_start, a_end = _utc_naive(a_start), _utc_naive(a_end)
                    antar_active = a_start <= target_date < a_end
                    if antar_active:
                        active_antar = a["lord"]

                        # Calculate Pratyantardasha
                        a_dur_years = (a_end - a_start).total_seconds() / 86400.0 / DAYS_IN_DASHA_YEAR
                        pratyantardashas = VimshottariDasha.calculate_pratyantardashas(active_antar, a_start, a_dur_years)

                        for p in pratyantardashas:
                            p_start = datetime.fromisoformat(p["start_exact"]) if "start_exact" in p else datetime.strptime(p["start"], "%d-%b, %Y")
                            p_end = datetime.fromisoformat(p["end_exact"]) if "end_exact" in p else datetime.strptime(p["end"], "%d-%b, %Y")
                            p_start, p_end = _utc_naive(p_start), _utc_naive(p_end)
                            prat_active = p_start <= target_date < p_end
                            if prat_active:
                                active_pratyantar = p["lord"]
                                pratyantar_end = p["end"]
                                pratyantar_end_exact = p["end_exact"]
                                break
                        break

                return {
                    "mahadasha": d["lord"],
                    "antardasha": active_antar,
                    "pratyantardasha": active_pratyantar,
                    "mahadasha_end": d["end"],
                    "mahadasha_end_exact": d.get("end_exact", d["end"]),
                    "pratyantardasha_end": pratyantar_end,
                    "pratyantardasha_end_exact": pratyantar_end_exact,
                }
        return {"mahadasha": "Unknown", "antardasha": "Unknown", "pratyantardasha": "Unknown",
                "mahadasha_end": "Unknown", "mahadasha_end_exact": "Unknown",
                "pratyantardasha_end": "Unknown", "pratyantardasha_end_exact": "Unknown"}
    @staticmethod
    def get_dasha_horizon(timeline: list[dict], target_date: datetime, horizon_years: int = 25) -> list[dict]:
        """
        Extends the 'current dasha' logic to return a flattened sequence
        of Mahadashas and their Antardashas covering the specified horizon.
        """
        target_date = _utc_naive(target_date)
        if not math.isfinite(horizon_years) or horizon_years < 0:
            raise ValueError("horizon_years must be finite and non-negative")
        horizon_end = target_date + timedelta(days=horizon_years * DAYS_IN_DASHA_YEAR)
        sequence = []

        for d in timeline:
            m_start = datetime.fromisoformat(d["start_exact"]) if "start_exact" in d else datetime.strptime(d["start"], "%d-%b, %Y")
            m_end = datetime.fromisoformat(d["end_exact"]) if "end_exact" in d else datetime.strptime(d["end"], "%d-%b, %Y")
            m_start, m_end = _utc_naive(m_start), _utc_naive(m_end)

            # If the Mahadasha overlaps with our horizon window
            maha_overlaps = (m_start <= target_date < m_end) if horizon_years == 0 else (m_start < horizon_end and m_end > target_date)
            if maha_overlaps:
                antardashas = VimshottariDasha.calculate_antardashas(d["lord"], m_start)

                for a in antardashas:
                    a_start = datetime.fromisoformat(a["start_exact"]) if "start_exact" in a else datetime.strptime(a["start"], "%d-%b, %Y")
                    a_end = datetime.fromisoformat(a["end_exact"]) if "end_exact" in a else datetime.strptime(a["end"], "%d-%b, %Y")
                    a_start, a_end = _utc_naive(a_start), _utc_naive(a_end)

                    # If the Antardasha overlaps with our specific window
                    antar_overlaps = (a_start <= target_date < a_end) if horizon_years == 0 else (a_start < horizon_end and a_end > target_date)
                    if antar_overlaps:
                        sequence.append({
                            "mahadasha": d["lord"],
                            "antardasha": a["lord"],
                            "start": a["start"],
                            "end": a["end"],
                            "start_exact": a.get("start_exact", a["start"]),
                            "end_exact": a.get("end_exact", a["end"]),
                        })
        return sequence
