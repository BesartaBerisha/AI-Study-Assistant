import json
import os
from typing import Optional, Tuple

from groq import Groq

from agents.document_agent import summarize
from agents.exam_agent import create_exam_questions
from agents.flashcard_agent import create_flashcards
from agents.quiz_agent import generate_quiz

_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """You are an AI Study Assistant — a helpful, friendly academic assistant.
You help students understand and study their uploaded documents.

You have tools to generate summaries, quizzes, flashcards, and exam questions from the
uploaded document. Use a tool whenever the student requests that type of content.

If no document has been uploaded, ask the student to upload one first.
Be encouraging and educational. After a tool runs, briefly mention what was generated
and tell the student to check the relevant tab."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "summarize_document",
            "description": (
                "Create a comprehensive summary of the uploaded study material. "
                "Use when the student asks for a summary, overview, or key points."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": (
                "Generate multiple-choice quiz questions to test knowledge. "
                "Use when the student wants to quiz themselves or practice questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "num_questions": {"type": "integer", "description": "Number of questions (default 5)"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"], "description": "Difficulty level"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_flashcards",
            "description": (
                "Create study flashcards with key terms and definitions. "
                "Use when the student wants flashcards or to memorize terms."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "num_cards": {"type": "integer", "description": "Number of flashcards (default 10)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_exam_questions",
            "description": (
                "Create challenging exam questions (essay, short answer, problem-solving). "
                "Use when the student wants to prepare for an exam."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "num_questions": {"type": "integer", "description": "Number of questions (default 5)"},
                },
                "required": [],
            },
        },
    },
]


def chat(
    user_message: str,
    document_text: Optional[str],
    messages_history: list,
) -> Tuple[str, dict]:
    if document_text:
        preview = document_text[:1500]
        full_message = (
            f"{user_message}\n\n"
            f"[Document loaded: {len(document_text):,} characters]\n"
            f"Document preview:\n{preview}..."
        )
    else:
        full_message = user_message

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": full_message})

    tool_results: dict = {}

    while True:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=4000,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or "", tool_results

        # Add assistant message with tool calls to history
        messages.append(msg)

        # Execute every tool call and append results
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            output, data = _run_tool(tool_call.function.name, args, document_text)
            tool_results.update(data)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output,
            })


def _run_tool(name: str, args: dict, document_text: Optional[str]) -> Tuple[str, dict]:
    if not document_text:
        return "Error: no document uploaded yet.", {}

    try:
        if name == "summarize_document":
            result = summarize(document_text)
            return f"Summary generated ({len(result):,} characters).", {"summary": result}

        if name == "generate_quiz":
            num = int(args.get("num_questions", 5))
            diff = args.get("difficulty", "medium")
            result = generate_quiz(document_text, num_questions=num, difficulty=diff)
            return f"Generated {len(result)} quiz questions.", {"quiz": result}

        if name == "create_flashcards":
            num = int(args.get("num_cards", 10))
            result = create_flashcards(document_text, num_cards=num)
            return f"Created {len(result)} flashcards.", {"flashcards": result}

        if name == "create_exam_questions":
            num = int(args.get("num_questions", 5))
            result = create_exam_questions(document_text, num_questions=num)
            return f"Created {len(result)} exam questions.", {"exam_questions": result}

        return f"Unknown tool: {name}", {}

    except Exception as exc:
        return f"Error in {name}: {exc}", {}
