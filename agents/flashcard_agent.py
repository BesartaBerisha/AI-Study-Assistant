import json
import os
import re

from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """You are an expert flashcard creator for studying.
Create concise, effective flashcards that help students memorize key concepts.

ALWAYS respond with ONLY a valid JSON array — no markdown fences, no extra text.
Each object must have exactly these keys:
- "front": the term or concept (keep it short)
- "back": the definition or explanation (clear and concise)"""


def create_flashcards(text: str, num_cards: int = 10) -> list:
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=4000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Create {num_cards} study flashcards from this material. "
                    f"Focus on the most important concepts. Return ONLY a JSON array:\n\n{text}"
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
