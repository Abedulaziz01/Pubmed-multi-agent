import json
from pydantic import BaseModel
from typing import Optional
from core.llm_client import call_llm

class PICOResult(BaseModel):
    population: str
    intervention: str
    comparison: Optional[str] = None
    outcome: str
    original_query: str

SYSTEM_PROMPT = """You are a medical research assistant specializing in PICO framework extraction.

PICO stands for:
- Population: Who is being studied? (age group, condition, demographics)
- Intervention: What treatment, exposure, or action is being tested?
- Comparison: What is it being compared to? (if any)
- Outcome: What result or effect is being measured?

Your job is to read a user question and extract these four components.

Rules:
- Return ONLY valid JSON. No explanation, no markdown, no code fences.
- Use exactly these keys: population, intervention, comparison, outcome
- If comparison is not mentioned, return null for that field
- If a field is unclear, make a reasonable medical inference
- Never return anything outside the JSON object

Example input: Does exercise help depressed teenagers?
Example output: {"population": "teenagers with depression", "intervention": "exercise", "comparison": null, "outcome": "improvement in depression symptoms"}
"""

def _parse_llm_response(response: str, original_query: str) -> PICOResult:
    cleaned = response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])
    data = json.loads(cleaned)
    data["original_query"] = original_query
    return PICOResult(**data)

def extract_pico(user_query: str) -> PICOResult:
    print(f"\n[Agent 1] Input query: {user_query}")

    response = call_llm(SYSTEM_PROMPT, user_query)
    print(f"[Agent 1] Raw LLM response: {response}")

    try:
        return _parse_llm_response(response, user_query)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"[Agent 1] First parse failed: {e}. Retrying with explicit prompt...")

        retry_prompt = f"""The user asked: "{user_query}"

You must return ONLY a JSON object with exactly these keys: population, intervention, comparison, outcome.
No markdown. No explanation. No code blocks. Just the raw JSON object.
If comparison is not present, set it to null.

Return the JSON now:"""

        retry_response = call_llm(SYSTEM_PROMPT, retry_prompt)
        print(f"[Agent 1] Retry LLM response: {retry_response}")

        return _parse_llm_response(retry_response, user_query)