"""Domain-aware retrieval from the astrology knowledge graph.

Intent routing is driven by explicit, allowlisted user tags in the chat API.
Keyword routing remains a fallback for direct/internal callers. User text is
never interpolated into Cypher.
"""
import json
import os
import re

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(override=False)

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


# Keywords are routing hints, not astrological rules. Bengali and English are
# included because the UI may receive either language.
DOMAIN_KEYWORDS = {
    "career": ("career", "job", "profession", "promotion", "work", "business", "\u099a\u09be\u0995\u09b0\u09bf", "\u0995\u09cd\u09af\u09be\u09b0\u09bf\u09af\u09bc\u09be\u09b0", "\u09aa\u09c7\u09b6\u09be", "\u09ac\u09cd\u09af\u09ac\u09b8\u09be", "\u09aa\u09cd\u09b0\u09ae\u09cb\u09b6\u09a8"),
    "education": ("education", "study", "studies", "exam", "school", "college", "university", "phd", "\u09aa\u09a1\u09bc\u09be\u09b6\u09cb\u09a8\u09be", "\u09aa\u09dc\u09be\u09b6\u09cb\u09a8\u09be", "\u09b6\u09bf\u0995\u09cd\u09b7\u09be", "\u09aa\u09b0\u09c0\u0995\u09cd\u09b7\u09be", "\u09ad\u09b0\u09cd\u09a4\u09bf"),
    "wealth": ("wealth", "money", "finance", "income", "salary", "savings", "\u09b8\u09ae\u09cd\u09aa\u09a6", "\u099f\u09be\u0995\u09be", "\u0985\u09b0\u09cd\u09a5", "\u0986\u09df", "\u09ac\u09c7\u09a4\u09a8", "\u09b8\u099e\u09cd\u099a\u09df"),
    "marriage": ("marriage", "married", "spouse", "husband", "wife", "relationship", "love", "\u09ac\u09bf\u09df\u09c7", "\u09ac\u09bf\u09ac\u09be\u09b9", "\u09a6\u09be\u09ae\u09cd\u09aa\u09a4\u09cd\u09af", "\u09b8\u09ae\u09cd\u09aa\u09b0\u09cd\u0995", "\u09aa\u09cd\u09b0\u09c7\u09ae", "\u099c\u09c0\u09ac\u09a8\u09b8\u0999\u09cd\u0997\u09c0"),
    "children": ("children", "child", "pregnancy", "progeny", "\u09b8\u09a8\u09cd\u09a4\u09be\u09a8", "\u0997\u09b0\u09cd\u09ad", "\u0997\u09b0\u09cd\u09ad\u09a7\u09be\u09b0\u09a3"),
    "foreign_travel": ("foreign", "abroad", "immigration", "settlement", "travel", "\u09ac\u09bf\u09a6\u09c7\u09b6", "\u09aa\u09cd\u09b0\u09ac\u09be\u09b8", "\u09ad\u09cd\u09b0\u09ae\u09a3", "\u09ac\u09bf\u09a6\u09c7\u09b6\u09af\u09be\u09a4\u09cd\u09b0\u09be"),
    "property": ("property", "real estate", "land", "house", "home", "\u09b8\u09ae\u09cd\u09aa\u09a4\u09cd\u09a4\u09bf", "\u099c\u09ae\u09bf", "\u09ac\u09be\u09dc\u09bf", "\u0997\u09c3\u09b9"),
    "spiritual": ("spiritual", "spirituality", "meditation", "moksha", "\u0986\u09a7\u09cd\u09af\u09be\u09a4\u09cd\u09ae\u09bf\u0995", "\u09a7\u09cd\u09af\u09be\u09a8", "\u09ae\u09cb\u0995\u09cd\u09b7"),
}

DOMAIN_CHARTS = {
    "career": ["D1_Main", "D9_Navamsha", "D10_Dashamsha"],
    "education": ["D1_Main", "D9_Navamsha", "D24_Chaturvimshamsha"],
    "wealth": ["D1_Main", "D9_Navamsha", "D2_Hora", "D4_Chaturthamsha", "D10_Dashamsha"],
    "marriage": ["D1_Main", "D9_Navamsha"],
    "children": ["D1_Main", "D9_Navamsha", "D7_Saptamsha"],
    "foreign_travel": ["D1_Main", "D9_Navamsha", "D4_Chaturthamsha", "D10_Dashamsha"],
    "property": ["D1_Main", "D9_Navamsha", "D4_Chaturthamsha"],
    "spiritual": ["D1_Main", "D9_Navamsha", "D20_Vimshamsha"],
    "general": ["D1_Main", "D9_Navamsha"],
}

