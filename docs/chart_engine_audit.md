# Chart engine and Vimshottari readiness audit

Audit status: **core chart generation operational; several high-level systems are known approximations and must not be used as verified prediction evidence** (2026-10-01).

Implementation updates made after this snapshot are documented in [chart_engine_historical_readiness.md](chart_engine_historical_readiness.md); that addendum supersedes this report's earlier statements about replay timestamps, transit longitudes, DST handling, and ephemeris provenance.

## What is verified in this pass

- `AstroEngine.generate_chart` successfully produced a complete `ChartState` for a known London birth input in the current project venv.
- Planetary coordinates are calculated by PySwissEph with `FLG_SIDEREAL` and Lahiri mode initialized in `chart_engine.core_config`.
- The Vimshottari lord order and weights sum to 120 years. Birth Mahadasha lord is selected by the sidereal Moon's 27 equal nakshatra segments; remaining balance is the fraction of the current nakshatra remaining multiplied by its lord's nominal years.
- Antardasha duration is `MD years × AD lord years / 120`; Pratyantardasha duration is the same proportional subdivision of its parent. Five built-in `unittest` regression tests cover a hand-calculated Rohini/Moon balance, sequence, proportional closure, invalid longitudes, and exact horizon boundaries.
- Dasha timelines now use the same UT Julian Day as the chart, including when `julian_day_override` is supplied. Previously the dasha birth anchor came from the local-time string, which could disagree with the instant used for the chart.
- Dasha horizon overlap checks now use exact timestamps and half-open periods instead of truncated display dates.
- The seven classical Bhinnashtakavarga contribution tables had three missing entries (Moon-from-Mercury, Mars-from-Saturn, Saturn-from-Lagna): their totals were 334, not the fixed 337. These are corrected; a regression test checks the canonical totals Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56, Venus 52, Saturn 39.
- A day-only birth record is not silently imputed with noon by the current chart-feature dataset builder; records missing a required timestamp are rejected. Keep that behavior for evidence scoring unless an uncertainty/ensemble method is explicitly used.

## Subsystem audit matrix

| Subsystem | Audit result | Historical evidence use |
|---|---|---|
| UT/local-time conversion | Operational for ordinary timestamps. `pytz.localize()` uses its default policy for ambiguous/nonexistent DST wall times; callers must not assume these are resolved correctly. A Julian-Day override is now authoritative for chart and dasha math, but the supplied local-time text remains in provenance and can disagree. | Only with verified source timezone/instant and DST disambiguation. |
| Ephemeris positions | PySwissEph produces sidereal positions with Lahiri mode; Rahu is Mean Node and Ketu its exact opposite. Current smoke test ran with Swiss Ephemeris flags. The calculation does not persist a per-planet returned ephemeris flag/version in ChartMetadata, so fallback/model reproducibility is not fully auditable. | Core candidate, but still needs pinned reference vectors and provenance. |
| Ascendant/houses | Ascendant is obtained from Swiss Ephemeris Placidus cusps and shifted by Lahiri; planet houses are then Whole Sign. This is a coherent declared convention, but high-latitude/error handling and reference-chart comparisons are absent. | Only with birth-time certainty and declared house convention. |
| Vargas | D2/D3/D4/D7/D9/D10 and several less-universal vargas are implemented by bespoke formulas. D30 has a recognizable unequal-segment mapping; no full golden suite validates the set or resolves school-specific choices. | Do not use less-common vargas as verified evidence yet. |
| Panchang | Tithi, paksha, nakshatra/pada, yoga and karana are longitude-boundary arithmetic; karana has boundary tests. Vaar uses sunrise where Swiss rise succeeds and silently falls back to Julian weekday otherwise. Sunrise/panchang timezone and reference vectors are incomplete. | Partial; only tested fields/conventions. |
| Vimshottari | Formula and selected boundaries are tested; implementation convention is 365.2425 days. The proportional arithmetic is self-consistent, but independent exact-date golden vectors under matching conventions are still needed. | Primary dasha candidate, with convention and input uncertainty recorded. |
| Other dasha systems | Ashtottari's own module states that its 27-nakshatra mapping approximates the classical 28-star/Abhijit treatment. Jaimini Chara orders all forward signs before reverse signs via sorting, rather than a demonstrated classical sequence. Yogini/Kalachakra/additional dasha implementations have not been reference-validated; engine catches exceptions and substitutes empty results. | Exclude from evidence scoring until independently implemented/tested; empty output must not be interpreted as “no periods.” |
| Ashtakavarga | Three transcription errors fixed by the 337-total invariant. However Trikona Shodhana is applied to aggregate Sarvashtakavarga rather than each Bhinna table, Ekadhipatya reduction is a simplified pairwise minimum, and a standalone Lagna bindu/Samudaya table is a project-specific construction. Output is not a complete classical Shodhana result. | Raw BAV/SAV only after chart-level test; Shodhana/Samudaya unsupported for validation. |
| Graha Drishti | Discrete sign-house aspects, with special Mars/Jupiter/Saturn aspects; Rahu/Ketu special aspects are a tradition choice. Strength interpolation is heuristic and omits longitude-based exact aspects. | Use only binary sign-aspect conditions with declared school; do not treat strength as classical quantitative strength. |
| Combustion/war | Angular-distance combustion thresholds are implemented, but choices vary by tradition. Engine does not pass planetary latitudes to war analysis; its default equal latitudes make winner depend on planet iteration order. | Combustion only with threshold convention; war winner is not reliable. |
| Shadbala | Source explicitly labels multiple Kala Bala parts “simplified”; engine supplies default noon/day-birth values and does not calculate actual birth sunrise/time parts. Other subcomponents also include approximations. Aspect-derived Drik output is computed separately and is not used to override Shadbala's own simplified Drik. | Do not use current total/category as a verified Shadbala score. |
| Jaimini/KP | Several Jaimini components are conventional variants but lack full reference vectors. KP uses a fixed approximate linear ayanamsa and, unless cusps are passed, synthetic equal 30° cusps; engine passes no true cusps. | KP output is approximate, not production-verified. |
| Special/predictive features | Mangal/Pitra/etc. are simplified rule flags with school-dependent definitions. “Medical” indicators are heuristic, not validated medical facts. “Varshaphala” computes a Muntha approximation, not a full solar-return chart; default year is hardcoded 2026. Remedy suggestions key off dusthana placement rather than a complete strength/rulership analysis. | Not evidence-grade. Do not present heuristic flags as factual outcome predictions. |
| Transit/Navatara | Current transits use wall-clock `now`, so identical natal input gives time-varying ChartState. Navatara transit longitudes are reconstructed from sign midpoints (15° approximation), not actual transit positions. No `as_of` input exists for historical replay. | Cannot be used in a reproducible historical backtest until reference time is explicit and actual longitudes are retained. |
| Uncertainty | `d1_stable_5min`/`d9_stable_5min` compare only the Ascendant at ±5 minutes; the aggregate 0–1 score is a hand-weighted indicator, not a calibrated uncertainty probability, and does not include birth-time uncertainty intervals. | Label as a limited sensitivity flag, never as confidence/reliability. |

