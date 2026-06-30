# AI Study Assistant

> A multi-agent AI system that turns any document into a complete study kit — summaries, flashcards, quizzes, and exam questions — through a single conversational interface.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3%2070B-F55036?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Track: Concierge Agents

## 1. The Problem

Studying from raw material — a 40-slide lecture deck, a dense PDF chapter, a page of typed notes — is inefficient on its own. Before a student can actually *study*, they first have to manually:

- Re-read and distill the material into a summary
- Pull out key terms and write flashcards by hand
- Invent their own practice questions to self-test
- Guess what an exam might actually ask

This prep work takes longer than the studying itself, and most students skip it — which means they go into exams under-prepared. The problem isn't a lack of study *techniques* (summarizing, flashcards, and practice testing are all proven, research-backed methods) — it's the manual labor required to produce that material in the first place.

## 2. The Solution

**AI Study Assistant** removes that bottleneck. A student uploads one document, and a coordinated team of AI agents instantly produces every study artifact a research-backed study routine requires — summary, flashcards, quiz, and exam questions — all grounded in that exact document, not generic web content.

The system is built around a **Concierge Agent** pattern: instead of one monolithic prompt trying to do everything, a central orchestrator interprets what the student is asking for in natural language and delegates to the specialist agent built for that job. This is the same reason real organizations route a request to a specialist instead of asking the front-desk person to do surgery — specialization produces better output than one generalist trying to do it all.

## 3. Why Agents — Not Just a Single Prompt

A single LLM call with one giant prompt ("summarize, quiz, and flashcard this") consistently produces worse, blander results than focused prompts, because the model has to balance four different goals at once and dilutes effort across all of them.

Splitting the work into agents solves this directly:

| Without agents | With agents (this project) |
|---|---|
| One prompt trying to do 4 jobs at once | 4 prompts, each tuned for one job |
| No clear routing — every request re-explains itself | Concierge interprets intent and calls the right tool |
| Hard to extend — adding a feature means rewriting the master prompt | Adding a study feature = adding one new agent + one tool definition |
| Output quality is "good enough at everything" | Each agent's system prompt is purpose-built for its output format |

Agents are not used here as a buzzword — they are the mechanism that lets each output type (summary vs. quiz vs. flashcard vs. exam) get a prompt and parsing strategy optimized specifically for it, while still feeling like one assistant to the student.

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Streamlit UI  (app.py)                   │
│   Sidebar: Upload + Quick Generate   │  Tabs: Chat ·       │
│                                       │  Summary · Quiz ·   │
│                                       │  Flashcards · Exam  │
└───────────────────────┬────────────────────────────────────┘
                         │  user message + document text
                         ▼
              ┌─────────────────────────┐
              │     Concierge Agent     │   agents/concierge_agent.py
              │  (LLaMA 3.3 70B, tool   │   - interprets user intent
              │   calling, agentic loop)│   - decides which agent(s) to call
              └────┬─────┬─────┬────┬───┘   - loops until a final answer
                   │     │     │    │
        ┌──────────┘  ┌──┘   ┌─┘   └────────┐
        ▼             ▼      ▼              ▼
 ┌────────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐
 │  Document  │ │   Quiz   │ │ Flashcard │ │    Exam    │
 │   Agent    │ │  Agent   │ │   Agent   │ │   Agent    │
 │ summarize()│ │ MCQ JSON │ │ Term/Def  │ │ Essay/SA/  │
 │            │ │          │ │   JSON    │ │ Problem    │
 └────────────┘ └──────────┘ └───────────┘ └────────────┘
        │             │            │              │
        └─────────────┴──── Groq API (LLaMA 3.3) ─┘