DOMAIN_HOUSES = {
    "career": {2, 6, 10, 11},
    "education": {2, 4, 5, 9, 11},
    "wealth": {2, 5, 9, 11},
    "marriage": {2, 7, 8, 11},
    "children": {2, 5, 9, 11},
    "foreign_travel": {4, 9, 12},
    "property": {4, 11},
    "spiritual": {5, 8, 9, 12},
    "general": set(range(1, 13)),
}
DOMAIN_TERMS = {
    "career": ["career", "profession", "job", "work", "business"],
    "education": ["education", "study", "learning", "exam"],
    "wealth": ["wealth", "money", "income", "finance"],
    "marriage": ["marriage", "relationship", "spouse", "love"],
    "children": ["children", "child", "progeny"],
    "foreign_travel": ["foreign", "travel", "journey", "settlement"],
    "property": ["property", "land", "home", "real estate"],
    "spiritual": ["spiritual", "meditation", "moksha"],
    "general": [],
}
DOMAIN_GRAPH_THEMES = {
    "career": ["career", "leadership", "service", "fame"],
    "education": ["intellect", "creativity"],
    "wealth": ["wealth", "luxury"],
    "marriage": ["marriage", "love"],
    "children": ["children"],
    "foreign_travel": ["foreign travel"],
    "property": ["wealth", "self", "mother"],
    "spiritual": ["spirituality", "self", "mind"],
    "general": [],
}
AVAILABLE_DOMAINS = tuple(DOMAIN_CHARTS)


def resolve_domains(question: str, selected_domains=None) -> tuple[list[str], float, str]:
    """Honor validated user tags; fall back to every matched keyword domain."""
    if selected_domains:
        chosen = list(dict.fromkeys(
            domain for domain in selected_domains
            if isinstance(domain, str) and domain in AVAILABLE_DOMAINS
        ))
        if "general" in chosen:
            chosen = ["general"]
        if chosen:
            return chosen, 1.0, "user_selected"

    text = (question or "").casefold()
    matched_domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        matched = False
        for keyword in keywords:
            keyword = keyword.casefold()
            if any(ord(char) > 127 for char in keyword):
                matched = keyword in text
            else:
                matched = re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", text) is not None
            if matched:
                break
        if matched:
            matched_domains.append(domain)
    if not matched_domains:
        return ["general"], 0.0, "automatic_fallback"
    return matched_domains, 0.5, "automatic_fallback"


def resolve_domain(question: str) -> tuple[str, float]:
    """Return a conservative keyword-routed domain and normalized confidence."""
    domains, confidence, _ = resolve_domains(question)
    if len(domains) != 1:
        return "general", 0.0
    return domains[0], confidence
    text = (question or "").casefold()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            keyword = keyword.casefold()
            if any(ord(char) > 127 for char in keyword):
                matched = keyword in text
            else:
                matched = re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", text) is not None
            score += int(matched)
        if score:
            scores[domain] = score
    if not scores:
        return "general", 0.0
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "general", 0.0
    return ranked[0][0], min(1.0, ranked[0][1] / 2.0)