The fixed-total correction is consistent with the classical table checksum reported by [AstroSK's table reference](https://docs.astrosk.com/glossary/vedic/ashtakavarga/definition-of-suns-ashtakavarga) and the [Phaladeepika Ashtakavarga tables](https://www.panchanga.lv/wp-content/uploads/2020/06/Phaladipika_Shri-Mantreswara.pdf). Different textual recensions may differ in individual rows; lock the selected recension before expanding tests.

## Vimshottari convention and limits

The code uses a fixed **365.2425-day year**. The 120-year lord weights and proportional subperiod formulas are mathematically self-consistent under this convention. A pinned Jyotishyamitra 1.4.0 full tree independently checks all 9 MD, 81 AD, and 729 PD nodes: lord identities and parent-relative interval boundaries agree within 1e-9. Absolute dates differ by up to 144 minutes in the 120-year cycle because the reference uses a 120-calendar-year span. A second Delhi chart compares 1,586 shared MD/AD/PD edges with a maximum difference of 90.22 minutes. Those date deltas are convention diagnostics, not evidence of a broken proportional formula; input/ephemeris differences and astrological meanings are not validated by this test.

The implemented dasha timeline currently presents nine successive Mahadashas beginning at the theoretical start of the birth lord's period. Consumers should distinguish that pre-birth theoretical start from the remaining period active at birth. Display strings are day precision; `start_exact` / `end_exact` are authoritative for event-window comparisons.

## Not certified yet

This pass is not a complete mathematical audit of every subsystem. No complete independent golden-vector suite currently certifies all of the following: Swiss Ephemeris position/ayanamsa choices for agreed reference charts; timezone history and DST ambiguity; ascendant/whole-sign house mapping; every divisional-chart formula; Panchang boundaries; Shadbala; Ashtakavarga; aspects; or Yogini, Ashtottari, Jaimini, Kalachakra, and additional dasha systems. A legacy archived report only checked output shape/metadata and is not mathematical validation.

**Conclusion:** the chart engine is not yet production-verified for the user's historical event-matching plan. Core sidereal positions, Whole Sign placements, Panchang and Vimshottari can be brought to that standard with reference vectors. The other systems listed above need to be corrected, explicitly downgraded to experimental, or excluded from the reliability features. Add multiple reference charts with source conventions recorded (birth instant/timezone, coordinates, ephemeris/ayanamsa, house convention, dasha-year convention), compare every supported output field, test astronomical and period boundaries, and preserve vectors as automated tests. Unsupported or uncertain subsystems must remain marked unverified rather than being treated as historical evidence.

## Historical forecast validation prerequisite

The current marriage experiment has observed marriage dates but no prediction archived before those dates. The occupation dataset has observed labels but no prior astrology forecast. Neither can measure historical accuracy of astrological rules. For that, generate versioned claim records before revealing outcomes: domain/subdomain, stable rule/condition IDs, outcome definition, forecast window, chart-input provenance/precision, and prediction timestamp. Match only resolved events under predeclared broad-match rules; retain pending/censored cases; split by person and hold out a source/cohort. Day-only birth records should not contribute to time-dependent predictions as if their noon chart were factual.

## Calculation convention references

- [Vimshottari guide: remaining nakshatra fraction and proportional subperiods](https://www.shreekundli.com/vedic-astrology/dasha/vimshottari-dasha-guide)
- [Vedic Proof dasha API: explicit 365.2425-day convention](https://vedicproof.com/dasha-api)
- [JyotiPy dasha API: 365.25-day convention and software differences](https://jyotipy.readthedocs.io/en/latest/api/dasha.html)

These references document implementation conventions; they are not evidence that astrology predicts life outcomes.