```

**Flow:**
1. The student uploads a document → `utils/file_parser.py` extracts plain text (PDF / PPTX / DOCX / TXT)
2. The student types a request in chat, or clicks a Quick Generate button
3. The **Concierge Agent** receives the request with the document attached as context, and — using OpenAI-style tool calling against the Groq API — decides which specialist agent(s) to invoke
4. Each specialist agent runs its own focused Groq API call with a task-specific system prompt and returns structured output (plain text or JSON)
5. Results are written back into Streamlit's session state and rendered in the matching tab

### Why a manual agentic loop instead of one big call
The Concierge runs an explicit `while True` loop (see `agents/concierge_agent.py`): it sends the conversation to the model, checks if the model requested a tool call, executes that tool, feeds the result back, and repeats until the model returns a final text answer with no further tool calls. This is what allows a single user message like *"summarize this and then quiz me on it"* to trigger two agents in sequence within one turn.

---

## 5. Key Concepts Demonstrated

| Key Concept | Where | Notes |
|---|---|---|
| **Agent / Multi-agent system** | `agents/concierge_agent.py`, `agents/document_agent.py`, `agents/quiz_agent.py`, `agents/flashcard_agent.py`, `agents/exam_agent.py` | One orchestrator agent + four specialist agents, coordinated via tool-calling and a manual agentic loop |
| **Security features** | `.env` + `.gitignore`, `.env.example`, `utils/file_parser.py` | API key never hardcoded — loaded from environment via `python-dotenv`; `.env` is git-ignored so secrets can't leak into version control; every agent call is wrapped in try/except so a malformed document or API failure fails safely instead of crashing the app; uploaded documents are capped at 50,000 characters to prevent unbounded input |
| **Deployability** | See [Deployment](#7-deployment) below | App is structured for one-command local run (`streamlit run app.py`) and is directly deployable to Streamlit Community Cloud with no code changes — only the `GROQ_API_KEY` secret needs to be set in the host environment |

---

## 6. Features

| Feature | Description |
|---|---|
| **Smart Summarization** | Structured, exam-ready summary with headings and key concepts |
| **Interactive Flashcards** | Flip-card UI with term/definition pairs and progress tracking |
| **Scored Quizzes** | Multiple-choice questions with instant grading and explanations |
| **Exam Questions** | Essay, short-answer, and problem-solving questions with model answers |
| **Conversational Chat** | Natural-language interface — the Concierge routes the request automatically |

---

## 7. Setup & Installation

### Prerequisites
- Python 3.9+
- A free [Groq](https://console.groq.com) account (no credit card required)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/AI-Study-Assistant.git
cd AI-Study-Assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# then open .env and paste your real Groq key
```

Get your key at **[console.groq.com](https://console.groq.com) → API Keys → Create API key** (starts with `gsk_`).

```bash
# 4. Run the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

### Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub (your `.env` is git-ignored automatically — it will not be uploaded)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub repo
3. Set `app.py` as the entry point
4. In **App settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Deploy — no code changes required, since `os.environ.get("GROQ_API_KEY")` reads from whichever environment it's running in

---

## 8. Usage

### Quick Generate (sidebar)
Upload a document, then click:
- **📝 Summary** — instant structured summary
- **🃏 Flashcards** — 10 flashcards from key concepts
- **📋 Quiz** — 5 medium-difficulty multiple-choice questions
- **🎓 Exam** — 5 mixed exam-style questions

### Chat (natural language)
```
"Summarize the main points of this document"
"Give me a hard quiz with 10 questions"
"Create 15 flashcards focusing on definitions"
"Generate 3 essay questions for my exam"
```

---

## 9. Project Structure

```
AI-Study-Assistant/
├── app.py                    # Streamlit entry point — UI, session state, tabs
├── requirements.txt          # Python dependencies
├── .env.example               # Template for required environment variables
├── .gitignore                  # Excludes .env and other secrets from version control
├── agents/
│   ├── concierge_agent.py    # Orchestrator — tool calling + agentic loop
│   ├── document_agent.py     # Summarization specialist
│   ├── quiz_agent.py         # Multiple-choice quiz specialist
│   ├── flashcard_agent.py    # Flashcard specialist
│   └── exam_agent.py         # Exam question specialist
└── utils/
    └── file_parser.py        # PDF / PPTX / DOCX / TXT → plain text
```

---

## 10. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io) |
| AI Model | LLaMA 3.3 70B via [Groq](https://groq.com) |
| Agent orchestration | OpenAI-compatible tool calling (manual agentic loop) |
| PDF parsing | [pypdf](https://pypdf.readthedocs.io) |
| PPTX parsing | [python-pptx](https://python-pptx.readthedocs.io) |
| DOCX parsing | [python-docx](https://python-docx.readthedocs.io) |
| Config / secrets | [python-dotenv](https://github.com/theskumar/python-dotenv) |

---

## 11. Project Journey

The project started as a single-prompt summarizer, but that produced shallow, unfocused output when asked to also generate quizzes and flashcards. Splitting the work into a Concierge + specialist agents — each with its own narrow system prompt — was the turning point: output quality improved immediately because each agent only has to be good at one thing. The biggest engineering challenge was the agentic tool-use loop in the Concierge — making sure tool results are correctly fed back into the conversation so the model can chain multiple agents (e.g., "summarize and then quiz me") within a single user turn.

---

## License

MIT License.

---

> Built with [Streamlit](https://streamlit.io) and [Groq](https://groq.com)
