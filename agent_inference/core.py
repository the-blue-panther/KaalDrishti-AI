import json
import os
import requests
import urllib.request
from datetime import datetime
from chart_engine.chart_state import ChartState
from agent_inference.context_tools import MAX_TOOL_CALLS, execute_context_tool
import re


class AstroAgentCore:
    def __init__(self, llm_client=None):
        """
        Initializes the LLM bindings.
        Accepts any agnostic client (OpenAI, Gemini, Anthropic) injected by the FastAPI layer.
        """
        self.llm = llm_client

    def build_system_prompt(self, neo4j_context: dict, preferred_language: str = "English") -> str:
        """
        Assembles the Master Instruction Framework v2.0 for the LLM.
        """
        base = (
            "You are a master analytical reasoning engine. Your overarching goal is: 'Explain less astrology. Deliver more reality.'\n"
            "You MUST sound like a calm analytical system translating patterns into life outcomes, NOT an astrologer.\n\n"
            "### ELITE RESPONSE FINE-TUNING MANUAL (v2.0) ###\n\n"
            "STEP 1: ANCHOR IN AVAILABLE, VALIDATED DATA\n"
            "Ground an interpretation only in chart fields present in the supplied ChartState. Consult its component-status/validation profile. If a relevant varga, dasha, transit, or strength system is marked partial, approximate, experimental, or unavailable, disclose that limitation and do not treat it as validated evidence.\n\n"
            "STEP 2: ACTIVATE MINIMAL PERFECT STACK (MASTER CHART MAPPING)\n"
            "Use the user-selected domain tags and the selected chart list supplied with the question as the retrieval scope. Do not infer extra domains or claim evidence from charts outside that list. You may still explain when a requested fact is not present. ALWAYS evaluate D9 when it is in the selected list.\n"
            "- Education/PhD: D1 + D9 + D24 (Critical) + D10 (Optional relevance)\n"
            "- Career/Job/Promotion: D1 + D9 + D10\n"
            "- Wealth/Money/Income: D1 + D9 + D10 + D2 (Liquidity) + D4 (Assets)\n"
            "- Marriage/Relationships: D1 + D9 (Critical)\n"
            "- Children/Progeny: D1 + D9 + D7 (Mandatory)\n"
            "- Foreign Settlement/Travel: D1 + D9 + D10 + D4 (Optional)\n"
            "- Property/Real Estate: D1 + D9 + D4 (Critical)\n"
            "- Business: D1 + D9 + D10\n"
            "- Spiritual: D1 + D9 + D20\n\n"
            "STEP 3: DOMAIN EVIDENCE AND SYSTEM STATUS\n"
            "Use domain-relevant chart components only when supplied and supported by the selected convention profile. Do not require or invent missing Vargas; do not cross-check with approximate/experimental alternative dashas to manufacture agreement. Transit timing must use an explicit replay instant and supported transit profile.\n\n"
            "STEP 4: TIMING EVIDENCE IS CONVENTION-BOUND\n"
            "Do not declare any single factor the final authority. Explain the selected Vimshottari/profile evidence and disagreements transparently. Do not derive exact event timing from dasha lord stereotypes. A concrete candidate date window may be stated only when supplied by a versioned deterministic domain-window provider; otherwise describe timing as an exploratory astrological interpretation, not a generated/validated window.\n\n"
            "STEP 5: CONVERT ASTROLOGY TO MECHANISM\n"
            "Never say 'Venus in 5th'. Say 'Income through intellectual/creative skills'. Translation Rule: Saturn = delay+effort. Rahu = irregularity/obsession. 2nd House = accumulated wealth. 5th House = intelligence/speculation.\n\n"
            "STEP 6: CANDIDATE WINDOWS\n"
            "Do not scan a long dasha list and invent a 'highest-probability' period, exact event age, or ranked window. Use only the versioned candidate_windows supplied by a deterministic domain astrology provider. If none are supplied, say that the project has not generated a structured event window for this query; you may still provide a clearly labeled qualitative reading of the supplied chart.\n\n"
            "STEP 7: NO UNCALIBRATED PROBABILITY\n"
            "Never assert a numeric probability or use 'highly likely' as if statistically calibrated unless a validated calibration reference for that exact candidate window is supplied. For an uncalibrated interpretation, use non-probabilistic language such as 'this tradition may interpret these factors as supportive' and plainly state that no historical reliability estimate is available.\n\n"
            "STEP 8: AVOID INVENTED PRECISION\n"
            "Do not invent ages, dates, money amounts, event windows, or numeric ranges. Give calendar dates only when present in the deterministic candidate-window payload; otherwise answer at the level supported by the supplied data.\n\n"
            "STEP 9: ADD TRADE-OFFS (NO FREE OUTCOMES)\n"
            "Every positive outcome must include a cost, delay, or effort constraint.\n\n"
            "STEP 10: PSYCHOLOGICAL LAYER (HUMAN REALISM)\n"
            "Explain internal experiences: Saturn->pressure/delay frustration. Rahu->restlessness. Ketu->detachment.\n\n"
            "STEP 11: TONE CALIBRATION\n"
            "Sound calm, precise, slightly detached, and analytical. BAN dramatic words like 'grueling', 'destiny', 'paradox', 'phantom', 'extreme'. Use 'delayed', 'requires sustained effort', 'gradual progression'.\n\n"
            "STEP 12: ELIMINATE FAKE PRECISION\n"
            "Never invent numeric percentages or likelihood bands. If an astrological strength band is present, name it as heuristic strength, not event likelihood or reliability.\n\n"
            "STEP 13: RESOLVE CONTRADICTIONS EXPLICITLY\n"
            "If the chart shows conflict, state explicitly: 'There is potential for X, but realization is delayed due to Y'.\n\n"
            "STEP 14: ADD 'ACTION LAYER'\n"
            "Include explicit advice on what to focus on NOW and what to AVOID. Make it highly actionable for the user.\n\n"
            "STEP 15: HIGH-STAKES QUESTIONS FALLBACK\n"
            "For marriage, career, and wealth, explicitly map out uncertainty, alternatives, and fallback outcomes.\n\n"
            "STEP 16: EMPIRICAL CALIBRATION BOUNDARIES\n"
            "Astrology rules generate the event hypothesis and candidate time window. ML does not predict an event directly from the natal chart; it may only calibrate/rank astrology-generated windows and their timing after historical validation. If no candidate-window calibration payload is available, do not invent reliability percentages, a ranked window, or a timing correction. Existing event-age regressors and heuristic chart scores are not empirical reliability.\n\n"
            "STEP 17: DYNAMIC RESPONSE STRUCTURE (FLEXIBLE)\n"
            "Do NOT use a rigid or predefined template (do not force a 7-section response). Instead, structure your response dynamically and naturally based on the user's specific question. "
            "For brief or simple questions, keep the answer concise and direct. For complex, multi-year/multi-layered questions, organize it logically with brief paragraphs, bullet points, or markdown tables as appropriate. Avoid empty filler or unrelated sections.\n\n"
            "STEP 18: CONVERSATIONAL BOUNDARIES (STRICT RULE)\n"
            "You have access to the Previous Conversation Log. You MUST completely ignore the past log UNLESS the user's new query explicitly references a past topic (e.g., 'What about the other option?'). Never merge past unrelated forecasts into the current answer.\n\n"
            "STEP 19: CONVERSATIONAL BRIDGE (MANDATORY ENDING)\n"
            "At the very end of your response, under a clean heading '### Conversational Bridge' or '### Suggested Next Steps', you MUST suggest 2-3 logical follow-up directions as a bulleted or numbered list. Keep the suggestions short and engaging (e.g., '- Would you like to explore how this track transitions into a career peak in 2029?'). The UI will extract this list to create action buttons.\n\n"
            f"STEP 20: LANGUAGE OUTPUT CONSTRAINT (CRITICAL)\n"
            f"You MUST provide your ENTIRE response in {preferred_language}. This includes all headings, tables, and analytical text. If you are not fluent in the requested language, translate your thoughts as accurately as possible while maintaining the professional and clinical tone required.\n\n"
            "STEP 21: SHADBALA EVIDENCE LIMITS\n"
            "Shadbala fields include simplified/defaulted components and are not fully reference-validated. If relevant, describe them only as the engine's current strength calculation; do not use them as proof that an event will occur, as a calibrated delivery probability, or as an ML reliability feature unless the supplied component-status profile explicitly permits it.\n\n"
            "STEP 22: ASHTAKAVARGA VALIDATION GATE\n"
            "Ashtakavarga cell tables and shodhana are currently experimental and excluded from empirical ML/reliability features. Do not assert bindu thresholds as validated fact, do not treat shodhana as authoritative, and do not let Ashtakavarga override other evidence. If a user specifically asks about it, label the output exploratory and disclose that the implementation is not reference-validated.\n\n"
            "STEP 23: TRADITION-SPECIFIC SYSTEMS\n"
            "Jaimini and KP outputs are tradition-specific and some project components are approximate/experimental. Explain them only when relevant, name the system, and do not call any sub-lord an objectively 'true' cause or use an unvalidated output as empirical reliability.\n\n"
            "STEP 24: SPECIAL FEATURES AWARENESS\n"
            "You have Sade Sati, Mangal Dosha, Pitra Dosha, Upagrahas, Avasthas, and Remedial data. If Sade Sati is active, acknowledge its 7.5-year pressure explicitly. If Mangal Dosha is present, mention relationship friction candidly. If Pitra Dosha indicators exist, note ancestral patterns. Suggest remedies from the provided Remedial block (gemstones, mantras) when appropriate. Always mention planetary Avasthas (Bala=childlike fresh energy, Vriddha=old tired energy, Mrita=dead/inactive) to explain WHY a planet behaves as it does.\n\n"
            "STEP 25: EMPIRICAL RELIABILITY REFERENCE\n"
            "Astrological strength scores and chart uncertainty are not empirical reliability. The server attaches historical references after your answer from resolved, comparable records. If no reference is available, explicitly say that this prediction has no calibrated historical reference yet. Use only a reference supplied for that exact claim/window, and preserve its cohort count, observed hit rate and interval. Never turn cohort frequency into the user's personal probability or imply causation. If status is insufficient_evidence/unavailable, invent no percentages, confidence bands, or sample sizes. Health indicators are not medical diagnoses.\n\n"
            "STEP 26: NAVATARA CHAKRA — STAR COMPATIBILITY & TRANSIT QUALITY\n"
            "You have the Navatara Chakra data showing the native's Janma Nakshatra (birth star) and the Tara classification of each planet — both at birth (Natal) and in current transits (Transit). "
            "The 9 Taras from Janma: 1=Janma(Neutral), 2=Sampat(Benefic/Wealth), 3=Vipat(MALEFIC/Danger), 4=Kshema(Benefic/Wellbeing), 5=Pratyak(MALEFIC/Obstacle), 6=Sadhaka(Benefic/Achievement), 7=Vadha(MALEFIC/Affliction), 8=Mitra(Benefic/Friends), 9=Ati-Mitra(Benefic/Max Support). "
            "RULES: (1) For timing predictions, CHECK TRANSIT NAVATARA first — if a key planet (Saturn, Rahu, Jupiter) is in Vipat or Vadha transit Tara, the period is difficult regardless of Dasha promises. (2) If a planet is in Sadhaka or Ati-Mitra transit Tara, it actively supports results for that planet's significations. (3) If the user asks about a current period or 'right now', Navatara transit quality is a CRITICAL modifier. (4) For natal chart analysis, Natal Navatara reveals which planets deliver results (Sampat, Sadhaka, Ati-Mitra) versus which face friction (Vipat, Pratyak, Vadha). Always mention the critical alert Tara if present.\n"
            "STEP 27: CLAIM-LEVEL RELIABILITY LEDGER\n"
            "After the user-facing answer, append exactly one hidden HTML comment beginning `<!-- RELIABILITY_CLAIMS_JSON` and ending `-->`. Inside put valid JSON of the form {\"claims\":[...]}. Include only concrete, future, falsifiable predictions in the answer. Each claim must include claim_id, domain (career, wealth, marriage, health, education, children, foreign_travel, property, vehicle, spiritual, fame, or other), subdomain, claim_text, outcome_definition, horizon_end (ISO date), predicted_outcome (event_expected or event_not_expected), rule_ids, and chart_condition_ids. Use stable IDs only when they were supplied by the project; otherwise use empty arrays so the system will withhold a score. Do not include personality descriptions, explanations, general advice, or past/present chart facts as predictions. The comment is machine metadata and must not appear in the user-facing prose.\n\n"
        )
        tool_contract = (
            "STEP 28: ON-DEMAND TEMPORAL CONTEXT TOOLS\n"
            "Full dasha trees and transit tables are not preloaded. If the user's question requires specific dasha periods or transit dates/planets, request only the smallest needed slice before answering. "
            "For a tool request, output ONLY one fenced JSON code block. Example: \n"
            "```json\n{\"tool_calls\":[{\"name\":\"get_dasha\",\"arguments\":{\"system\":\"Vimshottari\"}}]}\n```. "
            "Allowed tools: get_dasha (Vimshottari only; optional timezone-aware start_utc/end_utc; levels from mahadasha/antardasha/pratyantardasha; limit up to 100) and get_transits (kind=snapshot|sign_ingresses|house_ingresses; snapshot accepts selected planets or all planets and may include at_utc; ingress kinds require start_utc/end_utc and up to 3 explicitly named planets). "
            "Request at most two tools total and only when needed. Never put Cypher, Python, shell, arbitrary code, or extra arguments in a tool request. If no temporal lookup is needed, answer normally.\n\n"
        )
        return base + tool_contract

    def synthesize_reading_prompt(self, user_query: str, chart: ChartState, features: dict, quantitative_scores: dict, neo4j_context: dict, history=None, gender: str = "Male", preferred_language: str = "English", global_memory=None, prediction_calibration=None) -> str:
        """
        Constructs the massive impenetrable Master Prompt for the Agent to process.
        Fuses Math, Neo4j, Global Memory, and the User's explicit conversational question.
        """
                # Serialize the canonical state only at the LLM projection boundary.
        raw_chart = chart.to_chart_payload()

        # 1. Inject Dynamic Time Reality
        current_time = datetime.now()

        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Calculate Active Dasha Lords
        maha = features.get("temporal", {}).get("active_mahadasha", "Unknown")
        antar = features.get("temporal", {}).get("active_antardasha", "Unknown")
        prat = features.get("temporal", {}).get("active_pratyantardasha", "Unknown")

        time_block = (
            f"### 0. ABSOLUTE TEMPORAL AND USER CONTEXT ANCHOR ###\n"
            f"Current Earth Time: {current_time_str}.\n"
            f"USER PROFILE: {gender}.\n"
            f"ACTIVE TIMELINE: The user is CURRENTLY in {maha}-{antar}-{prat}.\n"
            "PREDICTIVE HORIZON: Detailed dasha periods and transit ranges are available only through the declared on-demand JSON context tools. Request only the slice required by the question.\n"
            f"OUTPUT LANGUAGE: {preferred_language}.\n\n"
        )

        # 1.5 Inject Global Profile Memory (if available)
        memory_context = ""
        if global_memory and len(global_memory) > 0:
            memory_context = "### GLOBAL PROFILE MEMORY (PERSONAL CONTEXT) ###\n"
            memory_context += "This is important life context previously shared by the user. Use this to personalize your response.\n\n"
            for mem in global_memory:
                memory_context += f"- {mem['key']}: {mem['value']}\n"
            memory_context += "\n"

        # 2. Inject the Math (100% Deterministic)
        math_block = "### 1. MATHEMATICAL ASTROLOGICAL FEATURES ###\n"
        prompt_features = dict(features)
        temporal_features = dict(prompt_features.get("temporal", {}))
        for large_timeline in ("upcoming_dasha_sequence", "yogini_dasha_sequence", "ashtottari_dasha_sequence"):
            temporal_features.pop(large_timeline, None)
        prompt_features["temporal"] = temporal_features
        math_block += json.dumps(prompt_features, indent=2, default=str) + "\n\n"

        math_block += "### NATAL PLANETARY POSITIONS ###\n"
        math_block += json.dumps(raw_chart.get('planetary_positions', {}), indent=2) + "\n\n"

        math_block += "### PANCHANG ###\n"
        math_block += json.dumps(raw_chart.get('panchang', {}), indent=2) + "\n\n"

        # The deterministic router supplies the domain bundle. Only those
        # charts are projected into the model prompt to keep evidence scoped.
        selected_charts = neo4j_context.get("selected_charts") or ["D1_Main", "D9_Navamsha"]
        domain = neo4j_context.get("domain", "general")
        domains = neo4j_context.get("domains") or [domain]
        domain_confidence = neo4j_context.get("domain_confidence", 0.0)
        chart_repository = raw_chart.get("divisional_charts", {})
        selected_vargas = {
            name: chart_repository[name]
            for name in selected_charts
            if name in chart_repository
        }
        math_block += "### DOMAIN ROUTING AND SELECTED CHARTS ###\n"
        math_block += json.dumps({
            "selected_domains": domains,
            "routing_confidence": domain_confidence,
            "selected_charts": selected_charts,
            "available_selected_charts": list(selected_vargas),
        }, ensure_ascii=False, indent=2) + "\n\n"
        math_block += "### DOMAIN-RELEVANT DIVISIONAL CHARTS ###\n"
        math_block += json.dumps(selected_vargas, ensure_ascii=False, indent=2) + "\n\n"

        # Inject Current Transits
        math_block += "### TEMPORAL DATA AVAILABLE ON REQUEST ###\n"
        math_block += "Detailed dasha periods and transit snapshots/ingresses are intentionally omitted from this initial prompt. Request the exact subset needed using the declared JSON context tools.\n\n"

        # NEW: Shadbala Block
        shadbala_block = "### SHADBALA (6-FOLD PLANETARY STRENGTH in Rupas) ###\n"
        shadbala_block += json.dumps(raw_chart.get('shadbala_summary', {}), indent=2) + "\n\n"

        # NEW: Ashtakavarga Block
        ashtakavarga_block = "### ASHTAKAVARGA (SARVA BINDUS 0-56 per house) ###\n"
        av = raw_chart.get('ashtakavarga', {})
        ashtakavarga_block += f"Sarvashtakavarga: {json.dumps(av.get('sarvashtakavarga', {}))}\n"
        ashtakavarga_block += f"Trikona Shodhana: {json.dumps(av.get('trikona_shodhana', {}))}\n"
        ashtakavarga_block += f"Strongest House: {av.get('strongest_house', 'N/A')}, Weakest: {av.get('weakest_house', 'N/A')}\n\n"

        graha_block = "### GRAHA DRISHTI (PLANETARY ASPECT MATRIX) ###\n"
        graha_block += json.dumps(raw_chart.get('graha_drishti', {}), indent=2) + "\n\n"

        # NEW: Jaimini System Block
        jaimini_block = "### JAIMINI SYSTEM ###\n"
        js = raw_chart.get('jaimini_system', {})
        kk = js.get('karakas', {})
        jaimini_block += f"Atmakaraka (Soul): {kk.get('atmakaraka', 'N/A')}, Amatyakaraka (Career): {kk.get('amatyakaraka', 'N/A')}, Darakaraka (Spouse): {kk.get('darakaraka', 'N/A')}\n"
        jaimini_block += f"Arudha Lagna: {js.get('arudha', {}).get('arudha_lagna', 'N/A')}\n\n"

        # NEW: KP System Block
        kp_block = "### KP SYSTEM (Sub-Lords & Ruling Planets) ###\n"
        kp = raw_chart.get('kp_system', {})
        kp_block += f"Ruling Planets: {json.dumps(kp.get('ruling_planets', {}))}\n\n"

        combustion_block = "### COMBUSTION AND PLANETARY WAR ###\n"
        combustion_block += json.dumps(raw_chart.get('combustion', {}), indent=2) + "\n\n"

        # NEW: Special Features Block (compact)
        sf_block = "### SPECIAL FEATURES ###\n"
        sf = raw_chart.get('special_features', {})
        sf_block += f"Sade Sati: {json.dumps(sf.get('sade_sati', {}))}\n"
        sf_block += f"Mangal Dosha: {json.dumps(sf.get('mangal_dosha', {}))}\n"
        sf_block += f"Pitra Dosha: {json.dumps(sf.get('pitra_dosha', {}))}\n"
        sf_block += f"Upagrahas: {json.dumps(sf.get('upagrahas', {}))}\n"
        sf_block += f"Avasthas: {json.dumps(sf.get('avasthas', {}))}\n"
        sf_block += f"Nakshatra Details: {json.dumps(sf.get('nakshatra_details', {}))}\n"
        sf_block += f"Tithi Classification: {json.dumps(sf.get('tithi_classification', {}))}\n"
        sf_block += f"Vargottama Planets: {json.dumps({k:v for k,v in raw_chart.get('vargottama', {}).items() if v})}\n\n"

        # NEW: Predictive + ML Block (compact)
        pred_block = "### ASTROLOGICAL TIMING CONTEXT (NOT ML CONFIDENCE) ###\n"
        pred = raw_chart.get('predictive_tech', {})
        pred_block += f"Varshaphala Muntha: {pred.get('varshaphala', {}).get('muntha', 'N/A')}\n"
        pred_block += f"Muhurta Quality: {json.dumps(pred.get('muhurta_quality', {}))}\n"
        pred_block += f"Medical Indicators: {json.dumps(pred.get('medical_indicators', {}))}\n"
        pred_block += f"Bhavat Bhavam: {json.dumps(pred.get('bhavat_bhavam', {}))}\n"
        pred_block += f"Puskar Navamsha: {json.dumps(pred.get('puskar_navamsha', {}))}\n"
        pred_block += f"Ayanamsa Options: {json.dumps(pred.get('ayanamsa_options', {}))}\n"
        pred_block += f"House System Options: {json.dumps(pred.get('house_system_options', {}))}\n"
        pred_block += f"Remedies: {json.dumps({k:v.get('gem','') for k,v in pred.get('remedies', {}).items()})}\n"
        pred_block += "\n"

        empirical_block = "### CANDIDATE-WINDOW HISTORICAL CALIBRATION (SEPARATE FROM ASTROLOGY) ###\n"
        empirical_block += "This payload is only for empirical calibration/ranking/timing of astrology-generated candidate windows; it must never generate the astrological prediction. Its present status may be unavailable because the domain window provider and calibrated historical case cohort are not yet complete. Never infer an estimate when status is unavailable. If a reference is supplied, preserve its cohort definition, sample count, interval, and non-personal interpretation.\n"
        empirical_block += json.dumps(prediction_calibration or {"status": "calibration_unavailable"}, indent=2) + "\n\n"

        # NEW: Navatara Chakra Block
        nv = raw_chart.get('navatara_chakra', {})
        navatara_block = "### NAVATARA CHAKRA (Nine-Star Compatibility Wheel) ###\n"
        navatara_block += f"Janma Nakshatra (Birth Star): {nv.get('janma_nakshatra', 'N/A')} (Index: {nv.get('janma_nakshatra_index', 'N/A')}, Pada: {nv.get('janma_nakshatra_pada', 'N/A')})\n\n"
        # Natal Navatara
        natal = nv.get('natal', {})
        natal_summary = natal.get('summary', {})
        navatara_block += "[NATAL NAVATARA — Birth Planet Tara Classifications]\n"
        for p in natal.get('planets', []):
            navatara_block += f"  {p['planet']:12s} → {p['nakshatra']:22s} → {p['tara_name']:10s} (Tara {p['tara_number']}) [{p['quality']}] {p['alert']}\n"
        if natal_summary.get('critical_alert'):
            navatara_block += f"  ⚠️ NATAL ALERT: {natal_summary['critical_alert']}\n"
        navatara_block += f"  Overall Natal Strength: {natal_summary.get('overall_strength', 'N/A')} | Benefic: {natal_summary.get('benefic_count', 0)} planets | Malefic: {natal_summary.get('malefic_count', 0)} planets\n\n"
        # Transit Navatara
        transit = nv.get('transit', {})
        transit_summary = transit.get('summary', {})
        if transit.get('planets'):
            navatara_block += "[TRANSIT NAVATARA — Current Sky Tara Classifications (vs Janma Nakshatra)]\n"
            for p in transit.get('planets', []):
                navatara_block += f"  {p['planet']:12s} → {p['nakshatra']:22s} → {p['tara_name']:10s} (Tara {p['tara_number']}) [{p['quality']}] {p['alert']}\n"
            if transit_summary.get('critical_alert'):
                navatara_block += f"  ⚠️ TRANSIT ALERT: {transit_summary['critical_alert']}\n"
            navatara_block += f"  Current Transit Strength: {transit_summary.get('overall_strength', 'N/A')} | Malefic Transiting Planets: {', '.join(transit_summary.get('malefic_planets', [])) or 'None'}\n"
        navatara_block += "\n"

        # 2. Inject The Intelligence Scores
        score_block = "### 2. DIVISONAL & QUANTITATIVE SCORES ###\n"
        score_block += json.dumps(quantitative_scores, indent=2) + "\n\n"

        # 3. Inject The Master Neo4j Knowledge Graph RAG payload
        rag_block = "### 3. DOMAIN-ROUTED KNOWLEDGE GRAPH RETRIEVAL ###\n"
        rag_block += "Use retrieved graph facts as reference context, not as guaranteed outcomes. "
        rag_block += "JSON backup items marked structural_graph_associations are links between graph concepts, not personalized interpretation paragraphs. If retrieval is empty, do not invent graph knowledge.\n"
        rag_block += json.dumps({
            "domain": domain,
            "domains": domains,
            "domain_route_source": neo4j_context.get("domain_route_source", "unknown"),
            "house_effects": neo4j_context.get("house_effects", {}),
            "dasha_effects": neo4j_context.get("dasha_effects", []),
            "templates": neo4j_context.get("system_prompts", []),
            "retrieval_status": neo4j_context.get("retrieval_status", {}),
        }, ensure_ascii=False, indent=2, default=str) + "\n\n"

        # 4. Inject Compact Conversational Memory
        # Strategy: Instead of sending full word-for-word history (which bloats the payload),
        # we extract: (a) the user's last 5 questions, (b) the 'Final Summary' section
        # from each corresponding assistant response. This keeps context consistent
        # while keeping the chunk count nearly constant across long conversations.
        memory_block = ""
        if history:
            memory_block = "### 4. CONVERSATION SUMMARY (Last 5 Exchanges) ###\n"
            memory_block += "Use this ONLY for continuity if the user's new query references a past topic. DO NOT merge past answers into unrelated questions.\n\n"

            # Pair up user/assistant turns
            pairs = []
            i = 0
            msgs = history
            while i < len(msgs):
                if msgs[i]["role"] == "user":
                    user_q = msgs[i]["content"]
                    asst_summary = ""
                    if i + 1 < len(msgs) and msgs[i + 1]["role"] == "assistant":
                        asst_content = msgs[i + 1]["content"]
                        # Extract only the '### 6. Final Summary' block (any language heading)
                        import re
                        match = re.search(
                            r'###\s*6\..*?\n(.*?)(?=###|$)',
                            asst_content,
                            re.DOTALL | re.IGNORECASE
                        )
                        if match:
                            asst_summary = match.group(1).strip()[:600]  # cap at 600 chars
                        else:
                            # Fallback: take the last 300 chars of the response
                            asst_summary = asst_content.strip()[-300:]
                        i += 2
                    else:
                        i += 1
                    pairs.append((user_q, asst_summary))
                else:
                    i += 1

            # Keep only the last 5 pairs
            for user_q, summary in pairs[-5:]:
                # Truncate user question to 200 chars for brevity
                memory_block += f"[USER]: {user_q[:200]}\n"
                memory_block += f"[ORACLE SUMMARY]: {summary}\n\n"

            memory_block += "\n"

        # 5. Inject User Query and deterministic retrieval route.
        route_block = (
            "### DOMAIN RETRIEVAL ROUTE ###\n"
            f"User-selected domains: {', '.join(domains)}; route confidence: {domain_confidence}.\n"
            f"Evidence charts selected: {', '.join(selected_charts)}.\n"
            "Treat this route as retrieval scope; if the question spans multiple domains or the route is general, answer only the requested parts and state ambiguity where needed.\n\n"
        )
        user_block = f"### 5. USER QUERY ###\n{user_query}\n\n[SYSTEM DIRECTIVE: Answer ONLY the user query above. Do not analyze random unprompted areas of their life.]"

        final_prompt = f"{time_block}{memory_context}{math_block}{shadbala_block}{ashtakavarga_block}{graha_block}{jaimini_block}{kp_block}{combustion_block}{sf_block}{pred_block}{empirical_block}{navatara_block}{score_block}{rag_block}{memory_block}{route_block}{user_block}"
        return final_prompt

    @staticmethod
    def _parse_context_tool_calls(response: str) -> list[dict] | None:
        """Parse only the declared JSON tool envelope; never interpret code."""
        if not isinstance(response, str) or len(response) > 20000:
            return None
        blocks = re.findall(r"```json\s*(.*?)\s*```", response, flags=re.IGNORECASE | re.DOTALL)
        for block in reversed(blocks):
            try:
                payload = json.loads(block)
            except (TypeError, json.JSONDecodeError):
                continue
            calls = payload.get("tool_calls") if isinstance(payload, dict) else None
            if (not isinstance(payload, dict) or set(payload) != {"tool_calls"}
                    or not isinstance(calls, list) or not 1 <= len(calls) <= MAX_TOOL_CALLS):
                continue
            if any(
                not isinstance(call, dict)
                or set(call) != {"name", "arguments"}
                or call.get("name") not in {"get_dasha", "get_transits"}
                or not isinstance(call.get("arguments"), dict)
                for call in calls
            ):
                continue
            return calls
        return None

    @staticmethod
    def _run_context_tool_calls(tool_calls: list[dict], chart: ChartState) -> list[dict]:
        results = []
        for call in tool_calls[:MAX_TOOL_CALLS]:
            name = call["name"]
            try:
                result = execute_context_tool(name, call["arguments"], chart)
            except ValueError as exc:
                result = {"tool": name, "error": str(exc)}
            except Exception:
                result = {"tool": name, "error": "The requested chart context could not be retrieved."}
            results.append(result)
        return results

    def _execute_final_bridge_prompt(self, system_prompt: str, user_prompt: str) -> str:
        if len(system_prompt) + len(user_prompt) > 4000:
            return self._execute_bridge_chunked(system_prompt, user_prompt)
        return self._execute_bridge(system_prompt, user_prompt)

    def _execute_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """
        Executes inference using a local Ollama instance.
        """
        url = "http://localhost:11434/api/chat"
        model = os.getenv("OLLAMA_MODEL", "gemma:2b")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.4,
            }
        }
        try:
            # High timeout for local CPU inference
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "ERROR: No content from Ollama.")
        except Exception as e:
            return f"SYSTEM_ERROR: Local Ollama Execution Failed. Details: {str(e)}"

    def _chunk_prompt(self, text: str, max_chars: int = 12600) -> list:
        """
        Splits a large prompt into smaller chunks while preserving logical boundaries.
        Tries to split at paragraph breaks or newlines first.
        Max chunk size set to 12600 characters per user request.
        """
        if len(text) <= max_chars:
            return [text]

        chunks = []
        # Try to split by double newlines (paragraphs) first
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para) + 2  # +2 for the newlines we'll add back
            if current_len + para_len <= max_chars:
                current_chunk.append(para)
                current_len += para_len
            else:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                # If a single paragraph is too long, split by lines
                if para_len > max_chars:
                    lines = para.split('\n')
                    temp_chunk = []
                    temp_len = 0
                    for line in lines:
                        if temp_len + len(line) + 1 <= max_chars:
                            temp_chunk.append(line)
                            temp_len += len(line) + 1
                        else:
                            if temp_chunk:
                                chunks.append('\n'.join(temp_chunk))
                            temp_chunk = [line]
                            temp_len = len(line) + 1
                    if temp_chunk:
                        chunks.append('\n'.join(temp_chunk))
                else:
                    current_chunk = [para]
                    current_len = para_len

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        # Ensure no chunk is empty
        return [c for c in chunks if c.strip()]

    def _extract_code_block(self, text: str) -> str:
        """
        Extracts content from a markdown code block.
        Looks for ```markdown ... ``` or ``` ... ``` and returns the raw content.
        """
        import re
        # Try to find markdown code block
        patterns = [
            r'```markdown\s*\n(.*?)\n```',
            r'```\s*\n(.*?)\n```',
            r'```markdown(.*?)```',
            r'```(.*?)```'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # If no code block found, return the original text
        # (but strip any wrapper text that might have been added)
        return text.strip()

    def _execute_bridge_chunked(self, system_prompt: str, user_prompt: str, model: str = "gemini-web") -> str:
        """
        Executes inference by sending the prompt in chunks to Gemini Web UI via the bridge.
        This avoids the per-message input limit of the free web UI.
        The bridge maintains session context across messages.
        """
        url = "http://localhost:8001/v1/chat/completions"

        # Combine system and user prompts
        full_prompt = f"=== SYSTEM INSTRUCTION (read first) ===\n{system_prompt}\n\n=== USER DATA (read second) ===\n{user_prompt}"

        # Split into chunks
        chunks = self._chunk_prompt(full_prompt, 12600)

        if len(chunks) <= 1:
            # If it's small enough, send normally
            return self._execute_bridge(system_prompt, user_prompt, model)

        print(f"[Chunked Mode] Splitting prompt into {len(chunks)} chunks...")

        # Send each chunk as a separate message
        for i, chunk in enumerate(chunks):
            is_last = (i == len(chunks) - 1)

            if is_last:
                message = chunk + "\n\n[This is the FINAL chunk. Now generate your complete response based on ALL the context provided above. Return your response in a markdown code block with ```markdown ... ``` tags.]"
            else:
                message = chunk + "\n\n[Please reply with 'ACK' to confirm receipt of this chunk. Do not generate any analysis yet.]"

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "temperature": 0.4,
                "stream": False
            }

            try:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                if is_last:
                    print(f"[Chunked Mode] Final response received ({len(content)} chars)")
                    return self._extract_code_block(content)
                else:
                    # Check for acknowledgment
                    if "ACK" not in content.upper() and "✅" not in content:
                        print(f"[Chunked Mode] Warning: Chunk {i+1} did not get ACK. Response: {content[:100]}")
                    else:
                        print(f"[Chunked Mode] Chunk {i+1}/{len(chunks)} acknowledged")

            except requests.exceptions.ConnectionError:
                return "SYSTEM_ERROR: Universal Web LLM Bridge not running. Please start the bridge server on port 8001."
            except Exception as e:
                return f"SYSTEM_ERROR: Bridge Chunked Execution Failed at chunk {i+1}. Details: {str(e)}"

        return "ERROR: Failed to get complete response from chunked bridge."

    def _execute_bridge(self, system_prompt: str, user_prompt: str, model: str = "gemini-web") -> str:
        """
        Executes inference using the local universal-web-llm-bridge server.
        The bridge runs on localhost:8001 and exposes an OpenAI-compatible /v1/chat/completions endpoint.
        """
        url = "http://localhost:8001/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "ERROR: No content from bridge.")
        except requests.exceptions.ConnectionError:
            return "SYSTEM_ERROR: Universal Web LLM Bridge not running. Please start the bridge server on port 8001."
        except Exception as e:
            return f"SYSTEM_ERROR: Bridge Execution Failed. Details: {str(e)}"

    def generate_response(self, user_query: str, chart: ChartState, features: dict, quantitative_scores: dict, neo4j_context: dict, history: list = None, gender: str = "Male", preferred_language: str = "English", global_memory: list = None, prediction_calibration=None) -> str:
        """
        Executes the final inference. Uses Bridge by default, falls back to Gemini API or Ollama.
        """
        # Determine which mode to use: Forced to 'bridge' as requested by the user
        llm_mode = "bridge"

        system_prompt = self.build_system_prompt(neo4j_context, preferred_language)

                # Construct Prompts
        if llm_mode == "ollama":
            # LITE MODE: Gemma 2b and similar small models have 8k context windows.
            raw_chart = chart.to_chart_payload()
            lite_vargas = {
                "D1_Main": raw_chart.get("divisional_charts", {}).get("D1_Main"),
                "D9_Navamsha": raw_chart.get("divisional_charts", {}).get("D9_Navamsha"),
                "D10_Dashamsha": raw_chart.get("divisional_charts", {}).get("D10_Dashamsha")
            }
            lite_chart = chart.model_copy(update={"divisional_charts": lite_vargas})
            user_prompt = self.synthesize_reading_prompt(user_query, lite_chart, features, quantitative_scores, neo4j_context, history, gender, preferred_language, global_memory, prediction_calibration)
            return self._execute_ollama(system_prompt, user_prompt)


        if llm_mode == "gemini_api":
            # Use direct Gemini API (legacy mode)
            user_prompt = self.synthesize_reading_prompt(user_query, chart, features, quantitative_scores, neo4j_context, history, gender, preferred_language, global_memory, prediction_calibration)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            gemini_api_key = None
            try:
                gemini_key_path = os.path.join(base_dir, "API Keys", "Gemini_flash_API_key.txt")
                if os.path.exists(gemini_key_path):
                    with open(gemini_key_path, 'r') as f:
                        lines = f.read().strip().split('\n')
                        if lines and len(lines[0]) > 10:
                            gemini_api_key = lines[0].strip().rstrip('.')
            except Exception:
                pass
            if not gemini_api_key:
                gemini_api_key = os.getenv("GEMINI_API_KEY")

            if gemini_api_key:
                try:
                    from google import genai
                    client = genai.Client(api_key=gemini_api_key)
                    response = client.models.generate_content(
                        model='gemini-flash-latest',
                        contents=user_prompt,
                        config=genai.types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=0.4,
                        )
                    )
                    return response.text
                except Exception as e:
                    return f"SYSTEM_ERROR: Gemini LLM Execution Failed. Details: {str(e)}"
            return f"[MOCK AGENT RESPONSE]\nSYSTEM INSTRUCTION LENGTH: {len(system_prompt)}\nUSER PROMPT CONSTRUCT LENGTH: {len(user_prompt)}\n\n(WARNING: No API keys found.)"

        # DEFAULT: Use Bridge (Universal Web LLM Bridge on port 8001)
        user_prompt = self.synthesize_reading_prompt(user_query, chart, features, quantitative_scores, neo4j_context, history, gender, preferred_language, global_memory, prediction_calibration)
        first_response = self._execute_final_bridge_prompt(system_prompt, user_prompt)
        tool_calls = self._parse_context_tool_calls(first_response)
        if not tool_calls:
            return first_response

        tool_results = self._run_context_tool_calls(tool_calls, chart)
        tool_result_block = (
            "\n\n### ON-DEMAND DASHA / TRANSIT TOOL RESULTS ###\n"
            + json.dumps(tool_results, ensure_ascii=False, indent=2, default=str)
            + "\n\nUse only the returned fields and their component status. Now answer the user's original question in the requested language. Do not request another tool call."
        )
        return self._execute_final_bridge_prompt(system_prompt, user_prompt + tool_result_block)

    def extract_memories(self, user_query: str, assistant_response: str, existing_memory: list = None) -> list:
        """
        Extracts important life context from the conversation to store as global profile memory.
        Returns a list of dicts with 'key' and 'value'.
        """
        if not existing_memory:
            existing_memory = []

        # Build a compact memory extraction prompt
        existing_summary = "\n".join([f"- {m['key']}: {m['value']}" for m in existing_memory]) if existing_memory else "(No existing memories)"

        extraction_prompt = f"""You are a memory extraction system. Extract important life context from the conversation below.

EXISTING MEMORIES (DO NOT DUPLICATE):
{existing_summary}

USER QUERY:
{user_query}

ASSISTANT RESPONSE:
{assistant_response}

Extract 0-3 key facts that are valuable for future conversations. Focus on:
- Career/education goals and status
- Relationship/family context
- Health/wellness situations
- Financial matters
- Important life events or challenges
- Personality traits or preferences relevant to life decisions

Return ONLY a JSON array of objects with 'key' and 'value' fields.
Example: [{{"key": "career_goal", "value": "Currently transitioning to data science from finance"}}]

If nothing new to extract, return [] (empty array).

Return ONLY the JSON array, no other text."""

        try:
            # Use the bridge for memory extraction with a smaller model or the same one
            url = "http://localhost:8001/v1/chat/completions"
            payload = {
                "model": "gemini-web",
                "messages": [{"role": "user", "content": extraction_prompt}],
                "temperature": 0.3,
                "stream": False
            }

            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "[]")

            # Try to parse the JSON
            import re
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                return json.loads(json_match.group(0))
            return []
        except Exception as e:
            print(f"[Memory Extraction] Error: {e}")
            return []
