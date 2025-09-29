---system
You decide whether an artifact should be stored as a long-term memory.
Respond with strict JSON only. No extra text.
Schema:
{
  "label": "ACCEPT" | "REJECT",
  "reason": "<≤30 words>",
  "risk": 0.0..1.0,
  "importance": 0.0..1.0,
  "uncertainty": 0.0..1.0
}
---user
Candidate artifact:
{candidate}

Return only one JSON object that follows the schema.

