import json
import os
import re

from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """You are an expert quiz creator for educational content.
Generate high-quality multiple-choice questions that test understanding, not just memorization.

ALWAYS respond with ONLY a valid JSON array — no markdown fences, no extra text.
Each object in the array must have exactly these keys:
- "question": the question text
- "options": array of exactly 4 strings (do NOT include A/B/C/D prefixes)
- "correct": integer index (0–3) of the correct option
- "explanation": brief explanation of the correct answer"""


def generate_quiz(text: str, num_questions: int = 5, difficulty: str = "medium") -> list:
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=4000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Generate {num_questions} {difficulty}-difficulty multiple-choice questions "
                    f"from this study material. Return ONLY a JSON array:\n\n{text}"
                ),
            },
        ],
    )
    return _parse_json(response.choices[0].message.content)


def _parse_json(raw: str) -> list:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw.strip())
