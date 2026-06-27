import os

from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """You are an expert academic summarizer. When given study material, create a
comprehensive, well-structured summary that:
- Identifies and explains key concepts
- Highlights important facts, definitions, and relationships
- Organizes information with clear headings
- Is suitable for exam preparation

Format your summary with markdown headings and bullet points."""


def summarize(text: str) -> str:
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=4000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Please create a comprehensive study summary of the following material:\n\n{text}"},
        ],
    )
    return response.choices[0].message.content
