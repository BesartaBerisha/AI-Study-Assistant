import json
import os
import re

from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """You are an expert exam question creator for academic assessments.
Create challenging questions that require deep understanding and critical thinking.

ALWAYS respond with ONLY a valid JSON array — no markdown fences, no extra text.
Each object must have exactly these keys:
- "type": one of "essay", "short_answer", or "problem"
- "question": the full question text
- "hints": array of 1–2 hint strings to guide thinking
- "model_answer": a comprehensive model answer"""


def create_exam_questions(text: str, num_questions: int = 5) -> list:
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=6000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Create {num_questions} challenging exam questions from this material. "
                    f"Mix the question types (essay, short_answer, problem). "
                    f"Return ONLY a JSON array:\n\n{text}"
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
