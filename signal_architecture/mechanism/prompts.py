"""V7 Phase 12 — mechanism extraction + abstraction prompts.

The system prompt forbids the LLM from including entity names, dates,
addresses, case numbers, or jurisdictions. A best-effort Python scrubber
catches anything that slips through (4-digit years, title-cased multi-
word proper nouns).
"""

EXTRACTION_SYSTEM = """\
You are extracting an ABSTRACT risk mechanism from a verified insurance signal.

Goal: produce a pattern that might apply to OTHER entities on future cycles.

CRITICAL RULES (the platform scrubs violations, but obey them upfront):
- DO NOT name the entity, its officers, addresses, jurisdictions, or any case numbers.
- DO NOT include specific dates or 4-digit years.
- DO use generic role nouns: "director", "subsidiary", "regulator".
- DO use generic source types: "structured register", "court index", "regulator filing".

Return ONLY this JSON (no prose, no markdown fences):
{
  "summary": "one sentence, abstract, entity-anonymous",
  "tags": ["snake_case", "tags"],
  "keywords": ["words", "useful", "for", "recall"],
  "what_made_it_high_grade": "brief — why this earned structured_attested or higher"
}

Example input: cluster of OFAC SDN listing + UK FCA enforcement + press
confirmation (sanctions_screening_result, structured_attested, validator
advanced).
Example output:
{
  "summary": "Entity carries an SDN listing corroborated by a separate regulator enforcement action and contemporaneous press coverage",
  "tags": ["sdn", "regulator_corroboration", "press_corroboration"],
  "keywords": ["sdn", "sanctions", "regulator", "enforcement", "press"],
  "what_made_it_high_grade": "Two independent authoritative registers plus an independent reputational signal agreed on the same listing window"
}
"""


def build_extraction_user(payload_json: str) -> str:
    """Wrap a scrubbed payload JSON in the user-side directive."""
    return (
        "Extract an abstract mechanism from this verified signal "
        "(do NOT reproduce entity-specific details):\n\n"
        f"{payload_json}\n"
    )
