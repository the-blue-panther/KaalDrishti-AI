"""
ML Calibration Engine v3.0 — Upgraded with 30+ features
========================================================
Uses RandomForestRegressor with features extracted from the full
astro pipeline (Shadbala, Ashtakavarga, Domain Scores, Yogas,
Combustion, Special Features, Predictive).

Takes the engine output dict directly → produces confidence scores.
"""

import numpy as np
from chart_engine.chart_state import ChartState
try:
    from sklearn.ensemble import RandomForestRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
import json


class MLCalibrationEngine:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.feature_names = []
        self._initialize_rich_model()

    def _initialize_rich_model(self):
        self.feature_names = [
            "avg_shadbala_rupas", "sun_rupas", "moon_rupas", "mars_rupas",
            "mercury_rupas", "jupiter_rupas", "venus_rupas", "saturn_rupas",
            "ashtakavarga_avg", "ashtakavarga_max", "ashtakavarga_min",
            "career_score", "wealth_score", "marriage_score", "health_score",
            "education_score", "total_yogas", "raja_yoga_count",
            "combust_planet_count", "retrograde_count", "vargottama_count",
            "uncertainty", "mangal_dosha_severity", "sade_sati_intensity",
            "pitra_dosha_severity", "muhurta_quality_score",
            "strongest_planet_rupas", "weakest_planet_rupas",
            "domain_avg_score", "dasha_confidence",
        ]
        # Do not fabricate fitted behavior from synthetic labels. A caller may
        # load a model trained on documented outcomes in the future; until
        # then this adapter must remain explicitly heuristic.

    def _extract_features(self, chart: ChartState, features: dict, quantitative_scores: dict) -> np.ndarray:
        chart_output = chart.to_chart_payload()
        f = np.zeros(len(self.feature_names))
        sb = chart_output.get("shadbala_summary", {}).get("planets", {})
        rupas = []
        if sb:
            rupas = [v.get("total_rupas", 3) for v in sb.values()]
            f[0] = np.mean(rupas) / 8.5 if rupas else 0.5
            for idx, p in enumerate(["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]):
                f[1+idx] = sb.get(p, {}).get("total_rupas", 3) / 8.0
        av = chart_output.get("ashtakavarga", {})
        sarva = av.get("sarvashtakavarga", {})
        if sarva:
            vals = list(sarva.values())
            f[8] = np.mean(vals) / 48 if vals else 0.5
            f[9] = max(vals) / 56 if vals else 0.5
            f[10] = min(vals) / 28 if vals else 0.3
        if quantitative_scores:
            f[11] = quantitative_scores.get("career", {}).get("raw_score", 0.5)
            f[12] = quantitative_scores.get("wealth", {}).get("raw_score", 0.5)
            f[13] = quantitative_scores.get("marriage", {}).get("raw_score", 0.5)
            f[14] = quantitative_scores.get("health", {}).get("raw_score", 0.5)
            f[15] = quantitative_scores.get("education", {}).get("raw_score", 0.5)
        comp = features.get("composite", {})
        f[16] = min(comp.get("total_yogas", 1) / 16, 1.0)
        f[17] = min(len(comp.get("yoga_categories", {}).get("Royal", [])) / 5, 1.0) if isinstance(comp.get("yoga_categories", {}).get("Royal", []), list) else 0
        combust = chart_output.get("combustion", {})
        f[18] = sum(1 for v in combust.get("combustion_status", {}).values() if v) / 7
        f[19] = sum(1 for v in features.get("strength", {}).values() if v.get("is_retrograde")) / 7
        vt = chart_output.get("vargottama", {})
        f[20] = sum(1 for v in vt.values() if v) / 8
        f[21] = chart_output.get("metadata", {}).get("uncertainty_score", 0.3)
        sf = chart_output.get("special_features", {})
        sev_map = {"None":0,"Mild":0.25,"Moderate":0.5,"Strong":0.75,"Severe (Triple Mangal Dosha)":1.0}
        f[22] = sev_map.get(sf.get("mangal_dosha", {}).get("severity","None"), 0)
        f[23] = sf.get("sade_sati", {}).get("intensity", 0)
        pitra = sf.get("pitra_dosha", {}).get("severity", "None")
        f[24] = {"None":0,"Mild":0.33,"Moderate":0.66,"Severe":1.0}.get(pitra, 0)
        f[25] = chart_output.get("predictive_tech", {}).get("muhurta_quality", {}).get("score", 5) / 10
        f[26] = max(rupas) / 8.5 if rupas else 0.7
        f[27] = min(rupas) / 4.5 if rupas else 0.4
        f[28] = np.mean([f[11], f[12], f[13], f[14], f[15]])
        dasha = chart_output.get("dasha_timeline", {})
        f[29] = 0.6 + 0.1 * min(len(dasha) / 15, 1.0) if dasha else 0.6
        return f.reshape(1, -1)

    def predict_confidence_from_chart(self, chart: ChartState, features: dict,
                                       quantitative_scores: dict) -> dict:
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return {"overall_confidence": None, "domain_confidences": {},
                    "status": "unavailable; no model trained on resolved prediction outcomes is loaded",
                    "reliability_reference": "insufficient_evidence"}
        X = self._extract_features(chart, features, quantitative_scores)
        chart_output = chart.to_chart_payload()
        overall = float(self.model.predict(X)[0])
        overall = max(0.0, min(1.0, round(overall, 4)))
        domain_confidences = {}
        for d in ["career","wealth","marriage","health","education","children",
                   "spiritual","foreign_travel","property","vehicle"]:
            bs = quantitative_scores.get(d, {}).get("raw_score", 0.5)
            adj = bs * (1.0 - chart_output.get("metadata", {}).get("uncertainty_score", 0.3) * 0.3)
            domain_confidences[d] = round(max(0.0, min(1.0, adj)), 3)
        importances = dict(zip(self.feature_names, self.model.feature_importances_.tolist()))
        top = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]
        band = "Very High" if overall > 0.8 else ("High" if overall > 0.65 else ("Moderate" if overall > 0.45 else ("Low" if overall > 0.3 else "Very Low")))
        return {"overall_confidence": overall, "domain_confidences": domain_confidences,
                "confidence_band": band, "feature_count": len(self.feature_names),
                "top_features": [{"feature": ft, "importance": round(imp, 4)} for ft, imp in top],
                "ml_model": "RandomForestRegressor(n=200, max_depth=10)"}

    def predict_confidence(self, chart: ChartState, features: dict, final_output: dict) -> float:
        """Backward-compatible scalar confidence API using the canonical ChartState."""
        return self.predict_confidence_from_chart(
            chart, features, {"career": final_output}
        )["overall_confidence"]


ml_engine = MLCalibrationEngine()
