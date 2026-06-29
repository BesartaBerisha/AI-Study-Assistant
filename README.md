# AI Study Assistant

An AI-powered study tool that turns your documents into summaries, flashcards, quizzes, and exam questions using a multi-agent architecture.

## What it does

Upload a PDF, PowerPoint, Word, or text file and the app will:

- **Summarize** — generate a structured, exam-ready summary
- **Flashcards** — create key term / definition cards you can flip through
- **Quiz** — generate scored multiple-choice questions
- **Exam Questions** — produce essay, short-answer, and problem-solving questions
- **Chat** — ask anything about your document; the AI routes your request to the right agent automatically

## Architecture

```
app.py  (Streamlit UI)
│
└── agents/
    ├── concierge_agent.py   ← Orchestrator — routes requests via tool use
    ├── document_agent.py    ← Summarization
    ├── quiz_agent.py        ← Multiple-choice quiz generation
    ├── flashcard_agent.py   ← Flashcard creation
    └── exam_agent.py        ← Exam question generation

utils/
    └── file_parser.py       ← Parses PDF, PPTX, DOCX, TXT files
```

All agents use **Llama 3.3 70B** via [Groq](https://console.groq.com) (free, fast).

## Supported file types

| Format | Extension |
|--------|-----------|
| PDF | `.pdf` |
| PowerPoint | `.pptx`, `.ppt` |
| Word | `.docx`, `.doc` |
| Text / Markdown | `.txt`, `.md` |

## Setup

### 1. Clone or download the project

```bash
git clone <repo-url>
cd AI-Study-Assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (no credit card required)
3. Click **API Keys** → **Create API key**
4. Copy the key (starts with `gsk_...`)

### 4. Add your API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=gsk_your_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Usage

1. Upload a study document using the sidebar
2. Use the **Quick Generate** buttons in the sidebar for instant results, or
3. Type in the **Chat** tab — the assistant will automatically generate what you ask for
4. Switch between tabs to view Summary, Flashcards, Quiz, and Exam Questions

## Requirements

- Python 3.9+
- Internet connection (for Groq API calls)
- Free Groq account

## Tech stack

| Component | Technology |
|-----------|-----------|
| UI | Streamlit |
| AI Model | Llama 3.3 70B (via Groq) |
| PDF parsing | pypdf |
| PowerPoint parsing | python-pptx |
| Word parsing | python-docx |
| Environment config | python-dotenv |
