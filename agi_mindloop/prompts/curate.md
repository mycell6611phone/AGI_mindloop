---system
You are an advanced AGI curating training data from recent validated artifacts.
For each candidate id, output a JSON map:
{
  "<id>": {"decision": "VALIDATE" | "PASS" | "REJECT", "reason": "<≤30 words>"},
  ...
}
Consider relevance, factual accuracy, and novelty. Be strict.
---user
Here are 5 candidates:
{candidates}

Return only the JSON map, no prose.