class RAGCompiler:
    """Builds a domain-specific, parameterized graph retrieval payload."""

    def __init__(self):
        self.json_backup_path = os.getenv("NEO4J_JSON_BACKUP_PATH")
        self._json_data = None

    def _load_json_backup(self) -> dict:
        if self._json_data is not None:
            return self._json_data
        if not self.json_backup_path:
            self._json_data = {"nodes": {}, "relationships": []}
            return self._json_data
        try:
            nodes, relationships = {}, []
            with open(self.json_backup_path, "r", encoding="utf-8-sig") as stream:
                source = stream.read()
            # Current export is a JSON array containing a `data` JSONL string;
            # retain JSONL support for older backups too.
            try:
                parsed = json.loads(source)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                lines = [line for row in parsed if isinstance(row, dict)
                         for line in str(row.get("data", "")).splitlines()]
            elif isinstance(parsed, dict) and isinstance(parsed.get("data"), str):
                lines = parsed["data"].splitlines()
            else:
                lines = source.splitlines()
            for line in lines:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") == "node":
                    nodes[obj["id"]] = obj
                elif obj.get("type") == "relationship":
                    relationships.append(obj)
            self._json_data = {"nodes": nodes, "relationships": relationships}
        except Exception as exc:
            print(f"JSON_BACKUP_LOAD_ERROR: {exc}")
            self._json_data = {"nodes": {}, "relationships": []}
        return self._json_data

    @staticmethod
    def _select_planet_houses(features: dict, domain: str) -> list[dict]:
        houses = DOMAIN_HOUSES.get(domain, DOMAIN_HOUSES["general"])
        selected = []
        for planet, data in features.get("positional", {}).items():
            try:
                house = int(data["house"])
            except (KeyError, TypeError, ValueError):
                continue
            if domain == "general" or house in houses:
                selected.append({"planet": planet, "house": house})
        return selected

    @staticmethod
    def _select_domains_planet_houses(features: dict, domains: list[str]) -> list[dict]:
        houses = set()
        for domain in domains:
            houses.update(DOMAIN_HOUSES.get(domain, DOMAIN_HOUSES["general"]))
        domain_house_lords = set()
        house_lords = features.get("relational", {}).get("house_lords", {})
        for house_number in houses:
            lord_data = house_lords.get(house_number, house_lords.get(str(house_number), {}))
            if isinstance(lord_data, dict) and lord_data.get("lord"):
                domain_house_lords.add(lord_data["lord"])
        selected = []
        for planet, data in features.get("positional", {}).items():
            try:
                house = int(data["house"])
            except (KeyError, TypeError, ValueError):
                continue
            if "general" in domains or house in houses or planet in domain_house_lords:
                selected.append({"planet": planet, "house": house})
        return selected

    @staticmethod
    def _dasha_names(features: dict) -> list[str]:
        temporal = features.get("temporal", {})
        md = temporal.get("active_mahadasha", "Unknown")
        ad = temporal.get("active_antardasha", "Unknown")
        names = []
        if md != "Unknown":
            names.append(f"{md} Mahadasha")
        if md != "Unknown" and ad != "Unknown":
            names.append(f"{md}-{ad}")
        return names

    def _json_fallback(self, compiled: dict, planet_house_params: list[dict], dasha_names: list[str]) -> None:
        """Project the exported graph's structural facts into the RAG payload.

        This export does not contain the online GIVES_IN_HOUSE/GIVES_RESULT
        effect paragraphs. It does contain House->LifeTheme REPRESENTS,
        Planet->LifeTheme SIGNIFIES, and Mahadasha->LifeTheme ACTIVATES edges.
        Keep these clearly labeled as structural associations.
        """
        data = self._load_json_backup()
        nodes = data.get("nodes", {})
        house_themes = {}
        planet_themes = {}
        dasha_themes = {}

        def endpoint_properties(endpoint):
            if isinstance(endpoint, dict):
                return endpoint.get("properties", {})
            node = nodes.get(str(endpoint), {})
            return node.get("properties", {})

        for rel in data.get("relationships", []):
            rel_type = rel.get("label")
            start_props = endpoint_properties(rel.get("start"))
            end_props = endpoint_properties(rel.get("end"))
            theme = end_props.get("name")
            if not theme:
                continue
            if rel_type == "REPRESENTS":
                try:
                    house_themes.setdefault(int(start_props.get("number")), []).append(theme)
                except (TypeError, ValueError):
                    pass
            elif rel_type == "SIGNIFIES":
                planet_themes.setdefault(str(start_props.get("name", "")).casefold(), []).append(theme)
            elif rel_type == "ACTIVATES":
                dasha_themes.setdefault(str(start_props.get("name", "")).casefold(), []).append(theme)

        selected_domains = compiled.get("domains", ["general"])
        relevant_houses = set()
        domain_terms = set()
        for domain in selected_domains:
            relevant_houses.update(DOMAIN_HOUSES.get(domain, DOMAIN_HOUSES["general"]))
            domain_terms.update(DOMAIN_TERMS.get(domain, []))
            domain_terms.update(DOMAIN_GRAPH_THEMES.get(domain, []))
        represented_domain_themes = {
            theme.casefold()
            for house, themes in house_themes.items()
            if "general" in selected_domains or house in relevant_houses
            for theme in themes
        }
        for item in planet_house_params:
            planet = item["planet"]
            house = item["house"]
            themes = house_themes.get(house, [])
            significations = planet_themes.get(planet.casefold(), [])
            if "general" not in selected_domains:
                # Include house themes for the domain houses, and planet themes
                # only when their names match the requested topic.
                if house not in relevant_houses:
                    themes = []
                significations = [theme for theme in significations
                                  if theme.casefold() in represented_domain_themes
                                  or any(term in theme.casefold() for term in domain_terms)]
            compiled["house_effects"][planet] = {
                "house": house,
                "related_life_themes": themes,
                "planet_significations": significations,
                "source_type": "structural_graph_associations",
                "note": "Backup has no personalized planet-house effect paragraph.",
            }

        for dasha_name in dasha_names:
            for theme in dasha_themes.get(dasha_name.casefold(), []):
                if ("general" not in selected_domains
                        and theme.casefold() not in represented_domain_themes
                        and not any(term in theme.casefold() for term in domain_terms)):
                    continue
                compiled["dasha_effects"].append({
                    "period": dasha_name,
                    "theme": theme,
                    "effect": "Structural ACTIVATES association from JSON graph backup.",
                    "source_type": "structural_graph_associations",
                })

    def fetch_all_context(self, features: dict, user_query: str = "", selected_domains=None) -> dict:
        domains, confidence, route_source = resolve_domains(user_query, selected_domains)
        domain = domains[0] if len(domains) == 1 else "multi_domain"
        planet_house_params = self._select_domains_planet_houses(features, domains)
        dasha_names = self._dasha_names(features)
        charts = list(dict.fromkeys(
            chart for item in domains for chart in DOMAIN_CHARTS[item]
        ))
        domain_terms = list(dict.fromkeys(
            term for item in domains
            for term in DOMAIN_TERMS[item] + DOMAIN_GRAPH_THEMES[item]
        ))

        compiled = {
            "domain": domain,
            "domains": domains,
            "domain_confidence": confidence,
            "domain_route_source": route_source,
            "selected_charts": charts,
            "house_effects": {},
            "dasha_effects": [],
            "system_prompts": [],
            "rag_online": False,
            "retrieval_status": {"neo4j": "not_attempted", "json_backup": "not_attempted"},
        }

        query_houses = """
        UNWIND $ph_params AS ph
        MATCH (p:Planet {name: ph.planet})-[r:GIVES_IN_HOUSE]->(h:House)
        WHERE h.number = ph.house OR toInteger(h.number) = ph.house
        RETURN p.name AS planet, h.number AS house, r.effect AS effect
        """
        query_dasha = """
        UNWIND $dasha_names AS d_name
        MATCH (d {name: d_name})-[r:GIVES_RESULT]->(lt:LifeTheme)
        WHERE $domains CONTAINS 'general'
           OR any(term IN $domain_terms WHERE toLower(coalesce(lt.name, '')) CONTAINS term)
        RETURN d.name AS period, lt.name AS theme, r.effect AS effect
        """
        query_templates = """
        MATCH (t:InterpretationTemplate)
        WHERE t.id CONTAINS 'MASTER_ASTROLOGER'
           OR t.id CONTAINS 'TPL_1'
           OR t.id CONTAINS 'TPL_001_HOUSE_CONFLICT'
        RETURN t.id AS id, t.template_text AS prompt
        """

        try:
            if not (URI and USERNAME and PASSWORD):
                raise RuntimeError("Neo4j connection settings are incomplete")
            with GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD)) as driver:
                with driver.session() as session:
                    for record in session.run(query_houses, ph_params=planet_house_params):
                        compiled["house_effects"][record["planet"]] = {
                            "house": record["house"], "effect": record["effect"]
                        }
                    for record in session.run(query_dasha, dasha_names=dasha_names,
                                              domains=domains, domain_terms=domain_terms):
                        compiled["dasha_effects"].append({
                            "period": record["period"], "theme": record["theme"], "effect": record["effect"]
                        })
                    for record in session.run(query_templates):
                        compiled["system_prompts"].append({"id": record["id"], "prompt": record["prompt"]})
            compiled["retrieval_status"]["neo4j"] = "ok"
            compiled["rag_online"] = True
        except Exception as exc:
            print(f"RAG_BRIDGE_OFFLINE: {exc}")
            compiled["retrieval_status"]["neo4j"] = "offline"
            try:
                self._json_fallback(compiled, planet_house_params, dasha_names)
                compiled["retrieval_status"]["json_backup"] = "loaded"
            except Exception as json_exc:
                print(f"JSON_BACKUP_FALLBACK_FAILED: {json_exc}")
                compiled["retrieval_status"]["json_backup"] = "unavailable"

        return compiled
