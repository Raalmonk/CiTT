from __future__ import annotations

import json

from app.services.gemini_parser import GeminiAPICircuitProblem


schema = GeminiAPICircuitProblem.model_json_schema()
serialized = json.dumps(schema)

print(json.dumps(schema, indent=2))
print("additionalProperties" in serialized)
