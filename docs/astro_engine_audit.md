# Astro Agent architecture and numerical engine audit

Updated 2026-10-01. This records software and reference-vector agreement. It does not validate astrology as a scientific theory or establish outcome prediction.

## Repository and data architecture

| Layer | Current modules | Role |
|---|---|---|
| Application | `main.py`, `agent_inference/`, `frontend/`, `users/` | API, UI, persistence |
| Astronomy and chart | `chart_engine/` | PySwissEph, time/JD conversion, D1/vargas, dasha, transit and derived factors |
| Features | `feature_extraction/` | ChartState projections |
| Historical ingestion | `ml/acquisition.py`, `ml/multisource.py`, `ml/data_sources/base.py` | Immutable raw fetches, source parsing, conservative entity resolution, adapter contract |
| Historical pipeline | `ml/event_dates.py`, `ml/data_quality.py`, `ml/candidate_artifacts.py`, `ml/outcome_joiner.py`, `ml/relationship_pipeline.py` | Canonical intervals, reports, immutable candidate freeze, separate outcomes and relationship vertical slice |
| Existing domain/evaluation | `ml/marriage_windows.py`, `ml/prediction_cases.py`, `ml/*marriage*` | Current deterministic relationship candidate rules and legacy experiments |
| Tests/reference data | `tests/`, `tests/fixtures/` | Astronomy vectors, dasha and transit references, date/pipeline contracts |

Raw VedAstro birth and relationship files are staged independently, canonicalized into person and event JSONL, chart inputs are projected from birth data alone, candidates are frozen and hashed, then the outcome join writes separate PredictionCase and event-nearest artifacts. Full source counts and the bounded chart slice are reported in `docs/relationship_vertical_slice_report.md`.

## Numerical audit status by component

| Component | Status | Evidence / known limits |
|---|---|---|
| Birth local time → UTC | Partially verified | UTC/JD round trips preserve seconds; ambiguous and nonexistent New York DST wall times reject. VedAstro fixed offsets are retained; historical source civil-zone and DST provenance may still be uncertain. |
| Julian Day | Partially independently verified | Swiss conversion is exercised by published ephemeris vectors and round-trip fixtures. The round-trip is computational consistency, not an independent time-scale oracle. |
| Sidereal positions | Partially independently verified | Lahiri reset regression; chart fixture planet-longitude tolerance 0.0001°. Mean node used; Ketu is exactly opposite Rahu. A Mars vector independently compares to JPL Horizons; general fixture charts mostly share Swiss Ephemeris family. Installed PySwissEph currently reports Moshier planets + Swiss mean node. |
| Ascendant / houses | Partially cross-engine verified | Multi-region Ascendant tolerance 0.01° and Whole Sign house equality; Delhi reference Ascendant tolerance 0.003°. Placidus cusps are used for Ascendant calculation, then Whole Sign houses for planet mapping. Polar and broad independent house tests remain open. |
| D1 | Partially cross-engine verified | Sidereal planet longitudes and sign/house assignments compared with pinned Jyotishyamitra 1.4.0 and regional vectors. That package documents Swiss Ephemeris/Lahiri, so it is a separate chart implementation but not an independent ephemeris family. |
| D9 / D10 | Partially cross-engine verified | D9 signs checked on multiple inputs; D10 and D24 checked against pinned chart-library fixture. Divisional conventions remain school-dependent. |
| Nakshatra / Pada | Boundary verified; external timing partial | 81 start/midpoint/near-end longitude samples plus floating-point edge tests. One published nakshatra transition differs by about five minutes; a 10-minute acceptance window is retained. |
| Vimshottari MD/AD/PD | Partially independently verified | Lord order, balance and nested tiling tested; all 9 MD / 81 AD / 729 PD nodes compared with a pinned Jyotishyamitra tree. Parent-relative boundary ratios agree within 1e-9. Absolute civil dates differ by up to about 144 minutes over a theoretical 120-year cycle due to 365.2425-day versus calendar-year conventions; one real chart shared-edge comparison differs by up to about 90.22 minutes. Do not mix without normalizing conventions. |
| Jupiter/Saturn transit ingress and retrograde return | Partially independently verified | Replay, sign ingress, direct/retrograde re-entry and station tests. Published Saturn 2020 ingress and station tolerance is 90 seconds; Jupiter/Saturn exact ecliptic-longitude conjunction tolerance is 15 seconds against IMCCE. This does not validate interpreted transit effects. |
| Shadbala | Experimental | Several Kala Bala terms use defaults/simplifications; no independent numeric golden table. Exclude from calibration predictors until audited. |
| Ashtakavarga | Experimental | 337 total is only a checksum; source cells and shodhana semantics remain unresolved. Excluded from reliability features. |
| Yogas and domain rules | Interpretation unverified | Software output can be deterministic while classical interpretation remains convention-dependent and outcome validity unestablished. No formulas were changed to improve historical hit rates. |

### Independent numerical vectors and tolerances

- Swiss Ephemeris manual Appendix C / JPL Horizons Mars apparent position: longitude residual ≤0.2 arcsec and latitude residual ≤0.05 arcsec; the current engine reports Moshier fallback for planets.
- Jyotishyamitra 1.4.0 chart fixture: planetary sidereal longitude difference ≤0.0001°, Ascendant difference ≤0.003°, and supported D1/varga signs equal. Additional multi-region Ascendant checks allow ≤0.01° and planet longitude ≤0.0001°.
- Transit reference checks: Saturn ingress and station ≤90 seconds; 2020 Jupiter/Saturn ecliptic-longitude conjunction ≤15 seconds.
- Vimshottari: normalized parent-relative partitions ≤1e-9; absolute wall-clock boundary comparisons retain the stated year-convention discrepancy rather than averaging it away.
- UTC conversion: fixture round-trip preserves the given whole second exactly. DST ambiguous/nonexistent civil inputs are rejected instead of silently choosing an offset.

These checks measure numerical or software-convention agreement. They do not show that the astrological rule interpretations are true or predictive.

## Current follow-up verification

The current project `venv` is Python 3.11.9, PySwissEph 2.10.03 and pytz 2026.4. The full `unittest` suite passed **113 tests** after this follow-up’s changes. It includes current chart-reference, replay, dasha, transit, timezone, interval, compatibility, adapter-contract and corpus-quality tests. No chart formulas or engine conventions were changed. The machine-readable statuses and frozen conventions are in `astro_engine_manifest.json`; every candidate artifact copies that profile and lists experimental components actually used.

## Remaining numerical work

Broaden external ephemeris-family comparisons for multiple dates and all planets, add independent Ascendant vectors across high latitudes, expand Nakshatra/Pada reference times, reconcile dasha year conventions only by explicit normalization, and independently derive Shadbala/Ashtakavarga values before upgrading their status. Timezone history for pre-standard-time birth records remains source-limited. Keep computational verification separate from astrological interpretation and empirical prediction tests.
